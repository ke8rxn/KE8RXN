import requests
import os
from datetime import datetime

URL = "https://api.weather.gov/alerts/active"
OUTFILE = "GRLevelX_SPS.txt"


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
    lines.append("Title: Special Weather Statements")
    lines.append("Refresh: 300")
    lines.append("Font: 0, 11, 1, \"Arial\"")
    lines.append("Font: 1, 11, 1, \"Arial\"")
    lines.append("")

    # Live generation timestamp (UTC)
    utc_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"; Generated: {utc_now}")

    BORDER_R, BORDER_G, BORDER_B = 222, 184, 135   # light brown
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

        # === CORRECTED: Preserve the exact NWS office timezone ===
        nice_expires = expires_raw
        if expires_raw:
            try:
                dt = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                offset_hours = dt.utcoffset().total_seconds() / 3600 if dt.utcoffset() else 0

                # Accurate timezone abbreviations based on actual NWS offset
                if offset_hours == -4:
                    tz_abbr = "EDT"
                elif offset_hours == -5:
                    tz_abbr = "CDT"      # ← fixed for Central Daylight Time offices
                elif offset_hours == -6:
                    tz_abbr = "CST"
                else:
                    tz_abbr = dt.strftime("%z")   # fallback to raw offset

                nice_expires = dt.strftime(f"%B %d, %Y at %I:%M %p {tz_abbr}")
            except:
                pass  # fallback to raw string if parsing fails

        hover_text = f"{headline}\\n\\nExpires: {nice_expires}\\n\\n{description}\\n\\nGenerated: {utc_now}"

        lines.append(f"Color: {BORDER_R} {BORDER_G} {BORDER_B}")
        lines.append(f"Line: {BORDER_WIDTH}, 0, \"{hover_text}\"")
        for i in range(len(coords)):
            lat = coords[i][1]
            lon = coords[i][0]
            lines.append(f"{lat:.4f}, {lon:.4f}")
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
