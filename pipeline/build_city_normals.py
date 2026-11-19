"""Build data/cities.json from ERA5 monthly reanalysis.

Reads monthly 2 m temperature (t2m) and total precipitation (tp) from ERA5
"monthly averaged reanalysis" NetCDF files, averages each calendar month over
a 30-year baseline, samples the nearest grid cell to every city in
pipeline/cities.csv, and writes the result in the format the games load.

Usage:
    python pipeline/build_city_normals.py /Volumes/CLIMATEDATA/era5/*.nc
    python pipeline/build_city_normals.py data_dir/*.nc --start 1991 --end 2020

Notes:
- ERA5 t2m is in kelvin; converted to degC.
- ERA5 monthly-mean tp is in metres per day; converted to mm per month
  using the mean number of days in each calendar month.
- Coastal cities can land on a grid cell that is mostly ocean. Spot-check
  the output against a few known climographs before publishing.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parent.parent
CITIES_CSV = ROOT / "pipeline" / "cities.csv"
OUT_JSON = ROOT / "data" / "cities.json"
DAYS_IN_MONTH = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def open_era5(paths):
    ds = xr.open_mfdataset(paths, combine="by_coords")
    # Newer CDS downloads name the time axis "valid_time".
    if "valid_time" in ds.dims and "time" not in ds.dims:
        ds = ds.rename({"valid_time": "time"})
    for name in ("t2m", "tp"):
        if name not in ds:
            raise SystemExit(f"Variable '{name}' not found. Variables present: {list(ds.data_vars)}")
    return ds


def monthly_climatology(ds, start, end):
    ds = ds.sel(time=slice(f"{start}-01-01", f"{end}-12-31"))
    years = np.unique(ds["time"].dt.year.values)
    if len(years) < (end - start + 1):
        print(f"Warning: only {len(years)} years available in {start}-{end}.")
    return ds[["t2m", "tp"]].groupby("time.month").mean("time").load()


def nearest(clim, lat, lon):
    lons = clim["longitude"].values
    if lons.max() > 180 and lon < 0:  # grid stored as 0..360
        lon = lon + 360
    return clim.sel(latitude=lat, longitude=lon, method="nearest")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="ERA5 monthly NetCDF files containing t2m and tp")
    ap.add_argument("--start", type=int, default=1991)
    ap.add_argument("--end", type=int, default=2020)
    args = ap.parse_args()

    clim = monthly_climatology(open_era5(args.files), args.start, args.end)

    with open(CITIES_CSV, newline="", encoding="utf-8") as f:
        cities = list(csv.DictReader(f))

    out = []
    for c in cities:
        lat, lon = float(c["lat"]), float(c["lon"])
        cell = nearest(clim, lat, lon)
        t = (cell["t2m"].values - 273.15).round(1)
        p = (cell["tp"].values * 1000 * DAYS_IN_MONTH).round(0)
        out.append({
            "name": c["name"], "country": c["country"], "lat": lat, "lon": lon,
            "continent": c["continent"], "t": t.tolist(), "p": p.tolist(),
        })

    OUT_JSON.write_text(json.dumps({
        "source": f"ERA5 monthly reanalysis, {args.start}-{args.end} mean, nearest grid cell",
        "units": {"t": "degC monthly mean", "p": "mm monthly total"},
        "cities": out,
    }, ensure_ascii=False, indent=0))
    print(f"Wrote {len(out)} cities to {OUT_JSON}")


if __name__ == "__main__":
    main()
