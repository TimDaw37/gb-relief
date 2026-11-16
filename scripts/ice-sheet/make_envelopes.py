# Union of the BRITICE-CHRONO empirical ice limits over all 1 ka slices (31-15 ka): optimum, max and min envelopes.
# Source: Clark et al. 2022, PANGAEA doi:10.1594/PANGAEA.945729 (Data S3 GIS zip), CC BY 4.0.
import geopandas as gpd, glob
from shapely import make_valid
from shapely.ops import unary_union
for folder in ['Optimum','max','min']:
  gs=[]
  for f in sorted(glob.glob(f'src/Data S3 BRITICE CHRONO empirical reconstruction GIS data/{folder}/*.shp')):
    g=gpd.read_file(f); g=g[g.geometry.notna()]; gs.append(g.geometry.apply(make_valid).union_all()); crs=g.crs
  gpd.GeoSeries([unary_union(gs)],crs=crs).to_file(f'env_{folder.lower()}.gpkg')
