import requests
import os

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

    BORDER_R, BORDER_G, BORDER_B = 222, 184, 135   # light brown
    BORDER_WIDTH = 2

    for a in alerts:
        props = a["properties"]
        geom = a["geometry"]
        headline = props.get("headline", "Special Weather Statement")
        expires = props.get("expires", "")
        description = props.get("description", "").replace("\n", " ")

        coords = geom["coordinates"][0]
        if len(coords) > 1 and coords[-1] == coords[0]:
            coords = coords[:-1]

        hover_text = f"{headline}\\n\\nExpires: {expires}\\n\\n{description}"

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

        lines.append(f"; Expires: {expires}")
        lines.append(f"; {description}")
        lines.append("")

    return "\n".join(lines)


def main():
    alerts = fetch_sps_alerts()
    placefile = format_placefile(alerts)

    # Write the file (GitHub Actions will commit it if it changed)
    with open(OUTFILE, "w", newline="\n") as f:
        f.write(placefile)

    print(f"Generated {OUTFILE} with {len(alerts)} SPS alerts.")


if __name__ == "__main__":
    main()
