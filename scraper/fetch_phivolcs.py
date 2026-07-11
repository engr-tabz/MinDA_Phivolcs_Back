import json
import os
from datetime import datetime, timezone

import requests
import urllib3
from bs4 import BeautifulSoup

URL = "https://earthquake.phivolcs.dost.gov.ph/"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_feature(date_part, time_part, lat, lon, depth, mag, location):
    return {
        "type": "Feature",
        "properties": {
            "date": date_part,
            "time": time_part,
            "latitude": lat,
            "longitude": lon,
            "depth_km": depth,
            "magnitude": mag,
            "location": location,
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat],
        },
    }


def parse_table():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        URL,
        headers=headers,
        timeout=30,
        verify=False,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")

    if not tables:
        raise RuntimeError("No tables found.")

    features = []

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]

            if len(cols) < 6:
                continue

            try:
                date_time = cols[0].split()

                date_part = date_time[0]
                time_part = " ".join(date_time[1:])

                lat = float(cols[1])
                lon = float(cols[2])
                depth = float(cols[3])
                mag = float(cols[4])
                location = cols[5]

                features.append(
                    build_feature(
                        date_part,
                        time_part,
                        lat,
                        lon,
                        depth,
                        mag,
                        location,
                    )
                )

            except (ValueError, IndexError):
                continue

    print(f"Parsed features: {len(features)}")

    return {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "features": features,
    }


def save_geojson(data):
    os.makedirs("data", exist_ok=True)

    path = "data/earthquakes.geojson"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(data['features'])} records to {path}")


if __name__ == "__main__":
    geojson = parse_table()
    save_geojson(geojson)
