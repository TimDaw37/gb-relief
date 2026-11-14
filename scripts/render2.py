# Render GB relief images from the BNG height grid.  python3 render2.py WIDTH VARIANT EXAG [GEOL.png]
# VARIANT: relief (hypsometric tint + hillshade), grey (hillshade), tint (hypsometric tint only), geology
import numpy as np, sys, math
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
W=int(sys.argv[1]); V=sys.argv[2]; ex=float(sys.argv[3])
H0=np.load('bng_100m.npy'); X0,Y0=-20000,1230000; R0=100.0
M=np.load('masks_100m.npz'); los=M['land'].astype(bool); wat0=M['water'].astype(bool); fore0=M['fore'].astype(bool)&~los
valid=~np.isnan(H0)
# Isle of Man is outside OS GB coverage: keep the DTM there (BNG box E 215-250 km, N 465-505 km)
iom=np.zeros_like(los); iom[(Y0-505000)//100:(Y0-465000)//100,(215000-X0)//100:(250000-X0)//100]=True
land0=(los|(valid&iom))
need=land0&~valid
if need.any():
  idx=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True); H0[need]=H0[idx[0][need],idx[1][need]]; del idx
fore0&=~land0
Hz0=np.where(land0,H0,0).astype(np.float32)
Wd=W; Ht=round(H0.shape[0]*W/H0.shape[1]); res=R0*H0.shape[1]/W
if W!=H0.shape[1]:
  fr=np.asarray(Image.fromarray(land0.astype(np.float32)).resize((Wd,Ht),Image.BOX))
  hs_=np.asarray(Image.fromarray(Hz0).resize((Wd,Ht),Image.BOX))
  land=fr>0.5; H=np.where(land,hs_/np.maximum(fr,1e-6),0).astype(np.float32)
  wat=np.asarray(Image.fromarray(wat0.astype(np.float32)).resize((Wd,Ht),Image.BOX))>0.5
  fore=np.asarray(Image.fromarray(fore0.astype(np.float32)).resize((Wd,Ht),Image.BOX))>0.5
else: land=land0; H=Hz0; wat=wat0; fore=fore0
del H0,Hz0,land0,wat0,fore0,los,valid
gy,gx=np.gradient(H); p=gx/res*ex; q=-gy/res*ex; del gy,gx
slope=np.arctan(np.hypot(p,q)); asp=np.arctan2(q,-p); del p,q
def hs(az,alt):
  az=math.radians(360-az+90); alt=math.radians(alt)
  return np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-asp),0,1).astype(np.float32)
shade=0.5*hs(315,40)+0.2*hs(270,40)+0.2*hs(0,40)+0.1*hs(225,40); del slope,asp
stops=[(-5,(120,150,110)),(0,(132,165,118)),(50,(160,185,130)),(150,(205,205,150)),(300,(215,190,140)),(500,(190,155,115)),(800,(165,135,115)),(1100,(215,210,205)),(1400,(250,250,250))]
def tint(h):
  return np.stack([np.interp(h,[s[0] for s in stops],[s[1][c] for s in stops]).astype(np.float32) for c in range(3)],-1)
SEA=np.array([214,226,232],np.float32)
if V=='relief': img=tint(H)*(0.35+0.85*shade[...,None])
elif V=='grey': img=np.repeat((255*(0.25+0.8*shade))[...,None],3,-1); SEA=np.array([240,240,240],np.float32)
elif V=='tint': img=tint(H)
elif V=='geology':
  G=np.asarray(Image.open(sys.argv[4]).convert('RGB').resize((Wd,Ht),Image.NEAREST)).astype(np.float32)
  img=G*(0.45+0.7*shade[...,None])
lw,kw=ndimage.label(wat); szw=ndimage.sum(wat,lw,range(1,kw+1)); wat=np.isin(lw,np.where(szw>=3)[0]+1); del lw
img=np.clip(img,0,255); dry=land&~wat
img[~dry]=SEA
FORE=SEA*0.55+np.array([236,226,200],np.float32)*0.45 if V!='grey' else np.array([228,228,228],np.float32)
img[fore&~dry]=FORE
e=dry & ~ndimage.binary_erosion(dry); img[e]*=0.75
import os
if os.environ.get('NOPANEL'):
  a=((land|fore)*255).astype(np.uint8)   # sea transparent; land, inland water and foreshore opaque
  Image.fromarray(np.dstack([img.astype(np.uint8),a]),'RGBA').save(f'masters/{V}-{round(res)}m.png'); print('master',V,round(res)); sys.exit()
