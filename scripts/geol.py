# Rasterise BGS Geology 625k bedrock to the 100 m BNG grid, coloured by period (ICS/CGMW colours), igneous intrusions by composition
import json, glob, numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
Image.MAX_IMAGE_PIXELS=None
X0,Y0,R,W,H=-20000,1230000,100.0,7000,12400
TR=Transformer.from_crs(4326,27700,always_xy=True)
PER={'NEOGENE':'#FFE619','PALAEOGENE':'#FD9A52','CRETACEOUS':'#7FC64E','JURASSIC':'#34B2C9','TRIASSIC':'#812B92','PERMIAN':'#F04028',
     'CARBONIFEROUS':'#67A599','DEVONIAN':'#CB8C37','SILURIAN':'#B3E1B6','ORDOVICIAN':'#009270','CAMBRIAN':'#7FA056'}
ERA={'NEOPROTEROZOIC':'#FEB342','MESOPROTEROZOIC':'#FDB462','PALAEOPROTEROZOIC':'#F74370'}
FELSIC='#B71C1C'; MAFIC='#2F4F3F'; ARCH='#F0047F'; UND='#9E9E9E'
def colour(p):
  if p['rank']=='INTRUSION':
    return FELSIC if p['rcs_d'] in ('FELSIC-ROCK','SYENITIC-ROCK') else MAFIC
  if p['max_period'] in PER: return PER[p['max_period']]
  if p['max_era'] in ERA: return ERA[p['max_era']]
  if p['max_eon']=='ARCHAEAN': return ARCH
  if p['max_eon']=='PROTEROZOIC': return '#F74370'
  return UND
def lighten(h,a=0.15):
  c=np.array([int(h[i:i+2],16) for i in (1,3,5)]); return tuple(int(v) for v in c+(255-c)*a)
F={}
for f in glob.glob('bgs/*.json'):
  for ft in json.load(open(f))['features']: F[ft['properties']['objectid']]=ft
polys=[]
for ft in F.values():
  g=ft['geometry']; col=lighten(colour(ft['properties']))
  for poly in ([g['coordinates']] if g['type']=='Polygon' else g['coordinates']):
    a=np.array(poly[0]); e,n=TR.transform(a[:,0],a[:,1]); x=(e-X0)/R; y=(Y0-n)/R
    area=abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))/2
    polys.append((area,list(zip(x.tolist(),y.tolist())),col,colour(ft['properties'])))
polys.sort(key=lambda t:-t[0])
im=Image.new('RGB',(W,H),(200,200,200)); d=ImageDraw.Draw(im)
HEX=[c for _,c in [('Neogene',PER['NEOGENE']),('Palaeogene',PER['PALAEOGENE']),('Cretaceous',PER['CRETACEOUS']),('Jurassic',PER['JURASSIC']),('Triassic',PER['TRIASSIC']),('Permian',PER['PERMIAN']),('Carboniferous',PER['CARBONIFEROUS']),('Devonian',PER['DEVONIAN']),('Silurian',PER['SILURIAN']),('Ordovician',PER['ORDOVICIAN']),('Cambrian',PER['CAMBRIAN']),('Neoproterozoic',ERA['NEOPROTEROZOIC']),('Palaeoproterozoic',ERA['PALAEOPROTEROZOIC']),('Archaean',ARCH),('Felsic',FELSIC),('Mafic',MAFIC)]]+[UND]
ci=Image.new('L',(W,H),0); dc=ImageDraw.Draw(ci)
for _,pts,col,hx in polys: d.polygon(pts,fill=col); dc.polygon(pts,fill=(HEX.index(hx) if hx in HEX else len(HEX)-1)+1)
c=np.asarray(ci).copy(); bgc=c==0
from scipy import ndimage as _nd
ix=_nd.distance_transform_edt(bgc,return_distances=False,return_indices=True); c=c[ix[0],ix[1]]; np.save('geolidx_100m.npy',c.astype(np.uint8))
a=np.asarray(im).copy(); bg=(a==200).all(-1)
from scipy import ndimage
idx=ndimage.distance_transform_edt(bg,return_distances=False,return_indices=True)
a=a[idx[0],idx[1]]   # land outside the 625k polygons (coastal slivers, reclaimed ground) takes the nearest mapped unit
Image.fromarray(a).save('geol_100m.png')
L=[('Neogene',PER['NEOGENE']),('Palaeogene',PER['PALAEOGENE']),('Cretaceous',PER['CRETACEOUS']),('Jurassic',PER['JURASSIC']),('Triassic',PER['TRIASSIC']),
   ('Permian',PER['PERMIAN']),('Carboniferous',PER['CARBONIFEROUS']),('Devonian',PER['DEVONIAN']),('Silurian',PER['SILURIAN']),('Ordovician',PER['ORDOVICIAN']),
   ('Cambrian',PER['CAMBRIAN']),('Neoproterozoic',ERA['NEOPROTEROZOIC']),('Palaeoproterozoic',ERA['PALAEOPROTEROZOIC']),('Archaean (Lewisian)',ARCH),
   ('Felsic intrusions',FELSIC),('Mafic intrusions',MAFIC)]
json.dump([(t,lighten(c)) for t,c in L],open('geol_legend.json','w')); print(len(polys))
