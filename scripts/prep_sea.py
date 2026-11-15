# Reproject the zoom-10 seabed mosaic (EMODnet via LiDAR Lens) to the 100 m BNG grid; NaN where no seabed value
import numpy as np, json
from scipy import ndimage
from pyproj import Transformer
m=json.load(open('sea10.json')); n=1024; S=np.load('sea10.npy')
ok=np.isfinite(S); V=np.where(ok,S,0).astype(np.float32); K=ok.astype(np.float32); del S
R=100.0; E=np.arange(-20000,680000,R)+R/2; N=np.arange(1230000,-10000,-R)-R/2
tr=Transformer.from_crs(27700,4326,always_xy=True); out=np.full((len(N),len(E)),np.nan,np.float32)
for i0 in range(0,len(N),500):
  EE,NN=np.meshgrid(E,N[i0:i0+500]); LON,LAT=tr.transform(EE,NN)
  px=(LON+180)/360*256*n-m['x0']*256-0.5; py=(1-np.arcsinh(np.tan(np.radians(LAT)))/np.pi)/2*256*n-m['y0']*256-0.5
  v=ndimage.map_coordinates(V,[py,px],order=1,cval=0); k=ndimage.map_coordinates(K,[py,px],order=1,cval=0)
  out[i0:i0+500]=np.where(k>0.25,v/np.maximum(k,1e-6),np.nan)
np.save('bng_sea_100m.npy',out); print(np.isfinite(out).mean(), np.nanmin(out))
