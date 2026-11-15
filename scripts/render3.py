# Render GB relief images with seabed from the BNG grids.  python3 render3.py WIDTH VARIANT EXAG [GEOL.png]
# VARIANT: relief (hypsometric/bathymetric tint + hillshade), grey (hillshade), tint (tints only), geology
# NOPANEL=1: write an RGBA master for tile cutting (other countries transparent, alpha fading at the frame edge)
import numpy as np, sys, math, os, json
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
W=int(sys.argv[1]); V=sys.argv[2]; ex=float(sys.argv[3]); NOP=bool(os.environ.get('NOPANEL'))
X0,Y0,R0=-20000,1230000,100.0
H0=np.load('bng_100m.npy'); S0=np.load('bng_sea_100m.npy')
M=np.load('masks_100m.npz'); los=M['land'].astype(bool); wat0=M['water'].astype(bool); fore0=M['fore'].astype(bool)&~los
valid=~np.isnan(H0)
iom=np.zeros_like(los); iom[(Y0-505000)//100:(Y0-465000)//100,(215000-X0)//100:(250000-X0)//100]=True
land0=(los|(valid&iom))
need=land0&~valid
if need.any():
  idx=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True); H0[need]=H0[idx[0][need],idx[1][need]]; del idx
fore0&=~land0
sea0=~land0&np.isfinite(S0)            # seabed (EMODnet) beyond the GB coast
oth0=~land0&~sea0                       # land of other countries (Ireland, France): no data here
# one continuous surface for shading: LiDAR/GEM-15 on GB land, EMODnet offshore, nearest seabed value under other land
Sf=S0.copy(); bad=~np.isfinite(Sf)
if bad.any():
  idx=ndimage.distance_transform_edt(bad,return_distances=False,return_indices=True); Sf=Sf[idx[0],idx[1]]; del idx
Hc0=np.where(land0,H0,np.minimum(Sf,0.0)).astype(np.float32); del H0,S0,Sf
Wd=W; Ht=round(Hc0.shape[0]*W/Hc0.shape[1]); res=R0*Hc0.shape[1]/W
def down(a,mode=Image.BOX): return np.asarray(Image.fromarray(a.astype(np.float32)).resize((Wd,Ht),mode))
if W!=Hc0.shape[1]:
  H=down(Hc0); land=down(land0)>0.5; wat=down(wat0)>0.5; fore=down(fore0)>0.5; oth=down(oth0)>0.5
else: H,land,wat,fore,oth=Hc0,land0,wat0,fore0,oth0
del Hc0,land0,wat0,fore0,oth0,los,valid,sea0
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
  img=np.repeat((255*(0.25+0.8*shade))[...,None],3,-1)
  img[sea]=np.repeat((228*(0.62+0.45*shade))[...,None],3,-1)[sea]
  OTH=np.array([236,236,236],np.float32); WATER=np.array([226,232,236],np.float32)
else:
  if V=='relief': img=ramp(H,LAND)*(0.35+0.85*sh)
  elif V=='tint': img=ramp(H,LAND)
  elif V=='geology':
    G=np.asarray(Image.open(sys.argv[4]).convert('RGB').resize((Wd,Ht),Image.NEAREST)).astype(np.float32); img=G*(0.45+0.7*sh)
  B=ramp(H,BATHY); img[sea]=(B if V=='tint' else B*(0.62+0.45*sh))[sea]
  OTH=np.array([232,229,222],np.float32); WATER=np.array([196,218,230],np.float32)
del shade,sh
lw,kw=ndimage.label(wat&land); szw=ndimage.sum(wat,lw,range(1,kw+1)); wat=np.isin(lw,np.where(szw>=3)[0]+1); del lw
img=np.clip(img,0,255); dry=land&~wat
img[land&wat]=WATER
img[oth]=OTH
img[fore&~land]=img[fore&~land]*0.55+np.array([236,226,200],np.float32)*0.45
e=dry&~ndimage.binary_erosion(dry); img[e]*=0.72
e2=oth&~ndimage.binary_erosion(oth); img[e2]*=0.85
if NOP:
  a=np.where(oth,0,255).astype(np.float32)
  f=max(2,int(20000/res)); yy=np.arange(Ht)[:,None]; xx=np.arange(Wd)[None,:]
  edge=np.minimum(np.minimum(yy,Ht-1-yy),np.minimum(xx,Wd-1-xx)).astype(np.float32)
  a*=np.clip(edge/f,0,1)                                   # fade over the outer 20 km of the frame
  Image.fromarray(np.dstack([img.astype(np.uint8),a.astype(np.uint8)]),'RGBA').save(f'masters/{V}-{round(res)}m.png'); print('master',V,round(res)); sys.exit()
