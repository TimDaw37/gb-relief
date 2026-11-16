# Maximum extent of the last British-Irish Ice Sheet (BRITICE-CHRONO empirical reconstruction, 31-15 ka) on relief.
# python3 render_lgm.py WIDTH EXAG [notext]
import numpy as np, sys, math, json, geopandas as gpd
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
W=int(sys.argv[1]); ex=float(sys.argv[2]); NOTEXT=len(sys.argv)>3 and sys.argv[3]=='notext'
m=json.load(open('lgm_200m.json')); D=np.load('lgm_200m.npz'); X0,Y0,R0=m['x0'],m['y0'],m['res']
Wd=W; Ht=round(m['h']*W/m['w']); res=R0*m['w']/W
def down(a,mode=Image.BOX): return np.asarray(Image.fromarray(a.astype(np.float32)).resize((Wd,Ht),mode))
Hs=down(D['Hs']); Hv=down(D['Hv']); modern=down(D['modern'])>0.5; pl=down(D['paleoland'])>0.5; wat=down(D['water'])>0.5
iceO=down(np.load('ice_optimum.npy'))
gy,gx=np.gradient(Hs); p=gx/res*ex; q=-gy/res*ex; slope=np.arctan(np.hypot(p,q)); asp=np.arctan2(q,-p); del gy,gx,p,q
def hs(az,alt):
  az=math.radians(360-az+90); alt=math.radians(alt)
  return np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-asp),0,1).astype(np.float32)
sh=(0.5*hs(315,40)+0.2*hs(270,40)+0.2*hs(0,40)+0.1*hs(225,40))[...,None]; del slope,asp
LAND=[(-5,(120,150,110)),(0,(132,165,118)),(50,(160,185,130)),(150,(205,205,150)),(300,(215,190,140)),(500,(190,155,115)),(800,(165,135,115)),(1100,(215,210,205)),(1400,(250,250,250))]
BATHY=[(-2000,(38,66,112)),(-1000,(52,88,140)),(-500,(70,114,166)),(-200,(92,140,186)),(-100,(116,162,200)),(-60,(138,180,212)),(-30,(162,198,222)),(-10,(184,212,228)),(0,(200,222,232))]
def ramp(h,st): return np.stack([np.interp(h,[s[0] for s in st],[s[1][c] for s in st]).astype(np.float32) for c in range(3)],-1)
img=ramp(Hv,LAND)*(0.35+0.85*sh)
exposed=pl&~modern
SAND=np.array([226,214,176],np.float32)
img[exposed]=(ramp(np.maximum(Hv,0),LAND)*0.25+SAND*0.75)[exposed]*(0.55+0.55*sh[exposed])
sea=~pl; img[sea]=(ramp(np.minimum(Hv,0),BATHY)*(0.62+0.45*sh))[sea]
img[modern&wat]=np.array([196,218,230],np.float32)
# ice (BRITICE-CHRONO optimum, envelope of all 1 ka slices): translucent white, relief faintly through
ICE=np.array([244,248,252],np.float32); a=(0.84*iceO)[...,None]
img=img*(1-a)+(ICE*(0.80+0.25*sh))*a
img=np.clip(img,0,255)
# modern coastline (thin) and palaeo-shoreline at 26 ka (thin, sea side)
ce=modern&~ndimage.binary_erosion(modern); img[ce]=img[ce]*0.45+np.array([40,50,60],np.float32)*0.55
pe=sea&ndimage.binary_dilation(pl)&~modern; img[pe]=img[pe]*0.6+np.array([150,120,70],np.float32)*0.4
im=Image.fromarray(img.astype(np.uint8)).convert('RGBA'); del img
d=ImageDraw.Draw(im); s=W/6700
def to_px(x,y): return ((x-X0)/res,(Y0-y)/res)
def lines(kind):
  g=gpd.read_file(f'env_{kind}.gpkg').to_crs(m['proj']).geometry.iloc[0]
  polys=list(g.geoms) if hasattr(g,'geoms') else [g]
  for pg in polys:
    for ring in [pg.exterior]+list(pg.interiors):
      if ring.length<20000: continue
      yield [to_px(x,y) for x,y in ring.coords]
lw=max(1,round(3*s))
for pts in lines('optimum'): d.line(pts,fill=(70,95,120,255),width=lw,joint='curve')
dash=max(4,24*s); gap=max(3,16*s)
for pts in lines('max'):   # dashed outer bound
  acc=0; on=True
  for (x1,y1),(x2,y2) in zip(pts[:-1],pts[1:]):
    L=math.hypot(x2-x1,y2-y1); t=0
    while t<L:
      seg=min((dash if on else gap)-acc,L-t); xa,ya=x1+(x2-x1)*t/L,y1+(y2-y1)*t/L; xb,yb=x1+(x2-x1)*(t+seg)/L,y1+(y2-y1)*(t+seg)/L
      if on: d.line([(xa,ya),(xb,yb)],fill=(70,95,120,255),width=max(1,round(2*s)))
      t+=seg; acc+=seg
      if acc>=(dash if on else gap)-1e-6: acc=0; on=not on
