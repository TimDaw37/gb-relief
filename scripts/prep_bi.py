# Britain and Ireland grid: Lambert azimuthal equal-area (ETRS89/GRS80, centre 54N 4.5W), 125 m cells.
# Land: OS Open Zoomstack in Great Britain, OSM land polygons (LiDAR Lens coastmask3) elsewhere.
# Heights: GB LiDAR/GEM-15 mosaic (h10.npy); Ireland GEM-15 (gemie10.npy); seabed EMODnet (sea10.npy).
import numpy as np, json
from scipy import ndimage
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import from_origin
P='+proj=laea +lat_0=54 +lon_0=-4.5 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs'
X0,Y0,X1,Y1,R=-470000,810000,470000,-490000,125.0
W=int((X1-X0)/R); H=int((Y0-Y1)/R)
xs=X0+(np.arange(W)+0.5)*R; ys=Y0-(np.arange(H)+0.5)*R
toLL=Transformer.from_crs(P,4326,always_xy=True); toBNG=Transformer.from_crs(P,27700,always_xy=True)
def merc_sample(arr,meta,order=1,nanaware=True,cval=np.nan):
  n=2**meta['z'] if 'z' in meta else 1024; out=np.empty((H,W),np.float32)
  if nanaware:
    ok=np.isfinite(arr); V=np.where(ok,arr,0).astype(np.float32); Kk=ok.astype(np.float32)
  for i0 in range(0,H,400):
    XX,YY=np.meshgrid(xs,ys[i0:i0+400]); lo,la=toLL.transform(XX,YY)
    px=(lo+180)/360*256*n-meta['x0']*256-0.5; py=(1-np.arcsinh(np.tan(np.radians(la)))/np.pi)/2*256*n-meta['y0']*256-0.5
    if nanaware:
      v=ndimage.map_coordinates(V,[py,px],order=order,cval=0); k=ndimage.map_coordinates(Kk,[py,px],order=order,cval=0)
      out[i0:i0+400]=np.where(k>0.25,v/np.maximum(k,1e-6),np.nan)
    else: out[i0:i0+400]=ndimage.map_coordinates(arr.astype(np.float32),[py,px],order=order,cval=0)
  return out
mh=json.load(open('h10.json')); ms=json.load(open('sea10.json'))
Hgb=merc_sample(np.load('h10.npy'),mh); Hgb[Hgb<-15]=np.nan
Hie=merc_sample(np.load('gemie10.npy'),ms)
Sea=merc_sample(np.load('sea10.npy'),ms)
Kosm=merc_sample(np.load('osmland10.npy'),ms,order=0,nanaware=False)
# GB rasters (BNG 100 m): Zoomstack land, water, foreshore
Mz=np.load('masks_100m.npz'); los=np.zeros((H,W),bool); wat=np.zeros((H,W),bool); fore=np.zeros((H,W),bool)
for i0 in range(0,H,400):
  XX,YY=np.meshgrid(xs,ys[i0:i0+400]); E,N=toBNG.transform(XX,YY)
  c=np.floor((E+20000)/100).astype(int); r=np.floor((1230000-N)/100).astype(int)
  ok=(c>=0)&(c<7000)&(r>=0)&(r<12400); cc=np.clip(c,0,6999); rr=np.clip(r,0,12399)
  los[i0:i0+400]=ok&(Mz['land'][rr,cc]>0); wat[i0:i0+400]=ok&(Mz['water'][rr,cc]>0); fore[i0:i0+400]=ok&(Mz['fore'][rr,cc]>0)
gbzone=ndimage.binary_dilation(los,iterations=24)          # 3 km round Great Britain: Zoomstack decides there
osm_land=(Kosm>=128)|((Kosm>0.5)&(Kosm<1.5)&(np.isfinite(Hie)|np.isfinite(Hgb)))   # coastmask3 coverage, or unmasked tiles with terrain
land=los|(osm_land&~gbzone)
Hl=np.where(los,Hgb,np.where(np.isfinite(Hie),Hie,Hgb))
# land with no terrain: whole components (France) become 'other land'; small gaps are filled from the nearest height
lab,k=ndimage.label(land); val=ndimage.mean(np.isfinite(Hl)&land,lab,range(1,k+1))
oth=land&np.isin(lab,np.where(val<0.3)[0]+1); land&=~oth
need=land&~np.isfinite(Hl)
if need.any():
  idx=ndimage.distance_transform_edt(~np.isfinite(Hl),return_distances=False,return_indices=True); Hl[need]=Hl[idx[0][need],idx[1][need]]; del idx
# Irish inland water: Natural Earth 10 m lakes (public domain) outside Great Britain
import pyogrio, geopandas as gpd
frames=[gpd.read_file(f'ne/{f}.geojson') for f in ['ne_10m_lakes','ne_10m_lakes_europe']]
import pandas as pd
lk=gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),crs=4326).cx[-11:-5,51:55.5].to_crs(P)
T=from_origin(X0,Y0,R,R)
wie=rasterize(((g,1) for g in lk.geometry if g is not None),out_shape=(H,W),transform=T,fill=0,dtype='uint8').astype(bool)&~gbzone
wat=(wat|wie)&land; fore&=~land
# continental Europe (France): Natural Earth 10 m land, shown flat as 'other land'
cont=gpd.read_file('ne/ne_10m_land.geojson').explode(index_parts=False).cx[-5:6,48:52.5]
rp=cont.geometry.representative_point(); cont=cont[~((rp.x<1.9)&(rp.y>49.85))].to_crs(P)   # drop Britain, Ireland and their islands
cmask=rasterize(((g,1) for g in cont.geometry if g is not None),out_shape=(H,W),transform=T,fill=0,dtype='uint8').astype(bool)
oth=(oth|(cmask&~ndimage.binary_dilation(land,iterations=8)))&~land
Sf=Sea.copy(); bad=~np.isfinite(Sf)
idx=ndimage.distance_transform_edt(bad,return_distances=False,return_indices=True); Sf=Sf[idx[0],idx[1]]; del idx
Hc=np.where(land,Hl,np.minimum(Sf,0.0)).astype(np.float32)
np.savez('bi_125m.npz',H=Hc,land=land,water=wat,fore=fore,oth=oth)
json.dump({'proj':P,'x0':X0,'y0':Y0,'res':R,'w':W,'h':H},open('bi_125m.json','w'))
print(W,H,'land',land.mean(),'oth',oth.mean(),'irish lakes px',wie.sum(),'water',wat.sum())
