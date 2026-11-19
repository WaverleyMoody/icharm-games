# iCHARM Games

Climate and geography mini-games for the iCHARM platform, built in SDSU's Climate Informatics Lab. Each game runs on real climate data, so playing it teaches something: how to read a climograph, what separates climate zones, and why latitude, oceans and elevation shape the weather.

## Games

| Game | Status | What it teaches |
|---|---|---|
| [Climograph Match](games/climograph-match/) | Prototype | Reading climographs; Köppen climate zones |
| Higher or Lower | Planned | Comparing cities' temperature, rainfall and seasonality |
| Biome Drop | Planned | Linking land cover from above to the climate that produces it |

## Run locally

The games load data with `fetch`, so open them through a local web server rather than double-clicking the file:

```bash
python -m http.server 8000
# then open http://localhost:8000/
```

## Repo layout

```
index.html                    Landing page listing the games
games/<game>/index.html       Each game is one self-contained page
data/cities.json              Shared city list + monthly climate normals
pipeline/cities.csv           The 200 cities (name, country, lat, lon, continent)
pipeline/build_city_normals.py  Rebuilds data/cities.json from ERA5
```

## Data

`data/cities.json` currently holds **placeholder values** (approximate monthly normals entered by hand). Replace them before any public release:

```bash
pip install -r pipeline/requirements.txt
python pipeline/build_city_normals.py /path/to/era5/*.nc --start 1991 --end 2020
```

The script expects ERA5 monthly averaged reanalysis files containing `t2m` and `tp`. To change which cities are in the game, edit `pipeline/cities.csv` and rerun the script.

## Deploying

Everything is static HTML, CSS and JSON, so the repo can be served with GitHub Pages (Settings → Pages → deploy from `main`) or linked or embedded from iCHARM.
