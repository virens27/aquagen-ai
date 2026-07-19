"""
One-time migration: SQLite (ocean_data.db) -> Supabase Postgres (ocean_data table).

Run from the backend/ folder:
    python migrate_sqlite_to_supabase.py

What it does:
1. Reads all rows from local ocean_data.db (columns: lat, lon, date, depth, temperature, salinity)
2. Maps them onto the new ocean_data schema (latitude, longitude, profile_date, pressure_dbar,
   temperature_c, salinity_psu)
3. Since the old data has no float_id, assigns a placeholder ('legacy-hackathon-import') so the
   not-null constraint is satisfied. source_file is tagged so these rows are identifiable later.
4. Inserts in batches via SQLAlchemy, logs the run in ingestion_log.
"""
import sqlite3
import time
from datetime import datetime, timezone

from sqlalchemy import insert

from app.db.session import SessionLocal
from app.models.ingestion_log import IngestionLog
from app.models.ocean_data import OceanData

SQLITE_PATH = "ocean_data.db"
BATCH_SIZE = 500
PLACEHOLDER_FLOAT_ID = "legacy-hackathon-import"


def parse_date(date_str: str) -> datetime:
    """Handles ISO strings like '2023-01-01T03:23:36Z'."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def main() -> None:
    start_time = time.monotonic()

    # --- Read from SQLite ---
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT lat, lon, date, depth, temperature, salinity FROM ocean_data")
    rows = cur.fetchall()
    conn.close()

    total_rows = len(rows)
    print(f"Read {total_rows} rows from {SQLITE_PATH}")

    if total_rows == 0:
        print("Nothing to migrate. Exiting.")
        return

    # --- Log ingestion start ---
    db = SessionLocal()
    log_entry = IngestionLog(
        source="sqlite_migration",
        status="running",
        records_fetched=total_rows,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    inserted = 0
    failed = 0

    try:
        # --- Insert in batches ---
        for i in range(0, total_rows, BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            payload = []
            for row in batch:
                try:
                    payload.append(
                        {
                            "float_id": PLACEHOLDER_FLOAT_ID,
                            "cycle_number": None,
                            "profile_date": parse_date(row["date"]),
                            "latitude": row["lat"],
                            "longitude": row["lon"],
                            "pressure_dbar": row["depth"],
                            "temperature_c": row["temperature"],
                            "salinity_psu": row["salinity"],
                            "data_mode": "legacy",
                            "source_file": SQLITE_PATH,
                        }
                    )
                except Exception as row_err:
                    failed += 1
                    print(f"  Skipping bad row {dict(row)}: {row_err}")

            if payload:
                db.execute(insert(OceanData), payload)
                db.commit()
                inserted += len(payload)
                print(f"  Inserted {inserted}/{total_rows}...")

        # --- Log success ---
        log_entry.status = "success"
        log_entry.records_inserted = inserted
        log_entry.records_failed = failed
        log_entry.run_finished_at = datetime.now(timezone.utc)
        log_entry.duration_seconds = time.monotonic() - start_time
        db.commit()

        print(f"\nDone. Inserted {inserted} rows, {failed} failed.")

    except Exception as exc:
        db.rollback()
        log_entry.status = "failed"
        log_entry.error_message = str(exc)
        log_entry.records_inserted = inserted
        log_entry.records_failed = failed
        log_entry.run_finished_at = datetime.now(timezone.utc)
        log_entry.duration_seconds = time.monotonic() - start_time
        db.commit()
        print(f"\nMigration failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
