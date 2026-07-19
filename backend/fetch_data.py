import requests
import pandas as pd
import sqlite3
import io
import warnings
warnings.filterwarnings("ignore")

print("Fetching ARGO float data...")

url = (
    "https://erddap.ifremer.fr/erddap/tabledap/ArgoFloats.csv"
    "?latitude,longitude,time,pres,temp,psal"
    "&latitude>=-30&latitude<=30"
    "&longitude>=50&longitude<=100"
    "&pres<=100"
    "&time>=2023-01-01T00:00:00Z&time<=2023-06-30T00:00:00Z"
    "&orderBy(\"time\")"
)

print("Connecting to ERDDAP...")
response = requests.get(url, verify=False, timeout=120)

print(f"Status code: {response.status_code}")

if response.status_code != 200:
    print("Error response:")
    print(response.text[:500])
else:
    lines = response.text.split("\n")
    clean = "\n".join([lines[0]] + lines[2:])

    df = pd.read_csv(io.StringIO(clean))
    df.columns = ["lat", "lon", "date", "depth", "temperature", "salinity"]
    df = df.dropna()

    print(f"Fetched {len(df)} records")
    print(df.head())

    conn = sqlite3.connect("ocean_data.db")
    df.to_sql("ocean_data", conn, if_exists="replace", index=False)
    conn.close()

    print("Data saved to ocean_data.db successfully")