# Example 2 — a highway expansion impact assessment

## What it does

Creates a proposed four-kilometre route north of Minneapolis, two protected wetlands
and five parcels in WGS 84 lon/lat, then does what the chapter insists on: reprojects
to UTM zone 15N before it buffers 50 metres, joins the parcels inside the corridor,
and intersects the route with the wetlands to measure how many metres of road cross
protected ground. The listing prints the route length in degrees beside the metric
length, so the reason for the reprojection is visible rather than asserted.

## The listings

| file | what it is |
| --- | --- |
| `01_highway_impact.py` | the listing: buffer in metres, sjoin for parcels, overlay for wetlands |
| `run_highway_impact.py` | the harness: the reprojection, the three residential ids, 565.55 m of conflict |

## Run it

```bash
cd chapter3/infrastructure_impact_zone_analysis/example/files
python3 01_highway_impact.py
```

It reprojects, buffers, joins and intersects, then prints the residential count, the
conflict length and the affected ids; `run_highway_impact.py` asserts that the route
moves from EPSG:4326 to EPSG:32615, that parcels 1, 4 and 5 are inside the corridor
and that the route crosses both wetlands, and exits non-zero if any of that changes.

## What it produces

| path | what it is |
| --- | --- |
| `output/highway_impact.json` | route length in metres, affected parcels, wetlands crossed, conflict length |

```text
[0/3] Route length: 0.0140 degrees -> 1272.65 m after reprojection
[1/3] Calculating 50-meter buffer (using CRS: EPSG:32615)...
   -> Total affected residential parcels identified: 3
   -> Total length of highway intersecting wetlands: 565.55 meters.

   Affected Parcel IDs: [1, 4, 5]
   Wetlands affected: ['Wetland A', 'Wetland B']
```

## Notes

- A 50-metre buffer in EPSG:4326 is a 50-*degree* buffer; it would cover the state.
  Every distance in the listing is computed after `to_crs('EPSG:32615')`.
- `sjoin` with `predicate='within'` keeps the parcels inside the corridor, and the
  commercial parcel that also falls inside is filtered out afterwards — the count is
  residential, the join is geometric.
- A line intersecting a polygon returns line segments, so `geometry.length` is metres
  of affected road, not an area.
