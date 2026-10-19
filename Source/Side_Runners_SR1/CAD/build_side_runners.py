"""SR1 removable pumpkin side panels. CadQuery 2.7, mm. World X forward, Z floor top=3.
Prototype: reference wheel center X=-106.5,Z=-31, not measured articulation.
"""
from pathlib import Path
import cadquery as cq
import numpy as np
import json,struct
ROOT=Path(__file__).resolve().parent.parent
for d in ['CAD','STL','Guides']:(ROOT/d).mkdir(exist_ok=True)
def box(x,y,z,c=(0,0,0)):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(c).val()
def cyl(r,h,p=(0,0,0),d=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*d))
def union(*ss):
 s=ss[0]
 for a in ss[1:]:s=s.fuse(a)
 return s.clean()
def peg(p,d=(0,1,0)):
 v=cq.Vector(*d);o=cq.Vector(*p)
 def cone(a,b,z,h):return cq.Solid.makeCone(a,b,h,o+v*z,v)
 return union(cone(2.5,1.5,-.3,1.1),cyl(1.5,1.8,(o+v*.7).toTuple(),d),cone(1.8,1.5,1.7,.8),cone(1.5,.05,2.5,3.5))
def vslot(x,y,z,length=12):
 return union(cyl(1.7,12,(x,y-6,z-length/2),(0,1,0)),cyl(1.7,12,(x,y-6,z+length/2),(0,1,0)),box(3.4,12,length,(x,y,z-length/2)))
# Cab clamp: 7 mm floor captured between Z=-4 and +3. Upper jaw begins at Y63.
# Clamp shank remains outside floor Y73; tighten lightly, no drilling.
upper=union(box(10,25,4,(0,75.5,3)),box(10,10,7,(0,83,-4)),box(10,10,8,(0,83,-12)))
upper=upper.cut(cyl(1.7,25,(0,83,-14)))
# Horizontal panel insert faces outward at Y88, Z0.
upper=upper.cut(cyl(2,6.7,(0,88,0),(0,-1,0))).clean()
# Offset ear separates the vertical clamp fastener from the horizontal panel insert.
upper=union(upper,box(10,10,10.4,(10,83,-3.4)))
upper=upper.cut(cyl(1.7,16,(10,83,-5))).clean()
# Old center vertical hole would intersect side insert: fill then recut only side pocket.
upper=union(upper,cyl(2,19,(0,83,-12))).cut(cyl(2,6.7,(0,88,0),(0,-1,0))).clean()
# Lower jaw lies under floor; extends to ear screw. Eight-mm insert boss, mouth upward.
lower=union(box(10,15,8,(0,70.5,-12)),box(20,4,8,(5,76,-12)),box(10,10,8,(10,83,-12)))
lower=lower.cut(cyl(2,6.7,(10,83,-4),(0,0,-1))).clean()
# Upper outside body and lower jaw must not overlap. Lower central part ends at Y78.
lower=lower.cut(box(10.2,10.1,8.2,(0,83,-12.1))).clean()
# Bed hangers: plate Z19..23 replaces 4mm of the existing 20mm spacers.
def hanger(offset):
 a=box(12,64,4,(0,56,19))
 if offset:a=a.fuse(box(abs(offset)+12,12,4,(offset/2,82,19)))
 a=a.fuse(box(12,10,14,(offset,83,13)))
 a=a.cut(cyl(1.7,8,(0,30,17)))
 a=a.cut(cyl(2,6.7,(offset,88,21),(0,-1,0)))
 return a.clean()
rear_hanger=hanger(0);front_hanger=hanger(-12)
bedspacer=cyl(6,16).cut(cyl(1.7,18,(0,0,-1))).clean()
# Cab panel, inner face Y88. Four mm backing, 10mm supporting ledge.
cab=union(box(120,4,34,(5,90,-25)),box(120,10,3,(5,97,-25)))
for x in [-40,-10,20,50]:
 for z in [-15,1]:cab=cab.fuse(peg((x,92,z)))
for x in [-48,38]:cab=cab.cut(vslot(x,90,0,10))
cab=cab.clean()
# Rear panel continuous over arch; cut an R44 wheel envelope out of its lower edge.
rear=box(116,4,55,(-114,90,-25)).cut(cyl(44,20,(-106.5,82,-31),(0,1,0)))
# Small ledges beneath ends and two shelf tabs above arch, to carry flesh.
for x,z,w in [(-163,-25,18),(-64,-25,16),(-128,18,12),(-85,18,12)]:
 rear=rear.fuse(box(w,10,3,(x,97,z)))
for x,z in [(-163,-12),(-163,15),(-143,22),(-112,23),(-81,23),(-64,-12)]:
 rear=rear.fuse(peg((x,92,z)))