im=Image.fromarray(img.astype(np.uint8)); del img
# --- text panel in the North Sea (E 460-680 km, N 700-960 km), title, scale bar, credits
d=ImageDraw.Draw(im); F='/usr/share/fonts/truetype/dejavu/'
def px(E,N): return ((E-X0)/res,(Y0-N)/res)
x0,y0=px(462000,975000); x1,_=px(680000,0); w=x1-x0
s=W/7000
fT=ImageFont.truetype(F+'DejaVuSerif-Bold.ttf',max(24,int(150*s))); fS=ImageFont.truetype(F+'DejaVuSans.ttf',max(12,int(62*s)))
fC=ImageFont.truetype(F+'DejaVuSans.ttf',max(10,int(46*s)))
ink=(40,50,60); y=y0
d.text((x0,y),'Great Britain',font=fT,fill=ink); y+=fT.size*1.25
sub={'relief':'Shaded relief','grey':'Shaded relief','tint':'Elevation','geology':'Bedrock geology on shaded relief'}[V]
for line in [sub, f'{res:.0f} m grid · British National Grid']+([] if V=='tint' else [f'Vertical exaggeration {ex:g}×']):
  d.text((x0,y),line,font=fS,fill=ink); y+=fS.size*1.35
# scale bar 100 km
y+=fS.size*0.6; L=100000/res; bh=max(3,int(18*s))
for i in range(4):
  d.rectangle([x0+i*L/4,y,x0+(i+1)*L/4,y+bh],fill=ink if i%2==0 else (255,255,255),outline=ink,width=max(1,int(3*s)))
for t,xx in [('0',x0),('50',x0+L/2),('100 km',x0+L)]:
  d.text((xx,y+bh+fC.size*0.3),t,font=fC,fill=ink,anchor='ma' if t!='100 km' else 'la')
y+=bh+fC.size*2.2
if V=='geology':
  import json; Lg=json.load(open('geol_legend.json')); rows=(len(Lg)+1)//2; sw=fC.size*1.1; cw=(W*0.985-x0)/2
  for i,(t,c) in enumerate(Lg):
    xx=x0+(i//rows)*cw; yy=y+(i%rows)*fC.size*1.45
    d.rectangle([xx,yy,xx+sw*1.4,yy+sw],fill=tuple(c),outline=ink,width=max(1,int(2*s))); d.text((xx+sw*1.8,yy-fC.size*0.05),t,font=fC,fill=ink)
  y+=rows*fC.size*1.45+fC.size*1.2
cred=['LiDAR DTMs: Environment Agency (England); Welsh Government, DataMapWales (Wales); Scottish Government, SEPA, HES, OIC, Scottish Remote Sensing Portal (Scotland). Open Government Licence v3.0.',
      'Where no open LiDAR exists: GEM-15 v1 (experimental), produced by Google, CC BY 4.0 (Batchu et al. 2026).',
      'Coastline, inland water and foreshore: OS Open Zoomstack. Contains OS data © Crown copyright and database right 2026.']
if V=='geology': cred+=['Bedrock geology: BGS Geology 625k (DiGMapGB-625). Contains British Geological Survey materials © UKRI. Open Government Licence v3.0.']
cred+=['Tim Daw · sarsen.org · lidarlens.sarsen.org']
maxw=W*0.985-x0
def wrap(t):
  out=[];cur=''
  for wd in t.split():
    if d.textlength((cur+' '+wd).strip(),font=fC)>maxw: out.append(cur); cur=wd
    else: cur=(cur+' '+wd).strip()
  return out+[cur]
cred=[l for c in cred for l in wrap(c)+['']]
for line in cred: d.text((x0,y),line,font=fC,fill=ink); y+=fC.size*1.3
out=f'out/gb-{V}-{W}px'
im.save(out+'.png',optimize=True); im.convert('RGB').save(out+'.jpg',quality=88); print(out, im.size, round(res))
