# Fetch LiDAR Lens seabed tiles (EMODnet DTM 2024, MSL, zoom 10) over the same Web Mercator mosaic as h10.npy
import numpy as np, json, io, urllib.request
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
B='https://lidar-lens-gb.tim-daw.workers.dev/seabed/9/'
import math
n=512; tx=lambda lon:int((lon+180)/360*n); ty=lambda lat:int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
m={'z':9,'x0':tx(-16.5),'y0':ty(61.7)}; X1,Y1=tx(9.5),ty(48.8); Hs=((Y1-m['y0']+1)*256,(X1-m['x0']+1)*256)
idx=set(json.load(urllib.request.urlopen(urllib.request.Request('https://lidar-lens-gb.tim-daw.workers.dev/seabed/index.json',headers={'User-Agent':'gb-relief'})))['9'])
nx,ny=Hs[1]//256,Hs[0]//256
S=np.full(Hs,np.nan,np.float32)
def one(xy):
  x,y=xy
  if f'{x}_{y}' not in idx: return xy,None
  for t in range(3):
    try: b=urllib.request.urlopen(urllib.request.Request(B+f'{x}/{y}.webp',headers={'User-Agent':'gb-relief'}),timeout=60).read(); break
    except Exception: b=None
  if b is None: return xy,'fail'
  a=np.array(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.float64)
  h=a[...,0]*256+a[...,1]+(a[...,2].astype(np.int64)&252)/256-32768
  return xy,np.where(a[...,3]>0,h,np.nan).astype(np.float32)
fails=0
with ThreadPoolExecutor(16) as ex:
  for (x,y),t in ex.map(one,[(m['x0']+i,m['y0']+j) for i in range(nx) for j in range(ny)]):
    if t is None: continue
    if isinstance(t,str): fails+=1; continue
    S[(y-m['y0'])*256:(y-m['y0']+1)*256,(x-m['x0'])*256:(x-m['x0']+1)*256]=t
np.save('/home/claude/lgm/sea9.npy',S); json.dump(m,open('/home/claude/lgm/sea9.json','w')); print('fails',fails,'valid',np.isfinite(S).mean(),np.nanmin(S),np.nanmax(S))
