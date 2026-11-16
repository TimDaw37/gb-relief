# GB Relief

Shaded relief and bedrock geology maps of Great Britain and the surrounding sea floor, built from the open LiDAR terrain models and EMODnet bathymetry that also feed [LiDAR Lens](https://lidarlens.sarsen.org/). Three ways to use them:

- **Interactive map:** <https://timdaw37.github.io/gb-relief/>. Choose the style, lighting, vertical exaggeration and frame, then export a credited image at up to 7200 px wide.
- **Images:** ready-made maps of the whole of Great Britain in `images/`.
- **Base-map tiles:** Web Mercator XYZ tiles for Leaflet, MapLibre or OpenLayers, zoom 5 to 11, in `tiles/`.

## Images

| Version | 1000 px (700 m grid) | 3500 px (200 m grid) | 7000 px (100 m grid) |
|---|---|---|---|
| Relief and sea floor (tinted, shaded) | [JPG](images/gb-relief-1000px.jpg) | [JPG](images/gb-relief-3500px.jpg) · [PNG](images/gb-relief-3500px.png) | [JPG](images/gb-relief-7000px.jpg) · [PNG](images/gb-relief-7000px.png) |
| Grey hillshade | [JPG](images/gb-grey-1000px.jpg) | [JPG](images/gb-grey-3500px.jpg) · [PNG](images/gb-grey-3500px.png) | [JPG](images/gb-grey-7000px.jpg) · [PNG](images/gb-grey-7000px.png) |
| Elevation and depth tint | [JPG](images/gb-tint-1000px.jpg) | [JPG](images/gb-tint-3500px.jpg) · [PNG](images/gb-tint-3500px.png) | [JPG](images/gb-tint-7000px.jpg) · [PNG](images/gb-tint-7000px.png) |
| Bedrock geology on relief | [JPG](images/gb-geology-1000px.jpg) | [JPG](images/gb-geology-3500px.jpg) · [PNG](images/gb-geology-3500px.png) | [JPG](images/gb-geology-7000px.jpg) · [PNG](images/gb-geology-7000px.png) |

All images are on the British National Grid (EPSG:27700). Vertical exaggeration is 3.5×, 3× and 2.5× respectively. Each image carries its title, scale bar and the full data credits.

## Britain and Ireland

The same treatment for both islands together, on a Lambert azimuthal equal-area projection (ETRS89, centred 54° N, 4.5° W) that suits both. Ireland, the Isle of Man and the gaps in Scotland's LiDAR are GEM-15. The Irish LiDAR now in LiDAR Lens covers a few per cent of the island at 0.5–1 m and adds nothing visible at these scales. Credits run along a footer strip.

| Version | 1000 px (940 m grid) | 3500 px (270 m grid) | 7000 px (134 m grid) |
|---|---|---|---|
| Relief and sea floor | [JPG](images/britain-ireland-relief-1000px.jpg) | [JPG](images/britain-ireland-relief-3500px.jpg) · [PNG](images/britain-ireland-relief-3500px.png) | [JPG](images/britain-ireland-relief-7000px.jpg) · [PNG](images/britain-ireland-relief-7000px.png) |
| Grey hillshade | [JPG](images/britain-ireland-grey-1000px.jpg) | [JPG](images/britain-ireland-grey-3500px.jpg) · [PNG](images/britain-ireland-grey-3500px.png) | [JPG](images/britain-ireland-grey-7000px.jpg) · [PNG](images/britain-ireland-grey-7000px.png) |
| Elevation and depth tint | [JPG](images/britain-ireland-tint-1000px.jpg) | [JPG](images/britain-ireland-tint-3500px.jpg) · [PNG](images/britain-ireland-tint-3500px.png) | [JPG](images/britain-ireland-tint-7000px.jpg) · [PNG](images/britain-ireland-tint-7000px.png) |

No geology version yet: BGS 625k covers Great Britain only. GSI's 1:500,000 bedrock map for Ireland (CC BY 4.0) would complete it.

## Last British–Irish Ice Sheet: maximum extent

The envelope of the BRITICE-CHRONO empirical reconstruction (all 1 ka slices, 31–15 ka; Clark et al. 2022), on the relief and sea floor, with the land exposed at 26 ka from the BRITICE-CHRONO glacio-isostatic palaeotopography and the present coastline drawn through the ice. The margin is diachronous: different sectors reached it at different times. The ice shown includes the western margin of the Fennoscandian Ice Sheet. Lambert azimuthal equal-area, 55° N 3° W.

| Version | 1200 px | 2400 px | 6700 px |
|---|---|---|---|
| With title, legend and credits | [JPG](images/ice-sheet/bi-ice-sheet-max-extent-1200px.jpg) | [JPG](images/ice-sheet/bi-ice-sheet-max-extent-2400px.jpg) · [PNG](images/ice-sheet/bi-ice-sheet-max-extent-2400px.png) | [JPG](images/ice-sheet/bi-ice-sheet-max-extent-6700px.jpg) · [PNG](images/ice-sheet/bi-ice-sheet-max-extent-6700px.png) |
| Without text (for translation) | [JPG](images/ice-sheet/bi-ice-sheet-max-extent-notext-1200px.jpg) | | [JPG](images/ice-sheet/bi-ice-sheet-max-extent-notext-6700px.jpg) · [PNG](images/ice-sheet/bi-ice-sheet-max-extent-notext-6700px.png) |

Ice limits and palaeotopography: Clark, C.D., Ely, J.C., Fabel, D. & Bradley, S.L. 2022, BRITICE-CHRONO maps and GIS data of the last British-Irish Ice Sheet 31 to 15 ka, PANGAEA, doi:10.1594/PANGAEA.945729, CC BY 4.0; Clark et al. 2022, *Boreas* 51, 699–758, doi:10.1111/bor.12594. Scripts in `scripts/ice-sheet/`.

## Base-map tiles (Leaflet)

```html
<script src="https://timdaw37.github.io/gb-relief/gbrelief.js"></script>
<script>
  GBRelief.layer('relief').addTo(map);      // Great Britain: 'relief', 'grey' or 'geology'
  GBRelief.layer('relief-bi').addTo(map);   // Britain and Ireland: 'relief-bi' or 'grey-bi'
</script>
```

The tiles include the sea floor out to the edge of the British National Grid frame, fading over its outer 20 km. Ireland, France and everything beyond the frame are transparent, so put another base map underneath, or set the map container's background to `#d6e2e8` (`GBRelief.SEA`). Tiles go to zoom 11 (about 45 m per pixel), and Leaflet enlarges them above that. Any other client can use the template `https://timdaw37.github.io/gb-relief/tiles/{style}/{z}/{x}/{y}.webp`, with zoom 5–11 and the attribution in `gbrelief.js`. See [example.html](example.html).

## Data and method

- **Terrain.** 1 m open LiDAR DTMs:
  - Environment Agency LiDAR Composite DTM (England).
  - Welsh Government LiDAR DTM, via DataMapWales (Wales).
  - Scottish Government, SEPA, HES and OIC LiDAR, via the Scottish Remote Sensing Portal (Scotland).

  All are under the Open Government Licence v3.0. They were read from the LiDAR Lens overview tiles, which are LiDAR first, at about 90 m. In the gaps without open LiDAR (parts of the Highlands and Islands, and the Isle of Man), the terrain is GEM-15 v1. This is Google's experimental 15 m bare-earth model, CC BY 4.0 (Batchu et al. 2026).
- **Sea floor.** EMODnet Digital Bathymetry DTM 2024, mean-sea-level version, about 115 m cells, CC BY 4.0 ([doi:10.12770/cf51df64-56f9-4a99-b1aa-36b8d7b743a1](https://doi.org/10.12770/cf51df64-56f9-4a99-b1aa-36b8d7b743a1)), read from the LiDAR Lens seabed tiles (zoom 10). It is shaded like the land, with a blue depth tint. It compiles surveys of different ages and quality, so straight lines and steps can be survey artefacts. Depths are relative to mean sea level, not Ordnance Datum. Not for navigation.
- **Ireland.** For the Britain-and-Ireland maps: GEM-15 from the LiDAR Lens Irish tiles; coastline from the LiDAR Lens coast mask (OpenStreetMap land polygons, ODbL) outside Great Britain; the larger Irish loughs from Natural Earth; France flat from Natural Earth.
- **Coast and water.** Land is clipped to mean high water using OS Open Zoomstack. Inland water (National and Regional water bodies) and foreshore also come from Zoomstack. This removes the LiDAR flown over the sea and in estuaries.
- **Geology.** BGS Geology 625k (DiGMapGB-625) bedrock. Units are coloured by period with the ICS chart colours. Igneous intrusions are coloured by composition, felsic or mafic.
- **Shading.** Central-difference slopes and a four-direction sun: 315° at weight 0.5, 270° and 0° at 0.2 each, and 225° at 0.1, all at 40° elevation. The relief and geology versions lay this shading over the tint or the geology colours.
- **Rebuild.** The scripts are in `scripts/`. Run them in order: `fetch.py`, `prep.py`, `fetch_seabed.py`, `prep_sea.py`, `mask.py`, `geol.py`, `render3.py`, `build_sheets.py`, `cut_tiles.py`; Britain and Ireland: `fetch_bi.py`, `prep_bi.py`, `render_bi.py`, then `cut_tiles.py relief-bi` and `grey-bi`.

## Licence

The maps and tiles are © Tim Daw 2026, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit "GB Relief, Tim Daw (sarsen.org)" and keep the data credits:

> LiDAR DTMs: Environment Agency (England); Welsh Government, DataMapWales (Wales); Scottish Government, SEPA, HES, OIC, Scottish Remote Sensing Portal (Scotland). Open Government Licence v3.0. GEM-15 v1 (experimental), produced by Google, CC BY 4.0. Sea floor: EMODnet Digital Bathymetry (DTM 2024), CC BY 4.0, not for navigation. Contains OS data © Crown copyright and database right 2026. Geology versions: contains British Geological Survey materials © UKRI, Open Government Licence v3.0.

The code is MIT-licensed.
