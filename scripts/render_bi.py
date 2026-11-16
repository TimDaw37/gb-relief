# Render Britain-and-Ireland images from bi_125m.npz.  python3 render_bi.py WIDTH VARIANT EXAG   (VARIANT: relief, grey, tint)
import numpy as np, sys, math, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from pyproj import Transformer
Image.MAX_IMAGE_PIXELS=None
W=int(sys.argv[1]); V=sys.argv[2]; ex=float(sys.argv[3])
meta=json.load(open('bi_125m.json')); D=np.load('bi_125m.npz')
X0,Y0,R0=meta['x0'],meta['y0'],meta['res']
Wd=W; Ht=round(meta['h']*W/meta['w']); res=R0*meta['w']/W
def down(a): return np.asarray(Image.fromarray(a.astype(np.float32)).resize((Wd,Ht),Image.BOX))
if W!=meta['w']: H=down(D['H']); land=down(D['land'])>0.5; wat=down(D['water'])>0.5; fore=down(D['fore'])>0.5; oth=down(D['oth'])>0.5
else: H=D['H']; land=D['land']; wat=D['water']; fore=D['fore']; oth=D['oth']
sea=~land&~oth
gy,gx=np.gradient(H); p=gx/res*ex; q=-gy/res*ex; del gy,gx
slope=np.arctan(np.hypot(p,q)); asp=np.arctan2(q,-p); del p,q
def hs(az,alt):
  az=math.radians(360-az+90); alt=math.radians(alt)
  return np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-asp),0,1).astype(np.float32)
shade=0.5*hs(315,40)+0.2*hs(270,40)+0.2*hs(0,40)+0.1*hs(225,40); del slope,asp
LAND=[(-5,(120,150,110)),(0,(132,165,118)),(50,(160,185,130)),(150,(205,205,150)),(300,(215,190,140)),(500,(190,155,115)),(800,(165,135,115)),(1100,(215,210,205)),(1400,(250,250,250))]
BATHY=[(-2000,(38,66,112)),(-1000,(52,88,140)),(-500,(70,114,166)),(-200,(92,140,186)),(-100,(116,162,200)),(-60,(138,180,212)),(-30,(162,198,222)),(-10,(184,212,228)),(0,(200,222,232)),(8,(214,230,236))]
def ramp(h,st): return np.stack([np.interp(h,[s[0] for s in st],[s[1][c] for s in st]).astype(np.float32) for c in range(3)],-1)
sh=shade[...,None]
if V=='grey':
  img=np.repeat((255*(0.25+0.8*shade))[...,None],3,-1); img[sea]=np.repeat((228*(0.62+0.45*shade))[...,None],3,-1)[sea]
  OTH=np.array([236,236,236],np.float32); WATER=np.array([226,232,236],np.float32)
else:
  img=ramp(H,LAND)*(0.35+0.85*sh) if V=='relief' else ramp(H,LAND)
  B=ramp(H,BATHY); img[sea]=(B if V=='tint' else B*(0.62+0.45*sh))[sea]
  OTH=np.array([232,229,222],np.float32); WATER=np.array([196,218,230],np.float32)
del shade,sh
lw,kw=ndimage.label(wat&land); szw=ndimage.sum(wat,lw,range(1,kw+1)); wat=np.isin(lw,np.where(szw>=3)[0]+1); del lw
img=np.clip(img,0,255); dry=land&~wat
img[land&wat]=WATER; img[oth]=OTH
img[fore&~land]=img[fore&~land]*0.55+np.array([236,226,200],np.float32)*0.45
e=dry&~ndimage.binary_erosion(dry); img[e]*=0.72
e2=oth&~ndimage.binary_erosion(oth); img[e2]*=0.85
import os
if os.environ.get('NOPANEL'):
  a=np.where(oth,0,255).astype(np.float32); f=max(2,int(20000/res)); yy=np.arange(Ht)[:,None]; xx=np.arange(Wd)[None,:]
  a*=np.clip(np.minimum(np.minimum(yy,Ht-1-yy),np.minimum(xx,Wd-1-xx)).astype(np.float32)/f,0,1)   # fade over the outer 20 km
  Image.fromarray(np.dstack([img.astype(np.uint8),a.astype(np.uint8)]),'RGBA').save(f'masters/bi-{V}-{round(res)}m.png'); print('master',V,round(res)); sys.exit()
