"""Miniature IT cargo for the v0.4 pumpkin cart. Millimeters; decorative only.
CadQuery 2.7, numpy, Pillow. Run from any folder. Original stylized designs, not vendor replicas.
"""
from pathlib import Path
import csv,json,struct,math
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
for d in ['STL','CAD','Guides']:(ROOT/d).mkdir(parents=True,exist_ok=True)
parts={};assemblies={}
def box(x,y,z,c=(0,0,0)):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(c).val()
def rounded(x,y,z,r=1,c=(0,0,0)):return cq.Workplane(obj=box(x,y,z)).edges('|Z').fillet(r).val().translate(c)
def cyl(r,h,p=(0,0,0),d=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*d))
def union(*xs):
 s=xs[0]
 for x in xs[1:]:s=s.fuse(x)
 return s.clean()
def record(name,shape,color,note):
 shape=shape.clean();assert shape.isValid() and len(shape.Solids())==1,name
 b=shape.BoundingBox();out=shape.translate((-b.xmin,-b.ymin,-b.zmin))
 out.exportStl(str(ROOT/'STL'/f'{name}.stl'),tolerance=.025,angularTolerance=.12,relative=False)
 # Remove zero-area pole facets sometimes emitted for spherical CAD faces.
 stl=ROOT/'STL'/f'{name}.stl';raw=stl.read_bytes();count=struct.unpack_from('<I',raw,80)[0];keep=[]
 for i in range(count):
  facet=raw[84+i*50:84+(i+1)*50];row=struct.unpack('<12fH',facet);v=np.array(row[3:12]).reshape(3,3)
  if np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))>=1e-9:keep.append(facet)
 if len(keep)!=count:stl.write_bytes(raw[:80]+struct.pack('<I',len(keep))+b''.join(keep))
 parts[name]={'shape':shape,'color':color,'note':note,'solid_PLA_g':shape.Volume()/1000*1.24}
 return shape
BLACK='#3c5158';WHITE='#e3e6df';BLUE='#327991';RED='#b95833';GRAY='#849398'
def switch(w,dep,cols,rows,prefix):
 height=8.8 if rows==2 else 7.2
 body=rounded(w,dep,height,1.6).cut(rounded(w-3.2,dep-3.2,height+1,.5,(0,0,1.2)))
 # Blind port recesses leave about 1.0 mm of front wall.
 pitch=3.9 if cols==12 else 3.25;portw=2.8 if cols==12 else 2.3
 for row in range(rows):
  z=2.3+row*3.2
  for i in range(cols):
   x=(i-(cols-1)/2)*pitch
   body=body.cut(box(portw,.75,2.1,(x,-dep/2+.25,z)))
   # Small stepped top notch suggests an RJ45 jack, still only a shallow recess.
   body=body.cut(box(portw*.43,.75,.5,(x,-dep/2+.25,z+2.1)))
 if rows==2:
  for x in [-w/2-1.6,w/2+1.6]:
   ear=box(4,3.6,height,(x,-dep/2+1.8,0))
   ear=ear.cut(cyl(.9,5,(x,-dep/2-.5,height/2),(0,1,0)))
   body=body.fuse(ear)
 body=record(prefix+'_body',body,BLACK,'Open top UP; 0.16 mm layers; no supports expected. Retain lid with two narrow removable bands after painting port recesses.')
 lid=rounded(w,dep,1.2,1.6)
 for x in np.linspace(-w/2+6,w/2-6,9 if rows==2 else 5):
  lid=lid.cut(rounded(.8,7,.5,.35,(float(x),2,.85)))
 lid=record(prefix+'_lid',lid,GRAY,'Flat plain face DOWN; engraved vents UP. Center flat lid on rim and retain with two narrow bands; no snap fit.')
 return [(body,(0,0,0),BLACK),(lid,(0,0,height),GRAY)]
