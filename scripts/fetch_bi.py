# Ireland for the Britain-and-Ireland maps: GEM-15 (gem15/ie, zoom 10) and the OSM land-coverage coast mask (coastmask3, zoom 10),
# both from the LiDAR Lens Worker, into the same zoom-10 Web Mercator frame as sea10.npy
import numpy as np, json, io, urllib.request
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
B='https://lidar-lens-gb.tim-daw.workers.dev/'
def get(u):
  for t in range(3):
    try: return urllib.request.urlopen(urllib.request.Request(B+u,headers={'User-Agent':'gb-relief'}),timeout=60).read()
    except urllib.error.HTTPError as e:
      if e.code==404: return None
    except Exception: pass
  raise RuntimeError('failed '+u)
m=json.load(open('sea10.json')); Hs=np.load('sea10.npy',mmap_mode='r').shape; nx,ny=Hs[1]//256,Hs[0]//256
keys=[(m['x0']+i,m['y0']+j) for i in range(nx) for j in range(ny)]
gi=set(json.loads(get('gem15/ie/index.json'))['10']); C=json.loads(get('coastmask3/index.json'))
M={z:set(v) for z,v in C['m'].items()}; L={z:set(v) for z,v in C['l'].items()}
B10=set(C['b10'])
def cls(x,y):   # as coastClass() in gb/seabed-route.js, zoom 10 (no mask outside b10: land wherever there is terrain)
  if f'{x}_{y}' not in B10: return 'nomask'
  for k in range(C['top'],11):
    d=10-k; key=f'{x>>d}_{y>>d}'
    if key in M.get(str(k),()): continue
    return 'land' if key in L.get(str(k),()) else 'sea'
  return 'mixed'
G=np.full(Hs,np.nan,np.float32); K=np.zeros(Hs,np.uint8)
def one(xy):
  x,y=xy; g=None; k=None
  if f'{x}_{y}' in gi:
    b=get(f'gem15/ie/10/{x}/{y}.webp')
    if b:
      a=np.array(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.float64)
      g=np.where(a[...,3]>0,a[...,0]*256+a[...,1]+(a[...,2].astype(np.int64)&252)/256-32768,np.nan).astype(np.float32)
  c=cls(x,y)
  if c=='land': k=np.full((256,256),255,np.uint8)
  elif c=='nomask': k=np.full((256,256),1,np.uint8)
  elif c=='mixed':
    b=get(f'coastmask3/10/{x}/{y}.png'); k=np.array(Image.open(io.BytesIO(b)))
    if k.ndim==3: k=k[...,0]
  return xy,g,k
with ThreadPoolExecutor(16) as ex:
  for (x,y),g,k in ex.map(one,keys):
    sl=(slice((y-m['y0'])*256,(y-m['y0']+1)*256),slice((x-m['x0'])*256,(x-m['x0']+1)*256))
    if g is not None: G[sl]=g
    if k is not None: K[sl]=k
np.save('gemie10.npy',G); np.save('osmland10.npy',K)
print('nomask',(K==1).mean(),'gem valid',np.isfinite(G).mean(),'land',(K>=128).mean())
