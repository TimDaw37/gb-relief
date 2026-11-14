# Clean the zoom-10 Web Mercator mosaic and reproject to a British National Grid height grid (float32 .npy)
import numpy as np, json, sys
from scipy import ndimage
from pyproj import Transformer
z=10; H=np.load(f'h{z}.npy'); m=json.load(open(f'h{z}.json')); n=2**z
H[H<-15]=np.nan
nd=np.isnan(H); lab,_=ndimage.label(nd)
border=np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]); border=border[border>0]
hole=nd & ~np.isin(lab,border); del lab
print('holes px',hole.sum())
idx=ndimage.distance_transform_edt(nd,return_distances=False,return_indices=True).astype(np.int32)
H[hole]=H[idx[0][hole],idx[1][hole]]; del idx, nd
land=~np.isnan(H); lab,k=ndimage.label(land)
com=ndimage.center_of_mass(land,lab,range(1,k+1)); size=ndimage.sum(land,lab,range(1,k+1))
def rc2ll(r,c):
  r=m['y0']*256+r+0.5; c=m['x0']*256+c+0.5
  return c/(256*n)*360-180, np.degrees(np.arctan(np.sinh(np.pi*(1-2*r/(256*n)))))
drop=[]
for i,(r,c) in enumerate(com):
  lo,la=rc2ll(r,c)
  if (lo<-5.35 and 54.0<la<55.25) or (lo>-3.0 and la<49.95): drop.append(i+1)
H[np.isin(lab,drop)]=np.nan; del lab
Hz=np.where(np.isnan(H),np.float32(-50),H).astype(np.float32); del H
R=float(sys.argv[1]) if len(sys.argv)>1 else 100.0
E=np.arange(-20000,680000,R)+R/2; N=np.arange(1230000,-10000,-R)-R/2
tr=Transformer.from_crs(27700,4326,always_xy=True)
out=np.empty((len(N),len(E)),np.float32)
for i0 in range(0,len(N),500):
  EE,NN=np.meshgrid(E,N[i0:i0+500]); LON,LAT=tr.transform(EE,NN)
  px=(LON+180)/360*256*n-m['x0']*256-0.5
  py=(1-np.arcsinh(np.tan(np.radians(LAT)))/np.pi)/2*256*n-m['y0']*256-0.5
  out[i0:i0+500]=ndimage.map_coordinates(Hz,[py,px],order=1,cval=-50.0,output=np.float32)
out[out<-15]=np.nan
np.save(f'bng_{int(R)}m.npy',out); print(out.shape, np.nanmax(out))
