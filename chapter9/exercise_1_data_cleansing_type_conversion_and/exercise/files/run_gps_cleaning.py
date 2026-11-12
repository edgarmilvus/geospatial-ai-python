"""Harness for exercise 1 — cleanse the logs, then draw the baseline density.

The exercise is a pipeline with three gates: parse, drop, bounds-check. The harness rebuilds
all three from the raw frame the listing kept, compares the surviving count, and then checks
the two things that would silently defeat the rest — coordinates still stored as objects,
and zeros that were never removed. The PNG is opened as an array to confirm something was
actually drawn.
"""
import contextlib
import io
import pathlib
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 1 (GPS cleansing and baseline KDE)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "gps_cleansing_baseline_kde.py", "gps_cleaning")
    printed = log.getvalue()

    raw, frame, gdf = module.raw_df, module.df, module.gdf

    # The CSV is a real file in the project, not a name that only works from one directory.
    csv_path = FILES.parent / "output" / "raw_gps_logs.csv"
    h.check(csv_path.is_file(), "the run wrote %s" % csv_path.name)
    reread = module.pd.read_csv(csv_path)
    h.equal(len(reread), 50000, "the raw file holds fifty thousand rows")
    h.equal(list(reread.columns), ["latitude", "longitude", "start_time"],
            "with the three columns the exercise names")

    # The pipeline, rebuilt from the raw frame rather than trusted.
    rebuilt = reread.copy()
    rebuilt["latitude"] = module.pd.to_numeric(rebuilt["latitude"], errors="coerce")
    rebuilt["longitude"] = module.pd.to_numeric(rebuilt["longitude"], errors="coerce")
    rebuilt = rebuilt.dropna(subset=["latitude", "longitude"])
    rebuilt = rebuilt[(rebuilt["latitude"] != 0.0) & (rebuilt["longitude"] != 0.0)]
    rebuilt = rebuilt[rebuilt["latitude"].between(-90, 90)
                      & rebuilt["longitude"].between(-180, 180)]
    h.equal(len(frame), len(rebuilt), "the cleaned frame is the pipeline's own output")
    h.equal(len(frame), 47_765, "47 765 of 50 000 rows survive the three gates")
    h.equal(len(raw) - len(frame), 2235, "so 2 235 rows (4.47 %) were removed")
    h.equal(module.COERCED, 1370,
            "1 370 rows carried a coordinate that would not parse as a number")

    # Type enforcement, which is what the exercise says to prove.
    h.equal(frame["latitude"].dtype, "float64", "latitude is float64, not object")
    h.equal(frame["longitude"].dtype, "float64", "longitude is float64, not object")
    h.equal(int(frame[["latitude", "longitude"]].isna().sum().sum()), 0,
            "no null coordinate survives")
    h.equal(int((frame["latitude"] == 0).sum() + (frame["longitude"] == 0).sum()), 0,
            "no zero coordinate survives")
    h.check(frame["latitude"].between(-90, 90).all(), "every latitude is in bounds")
    h.check(frame["longitude"].between(-180, 180).all(), "every longitude is in bounds")

    # The box the generator drew. The text values '40.9' and '-73.8' parse as numbers and
    # are inside these bounds, so they survive - the type conversion, not the filter, is
    # what catches them.
    h.check(abs(frame["latitude"].min() - 40.6) < 0.01
            and abs(frame["latitude"].max() - 40.9) < 0.01,
            "latitudes span the New York box the generator drew")
    h.check(abs(frame["longitude"].min() + 74.05) < 0.01
            and abs(frame["longitude"].max() + 73.8) < 0.01,
            "and so do longitudes")

    # The spatial conversion.
    h.equal(len(gdf), len(frame), "every cleaned row becomes one point")
    h.equal(gdf.crs.to_epsg(), 4326, "the GeoDataFrame declares WGS 84")
    h.equal(gdf.geometry.geom_type.unique().tolist(), ["Point"], "the geometry is points")
    h.check(abs(gdf.geometry.x.iloc[0] - frame["longitude"].iloc[0]) < 1e-12,
            "the point's x is the row's longitude, in that order")
    h.check(abs(gdf.geometry.y.iloc[0] - frame["latitude"].iloc[0]) < 1e-12,
            "and its y is the latitude")

    # The bandwidth: a multiplier derived from the target, not a constant that happens to
    # equal one.
    h.equal(module.H_BANDWIDTH, 0.005, "the target bandwidth is 0.005 degrees")
    h.check(abs(module.BW_ADJUST * module.REFERENCE_BANDWIDTH - 0.005) < 1e-12,
            "bw_adjust x the reference bandwidth is the 0.005 degrees claimed")
    h.check(0.3 < module.BW_ADJUST < 0.8,
            "which is a fraction of seaborn's default, %.3f" % module.BW_ADJUST)

    # The figure, opened as pixels: a blank canvas and a density surface differ in the
    # number of distinct colours, and that is checkable without a human.
    figure_path = FILES.parent / "output" / "gps_density_baseline.png"
    h.check(figure_path.is_file(), "the run wrote %s" % figure_path.name)
    import matplotlib.image as mpimg
    image = mpimg.imread(figure_path)
    h.check(image.shape[0] > 500 and image.shape[1] > 500,
            "the PNG is a full-page figure (%d x %d)" % image.shape[:2])
    flat = image[:, :, :3].reshape(-1, 3)[::97]
    counts = {}
    for row in flat:
        key = tuple(row)
        counts[key] = counts.get(key, 0) + 1
    distinct = len(counts)
    commonest = max(counts.values()) / len(flat)
    h.check(distinct > 40, "and it carries a gradient, not a flat fill (%d colours)"
            % distinct)
    h.check(commonest < 0.9, "no single colour covers the page (%.0f %% is the most)"
            % (commonest * 100))

    h.contains(printed, "Cleaned records: 47765", "the listing reports the cleaned count")
    h.contains(printed, "Removed: 2235 rows (4.47 %)", "and what it removed")
    h.contains(printed, "CRS: EPSG:4326", "and the CRS it assigned")
    h.contains(printed, "bw_adjust = 0.507", "and the bandwidth factor it derived")
    h.contains(printed, "output/gps_density_baseline.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("gps_cleaning.json", {
        "raw_rows": len(raw),
        "coerced": module.COERCED,
        "cleaned_rows": len(frame),
        "removed": len(raw) - len(frame),
        "removed_percent": round((len(raw) - len(frame)) / len(raw) * 100, 2),
        "lat_range": [round(float(frame["latitude"].min()), 4),
                      round(float(frame["latitude"].max()), 4)],
        "lon_range": [round(float(frame["longitude"].min()), 4),
                      round(float(frame["longitude"].max()), 4)],
        "crs": gdf.crs.to_string(),
        "bandwidth_degrees": module.H_BANDWIDTH,
        "reference_bandwidth": round(module.REFERENCE_BANDWIDTH, 4),
        "bw_adjust": round(module.BW_ADJUST, 3),
        "png_bytes": figure_path.stat().st_size,
        "png_size": list(image.shape[:2]),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