im=Image.fromarray(img.astype(np.uint8)).convert('RGBA'); del img
F='/usr/share/fonts/truetype/dejavu/'; ink=(40,50,60); s=W/7000
def px(x,y): return ((x-X0)/res,(Y0-y)/res)
fT=ImageFont.truetype(F+'DejaVuSerif-Bold.ttf',max(22,int(140*s))); fS=ImageFont.truetype(F+'DejaVuSans.ttf',max(12,int(60*s))); fC=ImageFont.truetype(F+'DejaVuSans.ttf',max(10,int(44*s)))
pad=max(8,int(40*s)); probe=ImageDraw.Draw(im)
def wrap(t,font,maxw):
  out=[];cur=''
  for wd in t.split():
    if probe.textlength((cur+' '+wd).strip(),font=font)>maxw: out.append(cur); cur=wd
    else: cur=(cur+' '+wd).strip()
  return out+[cur]
def boxed(x0,y0,x1,draw_fn):
  yend=draw_fn(None)
  b=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(b).rectangle([x0-pad,y0-pad,x1,yend+pad*0.6],fill=(246,248,249,225))
  return Image.alpha_composite(im,b),yend
# title panel in the North Sea
tx0,ty0=px(262000,700000); tx1=W*0.985; tw=tx1-tx0-pad
while probe.textlength('Britain and Ireland',font=fT)>tw: fT=ImageFont.truetype(F+'DejaVuSerif-Bold.ttf',fT.size-1)
sub={'relief':'Shaded relief and sea floor','grey':'Shaded relief and sea floor','tint':'Elevation and depth'}[V]
subs=[l for t in [sub,f'{res:.0f} m grid · Lambert azimuthal equal-area (54° N, 4.5° W)']+([] if V=='tint' else [f'Vertical exaggeration {ex:g}×']) for l in wrap(t,fS,tw)]
BL=[(-10,'0'),(-50,'50'),(-100,'100'),(-200,'200'),(-1000,'1000 m')]
def title(d):
  y=ty0
  if d: d.text((tx0,y),'Britain and Ireland',font=fT,fill=ink)
  y+=fT.size*1.25
  for line in subs:
    if d: d.text((tx0,y),line,font=fS,fill=ink)
    y+=fS.size*1.35
  y+=fS.size*0.6; L=100000/res; bh=max(3,int(18*s))
  if d:
    for i in range(4): d.rectangle([tx0+i*L/4,y,tx0+(i+1)*L/4,y+bh],fill=ink if i%2==0 else (255,255,255),outline=ink,width=max(1,int(3*s)))
    for t,xx in [('0',tx0),('50',tx0+L/2),('100 km',tx0+L)]: d.text((xx,y+bh+fC.size*0.3),t,font=fC,fill=ink,anchor='ma' if t!='100 km' else 'la')
  y+=bh+fC.size*2.2
  if V!='grey':
    sw=tw/len(BL)
    if d: d.text((tx0,y),'Sea depth below mean sea level',font=fC,fill=ink)
    y+=fC.size*1.45
    if d:
      for i,(dep,lab) in enumerate(BL):
        c=tuple(int(v) for v in ramp(np.array([dep],np.float32),BATHY)[0]); d.rectangle([tx0+i*sw,y,tx0+(i+1)*sw,y+fC.size*1.1],fill=c,outline=ink,width=max(1,int(2*s)))
        d.text((tx0+i*sw+sw/2,y+fC.size*1.35),lab,font=fC,fill=ink,anchor='ma')
    y+=fC.size*2.8
  return y
im,_=boxed(tx0,ty0,tx1,title); title(ImageDraw.Draw(im))
# credits in a footer strip below the map
cred='Land: LiDAR DTMs of the Environment Agency (England), Welsh Government, DataMapWales (Wales) and Scottish Government, SEPA, HES, OIC, Scottish Remote Sensing Portal (Scotland), Open Government Licence v3.0. Ireland, the Isle of Man and gaps in Scotland: GEM-15 v1 (experimental), produced by Google, CC BY 4.0 (Batchu et al. 2026). Sea floor: EMODnet Digital Bathymetry (DTM 2024), mean sea level, CC BY 4.0, not for navigation. Coast: OS Open Zoomstack in Great Britain (contains OS data © Crown copyright and database right 2026); OpenStreetMap land polygons elsewhere (© OpenStreetMap contributors, ODbL); Irish lakes and the Continent: Natural Earth. Tim Daw · sarsen.org · lidarlens.sarsen.org'
cl=wrap(cred,fC,W-2*pad); fh=int(pad*1.6+len(cl)*fC.size*1.3)
canvas=Image.new('RGBA',(W,Ht+fh),(246,248,249,255)); canvas.paste(im,(0,0)); im=canvas; d=ImageDraw.Draw(im)
y=Ht+pad*0.8
for line in cl: d.text((pad,y),line,font=fC,fill=ink); y+=fC.size*1.3
im=im.convert('RGB'); out=f'out_bi/britain-ireland-{V}-{W}px'
im.save(out+'.png',optimize=True); im.save(out+'.jpg',quality=88); print(out, im.size, round(res))
