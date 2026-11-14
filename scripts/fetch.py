import numpy as np, math, io, sys, urllib.request, json, os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
B='https://lidar-lens-gb.tim-daw.workers.dev/'
z=int(sys.argv[1]); n=2**z
def tx(lon): return int((lon+180)/360*n)
def ty(lat): return int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
X=range(tx(-8.8),tx(1.8)+1); Y=range(ty(61.0),ty(49.8)+1)
def get(u):
  try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'relief-test'}),timeout=60).read()
  except Exception: return None
def dec(b):
  a=np.array(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.float64)
  h=a[...,0]*256+a[...,1]+a[...,2]/256-32768; return np.where(a[...,3]>=128,h,np.nan)
def one(xy):
  x,y=xy; out=np.full((256,256),np.nan,np.float32)
  srcs=[f'gbov/{z}/{x}/{y}.png'] if z<8 else [f'terrain/{z}/{x}/{y}.webp',f'ewov/{z}/{x}/{y}.png',f'gem15/{z}/{x}/{y}.webp']
  for s in srcs:
    b=get(B+s)
    if b:
      h=dec(b); out=np.where(np.isnan(out),h,out).astype(np.float32)
      if not np.isnan(out).any(): break
  return xy,out
H=np.full((len(Y)*256,len(X)*256),np.nan,np.float32)
with ThreadPoolExecutor(16) as ex:
  for (x,y),t in ex.map(one,[(x,y) for x in X for y in Y]):
    H[(y-Y[0])*256:(y-Y[0]+1)*256,(x-X[0])*256:(x-X[0]+1)*256]=t
np.save(f'h{z}.npy',H); json.dump(dict(z=z,x0=X[0],y0=Y[0]),open(f'h{z}.json','w'))
print(H.shape, np.nanmin(H), np.nanmax(H), np.isnan(H).mean())
