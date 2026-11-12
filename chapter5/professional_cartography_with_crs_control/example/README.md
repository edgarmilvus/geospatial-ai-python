# Advanced application script — a professional choropleth on a Mercator GeoAxes

## What it does

Draws the cartographic object the chapter is aiming at: eleven districts over California, handed to
an EPSG:3857 `GeoAxes` in WGS 84 so Cartopy reprojects them, shaded with a five-stop ramp and given
a colour bar, laid over a basemap built from two polygons and projected by the same axes, with a
50 km scale bar and a north arrow. It also prints the number that keeps the map honest — Web
Mercator inflates this region's area by 1.63× at 38 °N — and the projected coordinate of a known
longitude and latitude.

## The listings

| file | what it is |
| --- | --- |
| `01_professional_choropleth.py` | the listing: `GeoAxes`, `add_geometries`, basemap, bar, arrow |
| `run_professional_choropleth.py` | the harness: projection, transform vs pyproj, extent, area inflation |

## Run it

```bash
cd chapter5/professional_cartography_with_crs_control/example/files
python3 01_professional_choropleth.py
```

It projects the districts onto an EPSG:3857 `GeoAxes`, draws the choropleth with its basemap, colour
bar, scale bar and north arrow, and saves a 300 dpi PNG, printing the CRS pair, the projected area,
the density range, the extent in degrees and in metres and one district's projected coordinate.
`run_professional_choropleth.py` asserts the 3857 projection, that Cartopy's transform matches
pyproj's to a micrometre, the 1/cos(38 °)² inflation, the 50 000 m bar and a large PNG; it exits
non-zero when any of them changes.

```text
Districts: 11
Source CRS: EPSG:4326 -> axes _EPSGProjection
Projected area: 117,194 sq km
Type: GeoAxes
Projection: _EPSGProjection (EPSG:3857)
District 5 at (-121.4, 38.4) -> (-13,514,186.2, 4,636,087.5) m
```

## What it produces

| path | what it is |
| --- | --- |
| `output/custom_geo_visualization_hires.png` | the map at 300 dpi |
| `output/professional_choropleth.json` | projection, areas, inflation, extents, projected point, bar |

## Notes

- Two substitutions: the bundled dataset became eleven seeded districts, and
  `cx.add_basemap(..., source=Stamen.TonerLite)` became a two-polygon basemap handed to the same
  `GeoAxes` — the reprojection contextily would have performed, without the network call.
- GeoPandas 1.0 no longer reprojects for a Cartopy axes, so the layers go through
  `ax.add_geometries(..., crs=ccrs.PlateCarree())`. That argument is what triggers the transform;
  `gdf.plot(ax=geoax)` alone would draw degrees on an axes whose units are metres.
- The colour bar is a `ScalarMappable`, because the axes is fed a list of colours rather than a
  DataFrame column.
- 117 194 km² of projection against 72 023 km² on the ellipsoid is a 1.627× inflation: the map is a
  picture, not a measurement.