F='/usr/share/fonts/truetype/dejavu/'; ink=(40,50,60)
fT=ImageFont.truetype(F+'DejaVuSerif-Bold.ttf',max(18,int(118*s))); fS=ImageFont.truetype(F+'DejaVuSans.ttf',max(11,int(56*s))); fC=ImageFont.truetype(F+'DejaVuSans.ttf',max(10,int(44*s)))
pad=max(8,int(40*s))
# scale bar (always)
bx,by=to_px(-690000,-655000); L=200000/res; bh=max(3,int(16*s))
d.rectangle([bx-pad*0.5,by-pad*0.5,bx+L+pad*0.5+fC.size*2.5,by+bh+fC.size*1.9],fill=(246,248,249,215))
for i in range(4): d.rectangle([bx+i*L/4,by,bx+(i+1)*L/4,by+bh],fill=ink if i%2==0 else (255,255,255),outline=ink,width=max(1,int(2*s)))
for t,xx in [('0',bx),('100',bx+L/2),('200 km',bx+L)]: d.text((xx,by+bh+fC.size*0.25),t,font=fC,fill=ink,anchor='ma' if t!='200 km' else 'la')
if not NOTEXT:
  x0,y0=to_px(-695000,735000); x1=x0+max(250*s*2.6,W*0.33)
  probe=d; tw=x1-x0-pad
  def wrap(t,font):
    out=[];cur=''
    for wd in t.split():
      if probe.textlength((cur+' '+wd).strip(),font=font)>tw: out.append(cur); cur=wd
      else: cur=(cur+' '+wd).strip()
    return out+[cur]
  T=wrap('Last British–Irish Ice Sheet: maximum extent',fT)
  sub=wrap('Envelope of the BRITICE-CHRONO empirical reconstruction, 31–15 ka (Clark et al. 2022); the margin is diachronous, reached at different times in different sectors.',fS)
  items=[('ice','Ice, most-credible (optimum) limit'),('dash','Outer bound of the maximum limits'),('exp','Land exposed at 26 ka (palaeotopography, BRITICE-CHRONO GIA model)'),('coast','Present coastline')]
  def lay(dr):
    y=y0
    for l in T:
      if dr: dr.text((x0,y),l,font=fT,fill=ink)
      y+=fT.size*1.2
    y+=fS.size*0.3
    for l in sub:
      if dr: dr.text((x0,y),l,font=fS,fill=ink)
      y+=fS.size*1.3
    y+=fS.size*0.6; sw=fC.size*2.2
    for kind,txt in items:
      ls=wrap(txt,fC)
      if dr:
        if kind=='ice': dr.rectangle([x0,y,x0+sw,y+fC.size*1.1],fill=(240,244,248),outline=(70,95,120),width=max(1,round(3*s)))
        elif kind=='dash':
          for k in range(3): dr.line([(x0+k*sw/3,y+fC.size*0.55),(x0+k*sw/3+sw/5,y+fC.size*0.55)],fill=(70,95,120),width=max(1,round(2*s)))
        elif kind=='exp': dr.rectangle([x0,y,x0+sw,y+fC.size*1.1],fill=(212,200,160),outline=ink,width=1)
        else: dr.line([(x0,y+fC.size*0.55),(x0+sw,y+fC.size*0.55)],fill=(40,50,60),width=max(1,round(2*s)))
        for i,l in enumerate(ls): dr.text((x0+sw*1.35,y+i*fC.size*1.25),l,font=fC,fill=ink)
      y+=max(len(ls),1)*fC.size*1.25+fC.size*0.5
    return y
  ye=lay(None); box=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(box).rectangle([x0-pad,y0-pad,x1,ye+pad*0.4],fill=(246,248,249,228))
  im=Image.alpha_composite(im,box); lay(ImageDraw.Draw(im))
  cred=('Ice limits and 26 ka palaeotopography: Clark, C.D., Ely, J.C., Fabel, D. & Bradley, S.L. 2022, BRITICE-CHRONO maps and GIS data, PANGAEA, doi:10.1594/PANGAEA.945729, CC BY 4.0; '
        'Clark et al. 2022, Boreas 51, 699–758, doi:10.1111/bor.12594. Ice shown includes the western margin of the Fennoscandian Ice Sheet. '
        'Relief: LiDAR DTMs of the Environment Agency, Welsh Government and Scottish Government (OGL v3.0); GEM-15, produced by Google (CC BY 4.0); '
        'sea floor EMODnet Digital Bathymetry DTM 2024 (CC BY 4.0); coast OS Open Zoomstack (© Crown copyright 2026), © OpenStreetMap contributors (ODbL), Natural Earth. '
        'Lambert azimuthal equal-area, 55° N 3° W. Map: Tim Daw, sarsen.org, CC BY 4.0.')
  def wrapw(t):
    out=[];cur=''
    for wd in t.split():
      if d.textlength((cur+' '+wd).strip(),font=fC)>W-2*pad: out.append(cur); cur=wd
      else: cur=(cur+' '+wd).strip()
    return out+[cur]
  cl=wrapw(cred); fh=int(pad*1.6+len(cl)*fC.size*1.3)
  cv=Image.new('RGBA',(W,Ht+fh),(246,248,249,255)); cv.paste(im,(0,0)); im=cv; dd=ImageDraw.Draw(im); y=Ht+pad*0.8
  for l in cl: dd.text((pad,y),l,font=fC,fill=ink); y+=fC.size*1.3
im=im.convert('RGB'); out=f'out/bi-ice-sheet-max-extent{"-notext" if NOTEXT else ""}-{W}px'
im.save(out+'.png',optimize=True); im.save(out+'.jpg',quality=90); print(out,im.size,round(res))
