"""Adjustable hood and fender mount prototype HF2. CadQuery 2.7, units mm.
Run from any directory; exports STLs, assembly-coordinate STEP and checks.
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

# Local origin is existing hood carrier center. Place at world (130,0,12).
# Four original floor insert positions are world X=100/160, Y=+/-30.
base=rounded(76,88,2.4,9).cut(rounded(60,70,5,6,(0,0,-1)))
base=union(base,box(8,76,2.4,(-30,0,0)),box(8,76,2.4,(30,0,0)),box(64,6,2.4))
base=union(base,rounded(76,88,6,9).cut(rounded(71.2,83.2,8,6.6,(0,0,-1))))
# Raised internal towers. Pocket mouths face the centerline for iron access.
for x in [-18,18]:
    base=base.fuse(box(12,70,2.4,(x,0,0)))
    for sign in [-1,1]:
        base=base.fuse(box(12,10,38,(x,sign*27,0)))
        base=base.cut(cyl(2,6.7,(x,sign*22,32),(0,sign,0)))
# Two U-shaped sliding bars: beam top is local Z4; assembly lift 36..56.
bar=box(10,44,4)
for sign in [-1,1]:
    bar=bar.fuse(box(10,4,28,(0,sign*20,-28)))
    slot=union(cyl(1.7,8,(0,sign*20-4,-24),(0,1,0)),
               cyl(1.7,8,(0,sign*20-4,-4),(0,1,0)),
               box(3.4,8,20,(0,sign*20,-24)))
    bar=bar.cut(slot)
for y in [-12,0,12]:bar=bar.fuse(peg((0,y,4),(0,0,1)))
bar=bar.clean()
# Four side bosses: insert from outside towards center along Y.
for sign in [-1,1]:
    for x in [-22,22]:
        base=base.fuse(box(14,10,18,(x,sign*47,0)))
        base=base.cut(cyl(2,6.7,(x,sign*52,12),(0,-sign,0)))
for x in [-30,30]:
    for y in [-30,30]:base=base.cut(cyl(1.7,25,(x,y,-1)))
base=base.clean()

# Positive-Y riser, mirrored for negative-Y; both keep rearward deck extension.
riser=box(68,4,26,(0,54,0)).fuse(box(100,38,4,(-20,71,26)))
for x in [-8,8]:
    g=cq.Workplane('YZ',origin=(x-3,0,0)).polyline([(56,12),(56,26),(80,26)]).close().extrude(6).val()
    riser=riser.fuse(g)
for x in [-22,22]:
    cut=union(cyl(1.7,8,(x,50,6),(0,1,0)),cyl(1.7,8,(x,50,18),(0,1,0)),box(3.4,8,12,(x,54,6)))
    riser=riser.cut(cut)
    cut=cq.Workplane('XY').center(x,75).slot2D(23.4,3.4,90).extrude(10).translate((0,0,24)).val()
    riser=riser.cut(cut)
riser=riser.clean();riser_mirror=riser.mirror('XZ')

# Pad's local Y=0 is the adjustable bolt centerline. Underside is Z=0.
pad=rounded(100,34,8,4,(-20,0,0))
for x in [-54,-22,14]:
    for y in [-10,10]:pad=pad.fuse(peg((x,y,8),(0,0,1)))
for x in [-22,22]:pad=pad.cut(cyl(2,6.7,(x,0,0),(0,0,1)))
pad=pad.clean()
# Non-loadbearing alignment gauge: existing four-hole pattern and boss footprint.
gauge=rounded(76,88,2,9)
for x in [-22,22]:
    for y in [-47,47]:gauge=gauge.fuse(box(14,10,2,(x,y,0)))
for x in [-30,30]:
    for y in [-30,30]:gauge=gauge.cut(cyl(1.7,4,(x,y,-1)))
gauge=gauge.clean()

shapes={'01_spiked_hood_carrier_HF2':base,'02_fender_riser_positive_Y_HF2':riser,'03_fender_riser_negative_Y_HF2':riser_mirror,'04_fender_pad_print_2_HF2':pad,'00_alignment_gauge_optional_HF2':gauge,'05_raised_spike_bar_print_2_HF2':bar}
manifest=[]
for name,s in shapes.items():
    assert s.isValid() and len(s.Solids())==1,(name,s.isValid(),len(s.Solids()))
    p=s
    if name.startswith('02'):p=p.rotate((0,0,0),(1,0,0),90)
    if name.startswith('03'):p=p.rotate((0,0,0),(1,0,0),-90)
    if name.startswith('05'):p=p.rotate((0,0,0),(0,1,0),90)
    b=p.BoundingBox();p=p.translate((-b.xmin,-b.ymin,-b.zmin));b=p.BoundingBox()
    p.exportStl(str(ROOT/'STL'/f'{name}.stl'),tolerance=.025,angularTolerance=.08,relative=False)
    cq.exporters.export(s,str(ROOT/'CAD'/f'{name}.step'))
    raw=(ROOT/'STL'/f'{name}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0];edges={};deg=0;volume=0
    for i in range(n):
        row=struct.unpack_from('<12fH',raw,84+50*i);v=np.array(row[3:12]).reshape(3,3);keys=[tuple(np.round(a,5)) for a in v]
        deg+=int(np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))<1e-9);volume+=np.dot(v[0],np.cross(v[1],v[2]))/6
        for a,b2 in [(0,1),(1,2),(2,0)]:
            k=tuple(sorted([keys[a],keys[b2]]));edges[k]=edges.get(k,0)+1
    bad=sum(v!=2 for v in edges.values());assert bad==0 and deg==0 and volume>0,(name,bad,deg)
    dims=[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)];assert max(dims)<230
    manifest.append({'file':name+'.stl','quantity':2 if name.startswith(('04','05')) else 1,'valid_single_solid':True,'closed_mesh':True,'dimensions_mm':dims})

# Verify nominal and all adjustment extremes for collisions among printed parts.
# Actual chassis, tires, suspension and pumpkin are NOT covered by this check.
tests=[]
for dz in [-6,0,6]:
    for spread in [65,75,85]:
        items=[('carrier',base),('riser_plus',riser.translate((0,0,dz))),('riser_minus',riser_mirror.translate((0,0,dz))),('pad_plus',pad.translate((0,spread,30+dz))),('pad_minus',pad.translate((0,-spread,30+dz)))]
        items += [('bar_front',bar.translate((18,0,36))),('bar_rear',bar.translate((-18,0,56)))]
        overlap=[]
        for i,(a,sa) in enumerate(items):
            for b,sb in items[i+1:]:
                vol=sa.intersect(sb).Volume()
                if vol>.01:overlap.append([a,b,round(vol,4)])
        assert not overlap,(dz,spread,overlap)
        tests.append({'height_offset_mm':dz,'pad_center_Y_mm':spread,'printed_part_overlaps':overlap})
        if dz==0 and spread==75:
            assembly=cq.Assembly()
            for a,s in items:assembly.add(s,name=a)
            assembly.export(str(ROOT/'CAD'/'Front_Mount_Assembly_HF2.step'))
for lift in [36,46,56]:
    for x in [-18,18]:
        assert base.intersect(bar.translate((x,0,lift))).Volume()<.01
(ROOT/'Guides'/'validation.json').write_text(json.dumps({'parts':manifest,'adjustment_checks':tests,'physical_chassis_clearance_verified':False},indent=2))
print(json.dumps(manifest,indent=2),flush=True)
