# Rasterise OS Open Zoomstack land (to mean high water), surface water and foreshore to the 100 m BNG grid
import numpy as np, pyogrio, sys
from rasterio.features import rasterize
from rasterio.transform import from_origin
G='os/OS_Open_Zoomstack.gpkg'; T=from_origin(-20000,1230000,100,100); S=(12400,7000)
def r(layer,where=None):
  df=pyogrio.read_dataframe(G,layer=layer,where=where,columns=[])
  return rasterize(((g,1) for g in df.geometry if g is not None),out_shape=S,transform=T,fill=0,dtype='uint8')
land=r('land'); print('land',land.mean())
water=r('surfacewater',"type IN ('National','Regional')"); print('water',water.mean())
fore=r('foreshore'); print('fore',fore.mean())
np.savez_compressed('masks_100m.npz',land=land,water=water,fore=fore)
