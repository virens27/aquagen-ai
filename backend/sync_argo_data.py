"""
Weekly ARGO data sync — run by GitHub Actions on a schedule.

Fetches new ARGO float profiles from ERDDAP (Ifremer) since the last successful
sync, and inserts them into the ocean_data table on Supabase. Every run is
logged to ingestion_log regardless of outcome.

Run manually with:
    cd backend
    python sync_argo_data.py
(requires DATABASE_URL to be set in the environment or in backend/.env)
"""
import io
import time
import warnings
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from sqlalchemy import func, insert, select

from app.db.session import SessionLocal
from app.models.ingestion_log import IngestionLog
from app.models.ocean_data import OceanData

warnings.filterwarnings("ignore")

SOURCE_NAME = "github_actions_weekly_sync"
BATCH_SIZE = 500
DEFAULT_LOOKBACK_DAYS = 7  # used only if no prior successful sync is found

# Bounding box matches the original hackathon dataset (Indian Ocean region).
# Adjust these if you want to widen coverage later.
LAT_MIN, LAT_MAX = -30, 30
LON_MIN, LON_MAX = 50, 100
PRES_MAX = 100  # depth limit in meters


def get_last_sync_time(db) -> datetime:
    """
    Returns the run_finished_at of the most recent successful sync.
    Falls back to DEFAULT_LOOKBACK_DAYS ago if this is the first run.
    """
    last_success = db.execute(
        select(func.max(IngestionLog.run_finished_at)).where(
            IngestionLog.source == SOURCE_NAME,
            IngestionLog.status == "success",
        )
    ).scalar()

    if last_success is not None:
        return last_success

    return datetime.now(timezone.utc) - timedelta(days=DEFAULT_LOOKBACK_DAYS)


def build_erddap_url(start_time: datetime, end_time: datetime) -> str:
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"
        "?platform_number,latitude,longitude,time,pres,temp,psal"
        f"&latitude>={LAT_MIN}&latitude<={LAT_MAX}"
        f"&longitude>={LON_MIN}&longitude<={LON_MAX}"
        f"&pres<={PRES_MAX}"
        f"&time>={start_str}&time<={end_str}"
        '&orderBy("time")'
    )


def fetch_argo_data(start_time: datetime, end_time: datetime) -> pd.DataFrame:
    url = build_erddap_url(start_time, end_time)
    print(f"Fetching ARGO data from {start_time} to {end_time}...")
    response = requests.get(url, verify=False, timeout=180)

    if response.status_code != 200:
        # ERDDAP returns 404 when a query matches zero rows — not a real error.
        if response.status_code == 404:
            print("No new records found in this window.")
            return pd.DataFrame()
        raise RuntimeError(
            f"ERDDAP request failed: {response.status_code} — {response.text[:300]}"
        )

    lines = response.text.split("\n")
    clean = "\n".join([lines[0]] + lines[2:])  # drop ERDDAP's units row
    df = pd.read_csv(io.StringIO(clean))
    df.columns = ["float_id", "lat", "lon", "date", "depth", "temperature", "salinity"]
    df = df.dropna(subset=["lat", "lon", "date"])
    return df


def main() -> None:
    start_time = time.monotonic()
    db = SessionLocal()

    log_entry = IngestionLog(source=SOURCE_NAME, status="running")
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    inserted = 0
    failed = 0

    try:
        sync_from = get_last_sync_time(db)
        sync_to = datetime.now(timezone.utc)

        df = fetch_argo_data(sync_from, sync_to)
        total_rows = len(df)
        log_entry.records_fetched = total_rows
        db.commit()

        if total_rows == 0:
            log_entry.status = "success"
            log_entry.records_inserted = 0
            log_entry.run_finished_at = datetime.now(timezone.utc)
            log_entry.duration_seconds = time.monotonic() - start_time
            db.commit()
            print("Sync complete. No new records to insert.")
            return

        records = df.to_dict(orient="records")
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            payload = []
            for row in batch:
                try:
                    payload.append(
                        {
                            "float_id": str(row["float_id"]),
                            "cycle_number": None,
                            "profile_date": pd.to_datetime(row["date"]).to_pydatetime(),
                            "latitude": float(row["lat"]),
                            "longitude": float(row["lon"]),
                            "pressure_dbar": float(row["depth"])
                            if pd.notna(row["depth"])
                            else None,
                            "temperature_c": float(row["temperature"])
                            if pd.notna(row["temperature"])
                            else None,
                            "salinity_psu": float(row["salinity"])
                            if pd.notna(row["salinity"])
                            else None,
                            "data_mode": "R",  # realtime, from weekly sync
                            "source_file": "erddap_weekly_sync",
                        }
                    )
                except Exception as row_err:
                    failed += 1
                    print(f"  Skipping bad row: {row_err}")

            if payload:
                db.execute(insert(OceanData), payload)
                db.commit()
                inserted += len(payload)

        log_entry.status = "success"
        log_entry.records_inserted = inserted
        log_entry.records_failed = failed
        log_entry.run_finished_at = datetime.now(timezone.utc)
        log_entry.duration_seconds = time.monotonic() - start_time
        db.commit()

        print(f"\nSync complete. Inserted {inserted} rows, {failed} failed.")

    except Exception as exc:
        db.rollback()
        log_entry.status = "failed"
        log_entry.error_message = str(exc)[:2000]
        log_entry.records_inserted = inserted
        log_entry.records_failed = failed
        log_entry.run_finished_at = datetime.now(timezone.utc)
        log_entry.duration_seconds = time.monotonic() - start_time
        db.commit()
        print(f"\nSync failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