assemblies['24-port switch']=switch(56,26,12,2,'01_switch_24port')
assemblies['8-port switch']=switch(32,22,8,1,'02_switch_8port')
# Camera body with hollow underside, shallow lens face and sun hood.
cam=rounded(24,14,13.2,2.5)
cam=cq.Workplane(obj=cam).edges('>Z').fillet(.8).val()
cam=cam.cut(rounded(20,10,12,1,(0,0,-1)))
cam=cam.fuse(cyl(5.6,1.5,(11.7,0,7.2),(1,0,0)))
cam=cam.cut(cyl(4.1,1.6,(12.6,0,7.2),(1,0,0)))
cam=union(cam,rounded(27,16,1.2,2,(.5,0,13)))
cam=record('03_bullet_camera',cam,WHITE,'Open underside DOWN; 0.16 mm layers. Inspect 10 mm inner roof bridge; use internal supports if bridging is poor. Paint recessed lens black.')
assemblies['Bullet camera']=[(cam,(0,0,0),WHITE)]
# Dome camera: thick enough curved skin around a shallow lens recess.
dome=union(cyl(8,2.2),cq.Solid.makeSphere(6.8,cq.Vector(0,0,2.2)).intersect(box(16,16,10,(0,0,2.2))))
dome=dome.cut(cq.Solid.makeSphere(4.4,cq.Vector(0,0,2.2)))
dome=dome.cut(cyl(4.2,3,(0,0,-.5)))
dome=dome.cut(cyl(1.6,3,(5.45,0,4.3),(1,0,0)))
dome=record('04_dome_camera',dome,WHITE,'Base ring DOWN; 0.16 mm layers. Hollow underside; inspect top bridge. Paint upper dome smoky gray and lens black.')
assemblies['Dome camera']=[(dome,(0,0,0),WHITE)]
# Toolbox: open-top light shell and lid with integrated handle.
tool=rounded(36,22,16,2).cut(rounded(33.2,19.2,17,.7,(0,0,1.2)))
for x in [-10,10]:tool=tool.fuse(rounded(3,1.8,4,.5,(x,-10.9,11)))
tool=record('05_toolbox_body',tool,RED,'Open top UP; no supports expected. Retain lid with two narrow bands. Paint latches silver.')
lid=rounded(36,22,1.6,2)
handle=union(box(14,3,1.6,(0,0,4.6)),box(2.4,3,4,( -5.8,0,1.4)),box(2.4,3,4,(5.8,0,1.4)))
handle=cq.Workplane(obj=handle).edges('|Y').fillet(.5).val()
lid=union(lid,handle)
lid=record('05_toolbox_lid',lid,RED,'Flat underside DOWN; handle UP. The handle bridges about 9 mm. Inspect bridge; treat handle as decorative, not a lifting point.')
assemblies['Toolbox']=[(tool,(0,0,0),RED),(lid,(0,0,16),RED)]
# Flat connected cable coil: concentric raised strands carried by a thin annular backing.
coil=cyl(16,.8).cut(cyl(7.2,2,(0,0,-.5)))
for rad in [8.3,10.4,12.5,14.6]:
 ring=cq.Workplane('XY').circle(rad+.85).circle(rad-.85).extrude(1.6).translate((0,0,.6)).val()
 ring=cq.Workplane(obj=ring).edges('>Z').fillet(.55).val();coil=coil.fuse(ring)
# Retaining straps tie the four strands together; all features form one solid.
for angle in [25,205]:coil=coil.fuse(box(10,2.5,.8,(11.4,0,1.9)).rotate((0,0,0),(0,0,1),angle))
coil=record('06_cable_coil',coil.clean(),BLUE,'Flat backing DOWN; 0.16 mm layers, no supports expected. Paint retaining straps black. Decorative rigid coil, not flexible cable.')
assemblies['Cable coil']=[(coil,(0,0,0),BLUE)]
# Optional PC tower gives the cargo some height. Separate lid avoids a wide internal bridge.
tower=rounded(22,25,40,2).cut(rounded(19.2,22.2,41,.7,(0,0,1.2)))
# Front panel at -Y; shallow details preserve the wall.
tower=tower.cut(box(15,.8,2, (0,-12.25,30)))
tower=tower.cut(cyl(1.2,.8,(5,-12.7,25),(0,1,0)))
for x in [-6,-3,0,3,6]:tower=tower.cut(box(.9,.8,12,(x,-12.25,6)))
tower=record('07_pc_tower_body',tower,BLACK,'Open top UP; no supports expected. Print only if desired after the load check. Paint front slots / power button.')
top=record('07_pc_tower_lid',rounded(22,25,1.2,2),GRAY,'Flat face DOWN. Center on body rim and retain with two narrow bands; no snap fit.')
assemblies['PC tower']=[(tower,(0,0,0),BLACK),(top,(0,0,40),GRAY)]
# Layout within the measured CAD bed interior, not a measured RC payload.
layout={'24-port switch':(-27,32),'8-port switch':(-33,0),'Bullet camera':(4,-24),'Dome camera':(0,5),'Toolbox':(29,34),'Cable coil':(-32,-38),'PC tower':(33,-17)}
asm=cq.Assembly(name='IT_cargo_v01');placed=[]
for name,items in assemblies.items():
 dx,dy=layout[name]
 for i,(sh,local,col) in enumerate(items):
  placed_shape=sh.translate((local[0]+dx,local[1]+dy,local[2]))
  asm.add(placed_shape,name=name.replace(' ','_').replace('-','_')+'_'+str(i),color=cq.Color(col))
  placed.append((name,placed_shape))
