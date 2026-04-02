#!/usr/bin/env python3
import requests
from datetime import datetime, timezone

URL = "https://api.weather.gov/alerts/active?event=Flood%20Warning"
OUTFILE = "GRLevelX_FLW.txt"

def fetch_flw_alerts():
    r = requests.get(
        URL,
        headers={"User-Agent": "FLW-Placefile-Generator"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    alerts = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry")

        if props.get("event") != "Flood Warning":
            continue
        if not geom:
            continue

        alerts.append(feat)

    return alerts


def format_placefile(alerts):
    lines = []

    lines.append("Refresh: 120")
    lines.append("Title: Flood Warnings")
    lines.append("Font: 0, 11, 1, \"Arial\"")
    lines.append("Font: 1, 11, 1, \"Arial\"")
    lines.append("")

    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"; Generated: {utc_now}")

    BORDER_R, BORDER_G, BORDER_B = 0, 100, 0

    for a in alerts:
        props = a["properties"]
        geom = a["geometry"]

        headline = props.get("headline", "Flood Warning")
        expires_raw = props.get("expires", "")
        description = props.get("description", "").replace("\n", " ")

        # --- Handle Polygon and MultiPolygon ---
        coords_list = []

        if geom["type"] == "Polygon":
            coords_list = [geom["coordinates"][0]]

        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                coords_list.append(poly[0])

        else:
            continue

        # --- Process each polygon ---
        for coords in coords_list:

            if not coords or len(coords) < 2:
                continue

            if coords[-1] == coords[0]:
                coords = coords[:-1]

            nice_expires = expires_raw
            if expires_raw:
                try:
                    dt = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                    utc_dt = dt.astimezone(timezone.utc)
                    nice_expires = utc_dt.strftime("%Y-%m-%d %H:%M Z")
                except:
                    pass

            hover_text = (
                f"{headline}\n"
                f"Expires: {nice_expires}\n"
                f"{description}\n"
                f"Generated: {utc_now}"
            )

            lines.append(f"Color: {BORDER_R} {BORDER_G} {BORDER_B}")
            lines.append(f"Line: 2,,\"{hover_text}\"")

            for lon, lat in coords:
                lines.append(f"  {lat:.4f}, {lon:.4f}")

            first_lon, first_lat = coords[0]
            lines.append(f"  {first_lat:.4f}, {first_lon:.4f}")
            lines.append("End:")
            lines.append("")

    return "\n".join(lines)


def main():
    alerts = fetch_flw_alerts()
    placefile = format_placefile(alerts)

    with open(OUTFILE, "w", newline="\n") as f:
        f.write(placefile)

    print(f"Generated {OUTFILE} with {len(alerts)} Flood Warnings.")


if __name__ == "__main__":
    main()
