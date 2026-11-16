# Cut Web Mercator XYZ tiles (z5-11) from the BNG relief masters: WebP with alpha (sea transparent).
import numpy as np, math, os, sys
from PIL import Image
from scipy import ndimage
from pyproj import Transformer
from multiprocessing import Pool
Image.MAX_IMAGE_PIXELS=None
V=sys.argv[1]; BI=V.endswith('-bi'); OUT=f'pkg/gb-relief/tiles/{V}'
if BI:
  import json; _m=json.load(open('bi_125m.json')); X0,Y0=_m['x0'],_m['y0']; CRS=_m['proj']; SRC={5:(500,2800),6:(500,1400),7:(500,700),8:(250,350),9:(250,250),10:(125,125),11:(125,125)}
else: X0,Y0=-20000,1230000; CRS=27700
SRC0={5:(400,2800),6:(400,1400),7:(400,700),8:(200,350),9:(200,200),10:(100,100),11:(100,100)}
SRC=SRC if BI else SRC0
TR=Transformer.from_crs(4326,CRS,always_xy=True)
A=None; RES=None
def load(z):
  global A,RES
  m,r=SRC[z]; im=Image.open(f'masters/bi-{V[:-3]}-{m}m.png' if BI else f'masters/{V}-{m}m.png')
  if r!=m: im=im.resize((round(im.width*m/r),round(im.height*m/r)),Image.BOX)
  A=np.asarray(im).astype(np.float32); RES=r
def tile(args):
  z,x,y=args; n=2**z; i=(np.arange(256)+0.5)/256
  lon=(x+i)/n*360-180; lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(y+i)/n))))
  LO,LA=np.meshgrid(lon,lat); E,N=TR.transform(LO,LA)
  c=(E-X0)/RES-0.5; r=(Y0-N)/RES-0.5
  if c.max()<0 or r.max()<0 or c.min()>A.shape[1] or r.min()>A.shape[0]: return 0
  a=ndimage.map_coordinates(A[...,3],[r,c],order=1,cval=0)
  if a.max()<8: return 0
  rgb=[ndimage.map_coordinates(A[...,k],[r,c],order=1,mode='nearest') for k in range(3)]
  t=np.dstack(rgb+[a]).clip(0,255).astype(np.uint8)
  os.makedirs(f'{OUT}/{z}/{x}',exist_ok=True); Image.fromarray(t,'RGBA').save(f'{OUT}/{z}/{x}/{y}.webp',quality=82,method=4)
  return 1
if __name__=='__main__':
  for z in range(5,12):
    load(z); n=2**z
    x0=int(((-11.8 if BI else -10.5)+180)/360*n); x1=int((4.5+180)/360*n)
    y0=int((1-math.asinh(math.tan(math.radians(61.4)))/math.pi)/2*n); y1=int((1-math.asinh(math.tan(math.radians(49.4)))/math.pi)/2*n)
    jobs=[(z,x,y) for x in range(x0,x1+1) for y in range(y0,y1+1)]
    with Pool(2) as p: k=sum(p.map(tile,jobs,chunksize=16))
    print(V,z,k,'of',len(jobs),flush=True)
