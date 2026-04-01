import requests
import os
from datetime import datetime, timezone

URL = "https://api.weather.gov/alerts/active"
OUTFILE = "/var/www/sps/GRLevelX_SPS.txt"

def fetch_sps_alerts():
    r = requests.get(URL, headers={"User-Agent": "SPS-Placefile-Generator"})
    r.raise_for_status()
    data = r.json()
    alerts = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        if props.get("event") != "Special Weather Statement":
            continue
        geom = feat.get("geometry")
        if not geom or geom.get("type") != "Polygon":
            continue
        alerts.append(feat)
    return alerts

def format_placefile(alerts):
    lines = []

    # Refresh must be first for GR2Analyst
    lines.append("Refresh: 300")
    lines.append("Title: Special Weather Statements")
    lines.append("Font: 0, 11, 1, \"Arial\"")
    lines.append("Font: 1, 11, 1, \"Arial\"")
    lines.append("")

    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"; Generated: {utc_now}")

    BORDER_R, BORDER_G, BORDER_B = 222, 184, 135
    BORDER_WIDTH = 2

    for a in alerts:
        props = a["properties"]
        geom = a["geometry"]
        headline = props.get("headline", "Special Weather Statement")
        expires_raw = props.get("expires", "")
        description = props.get("description", "").replace("\n", " ")

        coords = geom["coordinates"][0]
        if len(coords) > 1 and coords[-1] == coords[0]:
            coords = coords[:-1]

        # Compute centroid for hidden point
        lats = [c[1] for c in coords]
        lons = [c[0] for c in coords]
        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)

        nice_expires = expires_raw
        if expires_raw:
            try:
                dt = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                utc_dt = dt.astimezone(timezone.utc)
                nice_expires = utc_dt.strftime("%Y-%m-%d %H:%M Z")
            except:
                pass

        hover_text = f"{headline}\\n\\nExpires: {nice_expires}\\n\\n{description}\\n\\nGenerated: {utc_now}"

        # Invisible dynamic object to trigger "Next Update"
        lines.append(f"Point: {centroid_lat:.4f}, {centroid_lon:.4f}, 0, \"\"")

        # Your original outline
        lines.append(f"Color: {BORDER_R} {BORDER_G} {BORDER_B}")
        lines.append(f"Line: {BORDER_WIDTH}, 0, \"{hover_text}\"")

        for lat, lon in coords:
            lines.append(f"{lat:.4f}, {lon:.4f}")

        # Close polygon
        lat0 = coords[0][1]
        lon0 = coords[0][0]
        lines.append(f"{lat0:.4f}, {lon0:.4f}")
        lines.append("End:")

        lines.append(f"; Expires: {expires_raw}")
        lines.append(f"; {description}")
        lines.append("")

    return "\n".join(lines)

def main():
    alerts = fetch_sps_alerts()
    placefile = format_placefile(alerts)

    with open(OUTFILE, "w", newline="\n") as f:
        f.write(placefile)

    print(f"Generated {OUTFILE} with {len(alerts)} SPS alerts.")

if __name__ == "__main__":
    main()
