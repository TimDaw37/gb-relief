# Grid for the British-Irish Ice Sheet maximum-extent map: LAEA (GRS80, 55N 3W), 200 m.
# Modern GB/Ireland land and heights from the Britain-and-Ireland grid (bi_125m.npz); modern sea floor EMODnet (sea9.npy);
# palaeotopography at 26 ka (BRITICE-CHRONO, Bradley et al. GIA model, 500 m) for the palaeo-shoreline and continental relief;
# modern coast elsewhere from Natural Earth 10 m land.
import numpy as np, json, rasterio, geopandas as gpd
from scipy import ndimage
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
R='/home/claude/relief/'
P='+proj=laea +lat_0=55 +lon_0=-3 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs'
X0,Y0,X1,Y1,RES=-720000,760000,620000,-700000,200.0
W=int((X1-X0)/RES); H=int((Y0-Y1)/RES); xs=X0+(np.arange(W)+0.5)*RES; ys=Y0-(np.arange(H)+0.5)*RES
def sample(fn_xy, arr, order=1, cval=np.nan):
  out=np.empty((H,W),np.float32)
  for i0 in range(0,H,500):
    XX,YY=np.meshgrid(xs,ys[i0:i0+500]); c,r=fn_xy(XX,YY)
    out[i0:i0+500]=ndimage.map_coordinates(arr,[r,c],order=order,cval=cval,mode='constant')
  return out
# Britain-and-Ireland grid
bm=json.load(open(R+'bi_125m.json')); B=np.load(R+'bi_125m.npz'); t1=Transformer.from_crs(P,bm['proj'],always_xy=True)
def to_bi(X,Y): x,y=t1.transform(X,Y); return (x-bm['x0'])/bm['res']-0.5,(bm['y0']-y)/bm['res']-0.5
Hbi=sample(to_bi,B['H'].astype(np.float32),1,np.nan)
inbi=sample(to_bi,np.ones(B['H'].shape,np.float32),0,0)>0.5
gbie=sample(to_bi,B['land'].astype(np.float32),0,0)>0.5
water=sample(to_bi,B['water'].astype(np.float32),0,0)>0.5
# modern sea floor, zoom 9 Web Mercator
sm=json.load(open('sea9.json')); S=np.load('sea9.npy'); ok=np.isfinite(S); V=np.where(ok,S,0).astype(np.float32); K=ok.astype(np.float32); n=512
t2=Transformer.from_crs(P,4326,always_xy=True)
def to_merc(X,Y):
  lo,la=t2.transform(X,Y); return (lo+180)/360*256*n-sm['x0']*256-0.5,(1-np.arcsinh(np.tan(np.radians(la)))/np.pi)/2*256*n-sm['y0']*256-0.5
v=sample(to_merc,V,1,0); k=sample(to_merc,K,1,0); Sea=np.where(k>0.25,v/np.maximum(k,1e-6),np.nan)
# palaeotopography 26 ka (BNG, 500 m)
pr=rasterio.open('src/Data S5 BRITICE CHRONO palaeotopographies and coastlines GIS data/26_PT_500m.tif'); PT=pr.read(1).astype(np.float32); PT[PT>30000]=np.nan
t3=Transformer.from_crs(P,27700,always_xy=True); a=pr.transform
def to_pt(X,Y): e,nn=t3.transform(X,Y); return (e-a.c)/a.a-0.5,(nn-a.f)/a.e-0.5
okp=np.isfinite(PT); PTs=sample(to_pt,np.where(okp,PT,0),1,0); PTk=sample(to_pt,okp.astype(np.float32),1,0); PT=np.where(PTk>0.25,PTs/np.maximum(PTk,1e-6),np.nan)
# modern land elsewhere (Natural Earth 10 m), outside the Britain-and-Ireland grid
ne=gpd.read_file(R+'ne/ne_10m_land.geojson').explode(index_parts=False).cx[-20:15,45:66]
rp=ne.geometry.representative_point(); ne=ne[~((rp.x>-11)&(rp.x<1.9)&(rp.y>49.85)&(rp.y<61))].to_crs(P)   # not Britain, Ireland, Man
T=from_origin(X0,Y0,RES,RES)
neland=rasterize(((g,1) for g in ne.geometry if g is not None),out_shape=(H,W),transform=T,fill=0,dtype='uint8').astype(bool)
modern=gbie|neland
# surfaces: shading (modern detail where we have it) and value for tinting (palaeo elevation off GB/Ireland)
Sf=np.where(np.isfinite(Sea),Sea,PT)
bad=~np.isfinite(Sf)
if bad.any(): idx=ndimage.distance_transform_edt(bad,return_distances=False,return_indices=True); Sf=Sf[idx[0],idx[1]]
PTf=PT.copy(); bad=~np.isfinite(PTf)
if bad.any(): idx=ndimage.distance_transform_edt(bad,return_distances=False,return_indices=True); PTf=PTf[idx[0],idx[1]]
Hs=np.where(gbie,Hbi,np.where(modern,PTf,np.minimum(Sf,0)))
Hv=np.where(gbie,Hbi,PTf)                 # tint value: modern height on GB/Ireland, palaeo elevation elsewhere
paleoland=(PTf>0)|modern
np.savez('lgm_200m.npz',Hs=Hs.astype(np.float32),Hv=Hv.astype(np.float32),modern=modern,paleoland=paleoland,water=water&gbie)
json.dump({'proj':P,'x0':X0,'y0':Y0,'res':RES,'w':W,'h':H},open('lgm_200m.json','w'))
# ice envelopes in the map grid
for kind in ['optimum','max','min']:
  e=gpd.read_file(f'env_{kind}.gpkg').to_crs(P)
  m=rasterize(((g,1) for g in e.geometry if g is not None),out_shape=(H,W),transform=T,fill=0,dtype='uint8')
  np.save(f'ice_{kind}.npy',m.astype(bool))
print(W,H,'modern land',modern.mean(),'palaeo land',paleoland.mean())
