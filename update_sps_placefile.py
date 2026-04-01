import requests
from datetime import datetime, timezone

URL = "https://api.weather.gov/alerts/active"
OUTFILE = "GRLevelX_SPS.txt"   # GitHub Actions writes to repo root

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

    # Refresh must be first
    lines.append("Refresh: 5")
    lines.append("Title: Special Weather Statements")
    lines.append("Font: 0, 11, 1, \"Arial\"")
    lines.append("Font: 1, 11, 1, \"Arial\"")
    lines.append("")

    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"; Generated: {utc_now}")

    # Tan border color
    BORDER_R, BORDER_G, BORDER_B = 222, 184, 135

    for a in alerts:
        props = a["properties"]
        geom = a["geometry"]
        headline = props.get("headline", "Special Weather Statement")
        expires_raw = props.get("expires", "")
        description = props.get("description", "").replace("\n", " ")

        coords = geom["coordinates"][0]

        # GeoJSON is [lon, lat]; convert to (lat, lon)
        if len(coords) > 1 and coords[-1] == coords[0]:
            coords = coords[:-1]

        # Format expiration time
        nice_expires = expires_raw
        if expires_raw:
            try:
                dt = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                utc_dt = dt.astimezone(timezone.utc)
                nice_expires = utc_dt.strftime("%Y-%m-%d %H:%M Z")
            except:
                pass

        hover_text = (
            f"{headline}\\n"
            f"Expires: {nice_expires}\\n"
            f"{description}\\n"
            f"Generated: {utc_now}"
        )

        # --- Visible tan border as Line with hover text ---
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
    alerts = fetch_sps_alerts()
    placefile = format_placefile(alerts)

    with open(OUTFILE, "w", newline="\n") as f:
        f.write(placefile)

    print(f"Generated {OUTFILE} with {len(alerts)} SPS alerts.")

if __name__ == "__main__":
    main()
