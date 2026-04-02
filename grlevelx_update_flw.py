#!/usr/bin/env python3
import requests
import datetime

# NWS API endpoint for active Flood Warnings (FLW)
URL = "https://api.weather.gov/alerts/active?event=Flood%20Warning"

# Output file name (GitHub Pages will serve this from your repo root)
OUTFILE = "GRLevelX_FLW.txt"

def fetch_alerts():
    """Fetch active Flood Warnings from the NWS API."""
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("features", [])

def format_placefile(alerts):
    """Convert NWS alerts into a GR2Analyst-compatible placefile."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append("Refresh: 120")
    lines.append("Title: Flood Warnings")
    lines.append(f"; Generated: {now}")
    lines.append("")

    for alert in alerts:
        props = alert.get("properties", {})
        geom = alert.get("geometry")

        if not geom or geom.get("type") != "Polygon":
            continue

        headline = props.get("headline", "Flood Warning")
        expires = props.get("expires", "N/A")
        desc = props.get("description", "").replace("\n", " ")

        lines.append(f"; {headline}")
        lines.append(f"; Expires: {expires}")
        lines.append(f"; {desc}")

        coords = geom["coordinates"][0]

        # Forest green polygon outline, 2px width
        lines.append("Polygon: 0 100 0 2")

        for lon, lat in coords:
            lines.append(f"{lat:.4f}, {lon:.4f}")

        lines.append("End:")
        lines.append("")

    return "\n".join(lines)

def main():
    alerts = fetch_alerts()
    text = format_placefile(alerts)

    with open(OUTFILE, "w") as f:
        f.write(text)

if __name__ == "__main__":
    main()
