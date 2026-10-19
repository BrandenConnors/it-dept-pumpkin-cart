"""Experimental pumpkin peg upgrade R2. CadQuery 2.7, units mm.
Run from any directory; exports three STLs, assembly-coordinate STEP and checks.
Designed for thicker fresh pumpkin panels (start around 8-10 mm); physical grip untested.
"""
from pathlib import Path
import math, json, struct
import cadquery as cq
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
for f in ['STL','Guides']: (ROOT/f).mkdir(parents=True,exist_ok=True)
def box(x,y,z,c=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(c).val()
def rounded(x,y,z,r=2,c=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).edges('|Z').fillet(r).translate(c).val()
def cyl(r,h,p=(0,0,0),d=(0,0,1)):
    return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*d))
def union(*ss):
    a=ss[0]
    for b in ss[1:]: a=a.fuse(b)
    return a.clean()
def peg(p,d):
    """6 mm exposed length, 3 mm shaft, 3.6 mm barb, 5 mm root.
    Root overlaps parent by .3 mm; long taper ends at a 0.1 mm tip diameter.
    """
    v=cq.Vector(*d); o=cq.Vector(*p)
    def cone(r1,r2,z,h):return cq.Solid.makeCone(r1,r2,h,o+v*z,v)
    return union(cone(2.5,1.5,-.3,1.1),cyl(1.5,1.8,tuple((o+v*.7).toTuple()),d),
                 cone(1.8,1.5,1.7,.8),cone(1.5,.05,2.5,3.5))
# Existing v06 bed: four mounting holes, ledges and tie/plaque holes retained.
bed=rounded(132,134,50,5).cut(rounded(127.2,129.2,52,2.6,(0,0,2.4)))
bed=cq.Workplane(obj=bed).edges('>Z').fillet(.6).val()
for y in [-48,-16,16,48]:bed=bed.fuse(rounded(112,1.8,.8,.8,(0,y,2.4)))
bed=union(bed,rounded(132,7.2,2.4,2,(0,-70.4,0)),rounded(132,7.2,2.4,2,(0,70.4,0)),rounded(7.2,148,2.4,2,(-69.4,0,0)))
for x in [-51,51]:
    for y in [-30,30]:bed=bed.cut(cyl(1.7,80,(x,y,-10)))
for x in [-44,0,44]:
    for y in [-66,66]:
        for z in [10,28]:bed=bed.cut(cyl(1.6,10,(x,y-5,z),(0,1,0)))
for y in [-44,0,44]:
    for z in [10,28]:bed=bed.cut(cyl(1.6,10,(-70,y,z),(1,0,0)))
for x in [-37.5,37.5]:
    for y in [-66,66]:
        for z in [18,24]:bed=bed.cut(cyl(1.4,10,(x,y-5,z),(0,1,0)))
bed_points=[]
for x in [-48,-16,16,48]:
    for sign in [-1,1]:
        for z in [12,28,43]:
            p=(x,sign*67,z);d=(0,sign,0);bed=bed.fuse(peg(p,d));bed_points.append({'position':p,'direction':d})
for y in [-48,-16,16,48]:
    for z in [12,28,43]:
        p=(-66,y,z);d=(-1,0,0);bed=bed.fuse(peg(p,d));bed_points.append({'position':p,'direction':d})
bed=bed.clean()
# Existing crowned roof and clevis/insert interfaces retained.
outer=cyl(700,170,(-85,0,-690),(1,0,0));inner=cyl(698.4,172,(-86,0,-690),(1,0,0))
roof=outer.cut(inner).intersect(rounded(158,168,12,12))
rim=rounded(158,168,12,12).cut(rounded(154.8,164.8,14,10.4,(0,0,-1))).intersect(outer)
roof=union(roof,rim,box(154,1.6,10).intersect(outer),box(1.6,164,10).intersect(outer))
for x in [-59,59]:
    for y in [-65,65]:
        roof=roof.fuse(box(10,10,10,(x,y,0)).intersect(outer)).cut(box(4.4,4.4,4.4,(x,y,-.01)))
        sign=1 if y>0 else -1
        roof=union(roof,box(10,2,9.2,(x,y-sign*3.2,-9)),box(10,8,9.2,(x,y+sign*6.2,-9)))
        roof=roof.cut(cyl(1.7,24,(x,y-12,-4),(0,1,0))).cut(cyl(2,6.7,(x,y+sign*10.2,-4),(0,-sign,0)))
roof_points=[]
for x in [-54,-18,18,54]:
    for y in [-52,8,52]:
        z=math.sqrt(700**2-y**2)-690
        # Internal pads give the 1.6 mm crown local support beneath each root.
        roof=roof.fuse(cyl(3.5,2,(x,y,z-2.5))).clean().fuse(peg((x,y,z),(0,0,1))).clean()
        roof_points.append({'position':(x,y,z),'direction':(0,0,1)})
roof=roof.clean()
# Upright pegs test grip, horizontal row tests the bed's support removal.
test=rounded(56,18,3,2)
for x in [-18,0,18]:test=test.fuse(peg((x,0,3),(0,0,1)))
for x in [-18,0,18]:test=test.fuse(peg((x,-9,3),(0,-1,0)))
test=test.clean()
shapes={'04_bed_50mm_sharp_6mm_R2':bed,'11_roof_sharp_6mm_R2':roof,'00_sharp_peg_test_strip_R2':test}
checks=[]
for name,s in shapes.items():
    assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
    b=s.BoundingBox();p=s.translate((-b.xmin,-b.ymin,-b.zmin));b=p.BoundingBox()
    p.exportStl(str(ROOT/'STL'/f'{name}.stl'),tolerance=.025,angularTolerance=.08,relative=False)
    cq.exporters.export(s,str(ROOT/'CAD'/f'{name}.step'))
    raw=(ROOT/'STL'/f'{name}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0];edges={};deg=0;volume=0
    for i in range(n):
        row=struct.unpack_from('<12fH',raw,84+50*i);v=np.array(row[3:12]).reshape(3,3);keys=[tuple(np.round(a,5)) for a in v]
        deg+=int(np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))<1e-9);volume+=np.dot(v[0],np.cross(v[1],v[2]))/6
        for a,c in [(0,1),(1,2),(2,0)]:
            k=tuple(sorted([keys[a],keys[c]]));edges[k]=edges.get(k,0)+1
    bad=sum(v!=2 for v in edges.values());assert bad==0 and deg==0 and volume>0,(name,bad,deg,volume)
    dims=[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)];assert max(dims)<230
    checks.append({'part':name,'valid_single_solid':True,'closed_mesh':True,'degenerate_triangles':deg,'dimensions_mm':dims,'physical_grip_tested':False})
(ROOT/'Guides'/'validation.json').write_text(json.dumps(checks,indent=2))
(ROOT/'Guides'/'peg_positions.json').write_text(json.dumps({'roof':roof_points,'bed':bed_points},indent=2))
print(json.dumps(checks,indent=2),flush=True)
