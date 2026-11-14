# Pack the BNG grids into lossless WebP sheets for the interactive viewer.
# Pixel: R,G = height code v = round((h + 100) * 4) (0.25 m steps), B = class
# (0 sea, 1 foreshore, 2 inland water, 10 + g land with BGS 625k unit g), A = 255.
# Levels 100/200/400/800 m; sheets of 1750 x 3100 data px plus a 1 px overlap margin.
import numpy as np, json, os
from PIL import Image
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
X0,Y0=-20000,1230000
H=np.load('bng_100m.npy'); M=np.load('masks_100m.npz'); G=np.load('geolidx_100m.npy')
los=M['land'].astype(bool); wat=M['water'].astype(bool); fore=M['fore'].astype(bool)
valid=~np.isnan(H)
iom=np.zeros_like(los); iom[(Y0-505000)//100:(Y0-465000)//100,(215000-X0)//100:(250000-X0)//100]=True
land=los|(valid&iom)
need=land&~valid
idx=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True); H[need]=H[idx[0][need],idx[1][need]]; del idx
fore&=~land
Hz=np.where(land,H,0).astype(np.float32); del H
os.makedirs('web/data',exist_ok=True)
SW,SH=1750,3100; meta={'x0':X0,'y0':Y0,'sheetW':SW,'sheetH':SH,'levels':{}}
def classes(lnd,wt,fr,g):
  c=np.zeros(lnd.shape,np.uint8); c[fr]=1; c[lnd]=10+g[lnd]; c[lnd&wt]=2; return c
for res in [100,200,400,800]:
  f=res//100
  if f==1: h,c=Hz,classes(land,wat,fore,G)
  else:
    Wd,Ht=7000//f,12400//f
    fr_=np.asarray(Image.fromarray(land.astype(np.float32)).resize((Wd,Ht),Image.BOX))
    hs_=np.asarray(Image.fromarray(Hz).resize((Wd,Ht),Image.BOX))
    l=fr_>0.5; h=np.where(l,hs_/np.maximum(fr_,1e-6),0).astype(np.float32)
    w=np.asarray(Image.fromarray(wat.astype(np.float32)).resize((Wd,Ht),Image.BOX))>0.5
    fo=np.asarray(Image.fromarray(fore.astype(np.float32)).resize((Wd,Ht),Image.BOX))>0.5
    g=G[f//2::f,f//2::f][:Ht,:Wd]
    c=classes(l,w,fo&~l,g)
  v=np.clip(np.round((h+100)*4),0,65535).astype(np.uint16)
  rgba=np.stack([(v>>8).astype(np.uint8),(v&255).astype(np.uint8),c,np.full(c.shape,255,np.uint8)],-1)
  ny=-(-rgba.shape[0]//SH); nx=-(-rgba.shape[1]//SW); sheets=[]
  P=np.zeros((ny*SH+2,nx*SW+2,4),np.uint8); P[...,1]=(400&255); P[...,0]=400>>8; P[...,3]=255
  P[1:1+rgba.shape[0],1:1+rgba.shape[1]]=rgba
  for j in range(ny):
    for i in range(nx):
      s=P[j*SH:j*SH+SH+2,i*SW:i*SW+SW+2]
      if (s[1:-1,1:-1,2]==0).all(): continue
      fn=f'data/L{res}_{i}_{j}.webp'; Image.fromarray(s,'RGBA').save('web/'+fn,lossless=True,quality=100,method=4)
      sheets.append([i,j]); print(fn,os.path.getsize('web/'+fn)//1024,'KB',flush=True)
  meta['levels'][res]={'w':rgba.shape[1],'h':rgba.shape[0],'nx':nx,'ny':ny,'sheets':sheets}
json.dump(meta,open('web/data/meta.json','w'))