for x in [-150,-60]:rear=rear.cut(vslot(x,90,21,10))
rear=rear.cut(cyl(44,25,(-106.5,82,-31),(0,1,0))).clean()
# Stand-off washers: move panels 5 or 10mm outward without loose nuts.
def spacer(h):return cyl(5,h).cut(cyl(1.7,h+2,(0,0,-1))).clean()
parts={};instances=[]
def add(name,s,qty=1,rotate=None):
 assert s.isValid() and len(s.Solids())==1,(name,len(s.Solids()))
 p=s if rotate is None else s.rotate((0,0,0),rotate[0],rotate[1])
 b=p.BoundingBox();p=p.translate((-b.xmin,-b.ymin,-b.zmin))
 p.exportStl(str(ROOT/'STL'/f'{name}.stl'),tolerance=.03,angularTolerance=.08,relative=False)
 cq.exporters.export(s,str(ROOT/'CAD'/f'{name}.step'))
 raw=(ROOT/'STL'/f'{name}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0];edges={};deg=0
 for i in range(n):
  v=np.array(struct.unpack_from('<12fH',raw,84+50*i)[3:12]).reshape(3,3);k=[tuple(np.round(a,5)) for a in v]
  deg+=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))<1e-9
  for a,b in [(0,1),(1,2),(2,0)]:
   e=tuple(sorted([k[a],k[b]]));edges[e]=edges.get(e,0)+1
 assert not deg and all(v==2 for v in edges.values()),name
 b=p.BoundingBox()
 parts[name]={'quantity':qty,'dimensions_mm':[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)],'valid_solid':True,'closed_mesh':True}
for side,sign in [('left',1),('right',-1)]:
 def mir(s):return s if sign==1 else s.mirror('XZ')
 add('01_cab_skirt_'+side,cab if sign==1 else mir(cab),rotate=((1,0,0),90*sign))
 add('02_rear_arch_'+side,mir(rear),rotate=((1,0,0),90*sign))
 add('03_cab_upper_clamp_'+side,mir(upper),2,((0,1,0),90))
 add('04_cab_lower_jaw_'+side,mir(lower),2)
 add('05_rear_bed_hanger_'+side,mir(rear_hanger),rotate=((0,1,0),90))
 add('06_forward_bed_hanger_'+side,mir(front_hanger),rotate=((0,1,0),90))
 instances += [('cab_'+side,mir(cab)),('arch_'+side,mir(rear))]
 for x in [-48,38]:
  instances += [('upper_'+side+str(x),mir(upper).translate((x,0,0))),('lower_'+side+str(x),mir(lower).translate((x,0,0)))]
 instances += [('rear_hanger_'+side,mir(rear_hanger).translate((-150,0,0))),('front_hanger_'+side,mir(front_hanger).translate((-48,0,0)))]
 for x in [-150,-48]:instances.append(('bed_spacer_'+side+str(x),bedspacer.translate((x,sign*30,3))))
add('07_bed_spacer_16mm_print_4',bedspacer,4)
add('08_offset_spacer_5mm_optional',spacer(5),8)
add('09_offset_spacer_10mm_optional',spacer(10),8)
# Check panel adjustment positions against the fixed brackets.
adjustment_checks=0
fixed=[(n,s) for n,s in instances if not n.startswith(('cab_','arch_'))]
for n,s in instances:
 if not n.startswith(('cab_','arch_')):continue
 sign=1 if 'left' in n else -1
 for dz in [-5,0,5]:
  for off in [0,5,10]:
   moved=s.translate((0,sign*off,dz))
   for other,solid in fixed:
    assert moved.intersect(solid).Volume()<.02,(n,dz,off,other)
   adjustment_checks+=1
# Check printed parts at nominal position; mating faces may touch, never overlap.
overlaps=[]
for i,(a,sa) in enumerate(instances):
 for b,sb in instances[i+1:]:
  if sa.BoundingBox().xmax<sb.BoundingBox().xmin:continue
  vol=sa.intersect(sb).Volume()
  if vol>.02:overlaps.append([a,b,round(vol,3)])
assert not overlaps,overlaps
assy=cq.Assembly()
for n,s in instances:assy.add(s,name=n)
assy.export(str(ROOT/'CAD'/'Side_Runners_Assembly_SR1.step'))
(ROOT/'Guides'/'validation.json').write_text(json.dumps({'parts':parts,'nominal_overlaps':overlaps,'panel_adjustment_positions_checked':adjustment_checks,'physical_fit_verified':False,'rear_wheel_reference_only':{'x':-106.5,'z':-31,'cutout_radius':44}},indent=2))
print(json.dumps(parts,indent=2))
