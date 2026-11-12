"""Read a folium HTML map as data, so a harness can assert what it holds.

A folium map is not a picture: it is a document that declares a centre, a zoom and
a set of Leaflet layers as JavaScript literals. Those literals are stable enough to
search — `center: [lat, lon]`, `"zoom": 12`, a `base_layers` dict whose keys are the
names the reader sees in the control panel — so a harness can check the numbers the
listing computed instead of trusting that a file exists.

Nothing here opens a browser: the tile images are fetched by the reader's browser,
never by the build.
"""
from __future__ import annotations

import html.parser
import pathlib
import re


class _Document(html.parser.HTMLParser):
    """Collect the tag names of a document, which is enough to call it HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.error = None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def read(path):
    """Return the document text and the tag list, raising if it does not parse."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    document = _Document()
    document.feed(text)
    document.close()
    return text, document.tags


def is_html(text, tags):
    """True when the file looks like a complete, self-contained map document."""
    head = text.lstrip()[:15].lower()
    return bool(
        head.startswith("<!doctype html") and "html" in tags and "head" in tags
        and "body" in tags and "script" in tags and "folium-map" in text
    )


def centre(text):
    """The [lat, lon] the map is centred on, as a float pair."""
    match = re.search(r"center:\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]", text)
    return (float(match.group(1)), float(match.group(2))) if match else None


def zoom(text):
    """The zoom the map opens at."""
    match = re.search(r'"zoom":\s*(\d+)', text)
    return int(match.group(1)) if match else None


def _block(text, key):
    match = re.search(key + r"\s*:\s*\{(.*?)\n\s*\},", text, re.S)
    return match.group(1) if match else ""


def base_layers(text):
    """Ordered [(display name, tile-layer variable)] from the layer control."""
    return re.findall(r'"([^"]+)"\s*:\s*(tile_layer_[0-9a-f]+)', _block(text, "base_layers"))


def overlays(text):
    """Ordered [(display name, variable)] of the control's overlay section."""
    return re.findall(r'"([^"]+)"\s*:\s*([A-Za-z_0-9]+)', _block(text, "overlays"))


def added_to_map(text):
    """Variables the document attaches to the map on load."""
    return set(re.findall(r"([A-Za-z_0-9]+)\.addTo\(map_", text))


def tile_layers(text):
    """{variable: {"url": ..., "attribution": ..., "show": ...}} for every TileLayer."""
    layers = {}
    for match in re.finditer(
            r"var (tile_layer_[0-9a-f]+) = L\.tileLayer\(\s*\"([^\"]+)\",\s*\{(.*?)\n\s*\}\s*\)",
            text, re.S):
        name, url, options = match.groups()
        attribution = re.search(r'"attribution":\s*"((?:[^"\\]|\\.)*)"', options)
        layers[name] = {"url": url,
                        "attribution": attribution.group(1) if attribution else None}
    return layers


def layer_urls_by_name(text):
    """{display name: tile URL} joining the control's names to the TileLayer URLs."""
    variables = tile_layers(text)
    return {name: variables[var]["url"]
            for name, var in base_layers(text) if var in variables}


def tile_urls(text):
    """Every tile template in document order; the first is the default base layer."""
    return [layer["url"] for layer in tile_layers(text).values()]


def count(text, needle):
    """How many times a literal occurs, which is how markers are counted."""
    return text.count(needle)


def iframe_documents(text):
    """Decode the base64 `data:` documents folium writes for every IFrame popup."""
    import base64

    documents = []
    for match in re.finditer(
            r'src="data:text/html;charset=utf-8;base64,([^"]+)"', text):
        documents.append(base64.b64decode(match.group(1)).decode("utf-8"))
    return documents


def _literal(text, start):
    """The balanced {...} or [...] literal that begins at `start`, quotes respected."""
    opening = text[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return ""


def geojson_layers(text):
    """Every GeoJSON payload a folium document loads, as parsed dicts.

    A `folium.GeoJson` is written as `var geo_json_x = L.geoJson(null, {...})` followed by
    `geo_json_x_add({...})`, and the payload is the GeoJSON itself - a FeatureCollection
    whose features carry the properties the tooltip reads.
    """
    import json

    layers = []
    for match in re.finditer(r"(?:addData|_add)\(\s*(\{)", text):
        payload = _literal(text, match.start(1))
        if payload:
            try:
                layers.append(json.loads(payload))
            except ValueError:
                pass
    return layers


def heat_layers(text):
    """Every `L.heatLayer` dataset, as lists of [lat, lon] or [lat, lon, weight]."""
    import json

    layers = []
    for match in re.finditer(r"L\.heatLayer\(\s*(\[)", text):
        payload = _literal(text, match.start(1))
        if payload:
            try:
                layers.append(json.loads(payload))
            except ValueError:
                pass
    return layers


def heat_layer_options(text):
    """The options dict of every `L.heatLayer` in the document, in order."""
    import json

    options = []
    for match in re.finditer(r"L\.heatLayer\(\s*(\[)", text):
        data = _literal(text, match.start(1))
        brace = text.find("{", match.start(1) + len(data))
        if brace == -1:
            options.append({})
            continue
        payload = _literal(text, brace)
        # The template writes a trailing comma before the closing brace, which JSON rejects.
        payload = re.sub(r",(\s*[}\]])", r"\1", payload)
        try:
            options.append(json.loads(payload) if payload else {})
        except ValueError:
            options.append({})
    return options


def heat_options(text):
    """The options dict of the first `L.heatLayer` in the document, as parsed JSON."""
    return (heat_layer_options(text) or [{}])[0]