asm.export(str(ROOT/'CAD'/'Cargo_Layout.step'))
# Validate printable meshes; one manifold solid per STL, actual mesh bounds.
manifest=[];checks=[]
for name,d in parts.items():
 stl=ROOT/'STL'/f'{name}.stl';b=stl.read_bytes();count=struct.unpack_from('<I',b,80)[0];facets=[]
 for ii in range(count):
  facet=b[84+ii*50:84+(ii+1)*50];vv=np.array(struct.unpack('<12fH',facet)[3:12]).reshape(3,3)
  if np.linalg.norm(np.cross(vv[1]-vv[0],vv[2]-vv[0]))>=1e-9:facets.append(facet)
 if len(facets)!=count:
  b=b[:80]+struct.pack('<I',len(facets))+b''.join(facets);stl.write_bytes(b)
 n=struct.unpack_from('<I',b,80)[0];edge={};deg=0;vol=0;coords=[]
 for i in range(n):
  row=struct.unpack_from('<12fH',b,84+50*i);v=np.array(row[3:12]).reshape(3,3);coords.extend(v);k=[tuple(np.round(p,5)) for p in v]
  if np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))<1e-9:deg+=1
  vol+=np.dot(v[0],np.cross(v[1],v[2]))/6
  for a,c in [(0,1),(1,2),(2,0)]:e=tuple(sorted([k[a],k[c]]));edge[e]=edge.get(e,0)+1
 coords=np.array(coords);size=coords.max(0)-coords.min(0);bad=sum(x!=2 for x in edge.values());assert bad==0 and deg==0 and vol>0,(name,bad,deg)
 assert max(size)<100 and abs(coords[:,2].min())<.01,(name,size,coords[:,2].min())
 checks.append({'file':name+'.stl','single_valid_solid':True,'nonmanifold_edges':bad,'degenerate_triangles':deg,'positive_volume':True,'triangles':n,'print_size_mm':[round(float(x),2) for x in size]})
 manifest.append({'file':name+'.stl','quantity':1,'size_mm':[round(float(x),2) for x in size],'solid_PLA_g':round(d['solid_PLA_g'],2),'note':d['note']})
# All pieces inside 127.2 x129.2 rectangular envelope, with >3 mm corner margins.
overlap=[]
for i,(na,sa) in enumerate(placed):
 b=sa.BoundingBox();assert b.xmin>-63.6 and b.xmax<63.6 and b.ymin>-64.6 and b.ymax<64.6,na
 for nb,sb in placed[i+1:]:
  if na==nb:continue
  bb=sb.BoundingBox()
  if any(min(getattr(b,k+'max'),getattr(bb,k+'max'))-max(getattr(b,k+'min'),getattr(bb,k+'min'))<=.001 for k in ['x','y','z']):continue
  v=sa.intersect(sb).Volume()
  if v>.01:overlap.append([na,nb,round(v,3)])
assert not overlap,overlap
(ROOT/'Guides'/'mesh_checks.json').write_text(json.dumps(checks,indent=2))
(ROOT/'Guides'/'parts_manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'Guides'/'layout.json').write_text(json.dumps({'units':'mm','bed_interior':[127.2,129.2],'origin':'bed center; +X toward bench, -X rear','item_centers':layout,'overlaps':overlap},indent=2))
with (ROOT/'Guides'/'parts_list.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['STL','Quantity','X mm','Y mm','Z mm','Solid PLA g','Print / assembly notes'])
 for d in manifest:w.writerow([d['file'],1,*d['size_mm'],d['solid_PLA_g'],d['note']])
print('Validated',len(parts),'STLs,',len(assemblies),'assembled objects; nominal solid-PLA mass',round(sum(x['solid_PLA_g'] for x in parts.values()),1),'g',flush=True)
# Rendering is provided by a local exact-geometry renderer, not image generation.
if __name__=='__main__':
 from render_cargo import make_previews
 make_previews(ROOT,assemblies,layout)
