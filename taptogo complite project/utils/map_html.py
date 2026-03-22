"""
utils/map_html.py — Leaflet map HTML for WebView fallback.
Use when flet_webview is installed.
"""
# ===== MAP FIX START =====


def get_map_html(lat: float = 19.2183, lng: float = 72.9781, zoom: int = 13, height: str = "300px") -> str:
    """Return HTML string with Leaflet map. For use with WebView."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body style="margin:0;padding:0;">
<div id="map" style="height:{height};width:100%;"></div>
<script>
var map = L.map('map').setView([{lat}, {lng}], {zoom});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '© OpenStreetMap'
}}).addTo(map);
L.marker([{lat}, {lng}]).addTo(map).bindPopup('Current Location').openPopup();
</script>
</body>
</html>
"""


# ===== MAP FIX END =====