im=Image.fromarray(img.astype(np.uint8)).convert('RGBA'); del img
# --- text panel in the North Sea on a light box
F='/usr/share/fonts/truetype/dejavu/'
def px(E,N): return ((E-X0)/res,(Y0-N)/res)
x0,y0=px(462000,975000); s=W/7000
fT=ImageFont.truetype(F+'DejaVuSerif-Bold.ttf',max(24,int(150*s))); fS=ImageFont.truetype(F+'DejaVuSans.ttf',max(12,int(62*s)))
fC=ImageFont.truetype(F+'DejaVuSans.ttf',max(10,int(46*s)))
ink=(40,50,60); pad=max(8,int(40*s)); maxw=W*0.985-x0-pad
sub={'relief':'Shaded relief and sea floor','grey':'Shaded relief and sea floor','tint':'Elevation and depth','geology':'Bedrock geology on shaded relief'}[V]
subs=[sub,f'{res:.0f} m grid · British National Grid']+([] if V=='tint' else [f'Vertical exaggeration {ex:g}×'])
cred=['LiDAR DTMs: Environment Agency (England); Welsh Government, DataMapWales (Wales); Scottish Government, SEPA, HES, OIC, Scottish Remote Sensing Portal (Scotland). Open Government Licence v3.0.',
      'Where no open LiDAR exists: GEM-15 v1 (experimental), produced by Google, CC BY 4.0 (Batchu et al. 2026).',
      'Sea floor: EMODnet Digital Bathymetry (DTM 2024), mean sea level, CC BY 4.0. Not for navigation.',
      'Coastline, inland water and foreshore: OS Open Zoomstack. Contains OS data © Crown copyright and database right 2026.']
if V=='geology': cred+=['Bedrock geology: BGS Geology 625k (DiGMapGB-625). Contains British Geological Survey materials © UKRI. Open Government Licence v3.0.']
cred+=['Tim Daw · sarsen.org · lidarlens.sarsen.org']
probe=ImageDraw.Draw(im)
def wrap(t,font):
  out=[];cur=''
  for wd in t.split():
    if probe.textlength((cur+' '+wd).strip(),font=font)>maxw: out.append(cur); cur=wd
    else: cur=(cur+' '+wd).strip()
  return out+[cur]
cl=[l for c in cred for l in wrap(c,fC)+['']][:-1]
Lg=json.load(open('geol_legend.json')) if V=='geology' else []; rows=(len(Lg)+1)//2
BL=[(-10,'0'),(-50,'50'),(-100,'100'),(-200,'200 m'),(-1000,'1000 m')]
def layout(d):
  y=y0
  if d: d.text((x0,y),'Great Britain',font=fT,fill=ink)
  y+=fT.size*1.25
  for line in subs:
    if d: d.text((x0,y),line,font=fS,fill=ink)
    y+=fS.size*1.35
  y+=fS.size*0.6; L=100000/res; bh=max(3,int(18*s))
  if d:
    for i in range(4): d.rectangle([x0+i*L/4,y,x0+(i+1)*L/4,y+bh],fill=ink if i%2==0 else (255,255,255),outline=ink,width=max(1,int(3*s)))
    for t,xx in [('0',x0),('50',x0+L/2),('100 km',x0+L)]: d.text((xx,y+bh+fC.size*0.3),t,font=fC,fill=ink,anchor='ma' if t!='100 km' else 'la')
  y+=bh+fC.size*2.2
  if V!='grey':   # depth key
    sw=maxw/len(BL)
    if d: d.text((x0,y),'Sea depth below mean sea level',font=fC,fill=ink)
    y+=fC.size*1.45
    if d:
      for i,(dep,lab) in enumerate(BL):
        c=tuple(int(v) for v in ramp(np.array([dep],np.float32),BATHY)[0]); d.rectangle([x0+i*sw,y,x0+(i+1)*sw,y+fC.size*1.1],fill=c,outline=ink,width=max(1,int(2*s)))
        d.text((x0+i*sw+sw/2,y+fC.size*1.35),lab,font=fC,fill=ink,anchor='ma')
    y+=fC.size*3.2
  if Lg:
    sw=fC.size*1.1; cw=maxw/2
    if d:
      for i,(t,c) in enumerate(Lg):
        xx=x0+(i//rows)*cw; yy=y+(i%rows)*fC.size*1.45
        d.rectangle([xx,yy,xx+sw*1.4,yy+sw],fill=tuple(c),outline=ink,width=max(1,int(2*s))); d.text((xx+sw*1.8,yy-fC.size*0.05),t,font=fC,fill=ink)
    y+=rows*fC.size*1.45+fC.size*1.2
  for line in cl:
    if d: d.text((x0,y),line,font=fC,fill=ink)
    y+=fC.size*1.3
  return y
yend=layout(None)
box=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(box).rectangle([x0-pad,y0-pad,W*0.985,yend+pad*0.6],fill=(246,248,249,225))
im=Image.alpha_composite(im,box); layout(ImageDraw.Draw(im)); im=im.convert('RGB')
out=f'out/gb-{V}-{W}px'
im.save(out+'.png',optimize=True); im.save(out+'.jpg',quality=88); print(out, im.size, round(res))
