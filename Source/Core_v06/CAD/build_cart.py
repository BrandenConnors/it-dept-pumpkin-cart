"""IT DEPT pumpkin cart v0.6 — parametric CadQuery 2.7 model, units mm.
Prototype only. Photo-derived mount dimensions are approximate; verify templates on the truck.
Run: python CAD/build_cart.py from the package root. Requires cadquery, numpy, matplotlib.
All STL exports are individually oriented and placed on Z=0. No pumpkin is printed.
"""
from pathlib import Path
import json, csv, math, struct
import cadquery as cq
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
for folder in ['STL','CAD','Guides']: (ROOT/folder).mkdir(exist_ok=True)
LENGTH=350.; WIDTH=146.; WHEELBASE=213.
HOLE=3.4; PEG=4.; SOCKET=4.4
# Floor mounting datum remains Z=3 to preserve all upper-part interfaces.
WEB_BOTTOM=-4.; RAIL_BOTTOM=-8.; SPLICE_THICKNESS=8.
FRONT_CHASSIS_SPACING=36.; REAR_CHASSIS_SPACING=86.
ADAPTER_THICKNESS=8.; MOUNT_SHIM_HEIGHT=12.
MOUNT_X=150.; FLOOR_SLOT_LENGTH=26.
INSERT_D=4.0; INSERT_L=5.7; INSERT_DEPTH=INSERT_L+1.0
REAR_BUMPER_SLOT_X=-164.; REAR_BUMPER_SLOT_Y=45.; REAR_BUMPER_SLOT_LENGTH=20.
parts={}; instances=[]
COLORS={'black':'#30383c','tan':'#c9b594','cream':'#eee2c6','orange':'#e88022','metal':'#8d979c'}

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
def drill(s,xy,r=HOLE/2,z=-10,h=80):
    for x,y in xy: s=s.cut(cyl(r,h,(x,y,z)))
    return s.clean()
def slot(x,y,length,width,z=-15,height=40):
    return cq.Workplane('XY').center(x,y).slot2D(length,width).extrude(height).translate((0,0,z)).val()
def insert_pocket(s,p,d=(0,0,-1),diameter=INSERT_D,depth=INSERT_DEPTH):
    # Pocket starts at the installation face. Original screw clearance stays open.
    return s.cut(cyl(diameter/2,depth,p,d)).clean()
def record(name,s,color='black',qty=1,rotation=None,note='Prototype; verify fit before final printing'):
    assert s.isValid(),name
    assert len(s.Solids())==1,(name,'multiple solids',len(s.Solids()))
    p=s
    if rotation: p=p.rotate((0,0,0),rotation[0],rotation[1])
    bb=p.BoundingBox(); p=p.translate((-bb.xmin,-bb.ymin,-bb.zmin))
    if name=='11_roof':
        # Absolute deflection avoids coarse facets on the large-radius crown.
        p.exportStl(str(ROOT/'STL'/f'{name}.stl'),tolerance=0.025,angularTolerance=0.04,relative=False)
    else:
        cq.exporters.export(p,str(ROOT/'STL'/f'{name}.stl'),tolerance=0.08,angularTolerance=0.15)
    bb=p.BoundingBox()
    parts[name]={'shape':s,'print_shape':p,'color':COLORS[color],'qty':qty,'note':note,
        'size':[round(bb.xlen,2),round(bb.ylen,2),round(bb.zlen,2)],'volume_mm3':s.Volume()}
    return s
def place(name,xyz=(0,0,0),rotation=None):
    s=parts[name]['shape']
    if rotation: s=s.rotate((0,0,0),rotation[0],rotation[1])
    s=s.translate(xyz)
    instances.append((name,s,parts[name]['color']))
    return s

# Floor structure: solid cab floor with narrow fore/aft backbone. Wheel areas left open.
floor=union(box(LENGTH,80,7,(0,0,WEB_BOTTOM)),box(122,WIDTH,7,(7,0,WEB_BOTTOM)),box(22,126,7,(-160,0,WEB_BOTTOM)),box(22,104,7,(160,0,WEB_BOTTOM)))
# Reduce material under bed and hood, retaining transverse mounting rails.
for x in [-126,-91,116,139]: floor=floor.cut(rounded(20,52,12,3,(x,0,-6)))
# Continuous deep side rails connect end supports to component mounts.
for y in [-32,32]:
    floor=floor.fuse(box(LENGTH,12,4,(0,y,RAIL_BOTTOM)))
# Solid material surrounds adjustable floor-to-adapter slots.
for x in [-MOUNT_X,MOUNT_X]:
    for y in [-18,18]:
        floor=floor.fuse(rounded(40,12,7,3,(x,y,WEB_BOTTOM)))
floorholes=[(x,y) for x in [-10,10] for y in [-65,65,-32,32]]
floorholes += [(x,y) for x in [-150,-48] for y in [-30,30]]
floorholes += [(x,y) for x in [100,160] for y in [-30,30]]
floorholes += [(x,y) for x in [-20,10] for y in [-45,45]]
floorholes += [(41,y) for y in [-45,45]]
floorholes += [(x,y) for x in [-60,60] for y in [-30,30]]
# New mechanical joints: bumper holes and two bolts per roof-post foot.
bumperholes=[(171,y) for y in [-30,30]]
postholes=[(x,y) for x in [-36,-20,54,70] for y in [-65,65]]
for x in [-28,62]:
    for y in [-65,65]:floor=floor.fuse(rounded(26,14,3,2,(x,y,0)))
for x,y in bumperholes:floor=floor.fuse(cyl(4,1.1,(x,y,1.9)))
# One-millimeter local pads bring all attached structures to the Z=3 mount datum.
for x,y in floorholes: floor=floor.fuse(cyl(5.5,1.1,(x,y,1.9)))
for x in [-28,62]:
    for y in [-65,65]:floor=floor.fuse(box(14,14,1.1,(x,y,1.9)))
for y in [-45,45]:
    floor=floor.fuse(box(44,8,1.1,(-5,y,1.9)))
    floor=floor.fuse(box(18,14,1.1,(43,y,1.9)))
# Extra underside material supports 6.7 mm insert pockets without changing top datum.
componentholes=[(x,y) for x in [-150,-48,100,160] for y in [-30,30]]
componentholes += [(x,y) for x in [-20,10] for y in [-45,45]]
componentholes += [(41,y) for y in [-45,45]] + postholes + bumperholes
for x,y in componentholes: floor=floor.fuse(cyl(5.5,2,(x,y,-6)))
# Broad outer splice seats match the new underside insert bosses.
for y in [-65,65]:floor=floor.fuse(rounded(40,16,2,2,(0,y,-6)))
# Rear bumper slots: photo-derived travel, independently clamped insert blocks below.
for y in [-REAR_BUMPER_SLOT_Y,REAR_BUMPER_SLOT_Y]:
    floor=floor.fuse(rounded(28,12,11,3,(REAR_BUMPER_SLOT_X,y,-8)))
# Six low side eyelets. 5 x 2.6 mm vertical slots accept typical narrow zip ties.
wireloops=[]
for x in [-75,25,85]:
    edge=73 if x==25 else 40
    for sign in [-1,1]:
        y=sign*(edge+2)
        floor=floor.fuse(rounded(12,8,7,2,(x,y,-4)))
        floor=floor.cut(slot(x,y,5,2.6,z=-5,height=8))
        wireloops.append((x,y))
floor=floor.clean()
floor=drill(floor,floorholes+bumperholes+postholes)
for x,y in componentholes: floor=insert_pocket(floor,(x,y,3))
for y in [-REAR_BUMPER_SLOT_Y,REAR_BUMPER_SLOT_Y]:
    floor=floor.cut(slot(REAR_BUMPER_SLOT_X,y,REAR_BUMPER_SLOT_LENGTH,HOLE,z=-10,height=15))
for x in [-28,62]:
    for y in [-65,65]: floor=floor.cut(box(SOCKET,SOCKET,14,(x,y,-9)))
for x in [-MOUNT_X,MOUNT_X]:
    for y in [-18,18]:floor=floor.cut(slot(x,y,FLOOR_SLOT_LENGTH,HOLE,z=-12,height=20))
floor=floor.clean()
record('01_floor_rear',floor.intersect(box(175,200,24,(-87.5,0,-12))).clean(),rotation=((1,0,0),180),note='v06 flat-face print fix: mounting face DOWN, rails UP. 7 mm web. No supports under main floor; brim recommended. Insert and mounting locations retained.')
record('02_floor_front',floor.intersect(box(175,200,24,(87.5,0,-12))).clean(),rotation=((1,0,0),180),note='v06 flat-face print fix: mounting face DOWN, rails UP. 7 mm web. No supports under main floor; brim recommended. Insert and mounting locations retained.')
place('01_floor_rear');place('02_floor_front')
splice=drill(rounded(40,16,SPLICE_THICKNESS,2),[(-10,0),(10,0)])
for x in [-10,10]:splice=insert_pocket(splice,(x,0,SPLICE_THICKNESS))
record('03_floor_splice_print_4',splice,qty=4,note='Four 8 mm insert splices. Install inserts in top face BEFORE assembly. Eight M3x16 bolts.')
for y in [-65,65]:place('03_floor_splice_print_4',(0,y,-6-SPLICE_THICKNESS))
for y in [-32,32]:place('03_floor_splice_print_4',(0,y,RAIL_BOTTOM-SPLICE_THICKNESS))

# Fixed dump-style cargo bed. Solid floor, four walls and external rind ledges.
# Same four mounting holes as v0.6; no hinges or tipping mechanism.
bed=rounded(132,134,36,5).cut(rounded(127.2,129.2,38,2.6,(0,0,2.4)))
bed=cq.Workplane(obj=bed).edges('>Z').fillet(0.6).val()
# Low rounded cargo-floor ribs; bolts and removable liner remain accessible.
for y in [-48,-16,16,48]:bed=bed.fuse(rounded(112,1.8,0.8,0.8,(0,y,2.4)))
# Seven-mm ledges support nominal 5-mm rind without relying on the ties for weight.
bed=union(bed,rounded(132,7.2,2.4,2,(0,-70.4,0)),rounded(132,7.2,2.4,2,(0,70.4,0)),rounded(7.2,148,2.4,2,(-69.4,0,0)))
bed=drill(bed,[(x,y) for x in [-51,51] for y in [-30,30]])
for x in [-44,0,44]:
    for y in [-66,66]:
        for z in [10,28]:bed=bed.cut(cyl(1.6,10,(x,y-5,z),(0,1,0)))
for y in [-44,0,44]:
    for z in [10,28]:bed=bed.cut(cyl(1.6,10,(-70,y,z),(1,0,0)))
# Paired plaque tie holes align with ears on the signs, through the rind.
for x in [-37.5,37.5]:
    for y in [-66,66]:
        for z in [18,24]:bed=bed.cut(cyl(1.4,10,(x,y-5,z),(0,1,0)))
record('04_fixed_dump_bed',bed.clean(),note='Fixed tray; flat floor down, open top up. Rind rests on outside ledges; secure through wall holes. No supports expected; inspect slicing.')
place('04_fixed_dump_bed',(-99,0,23))

def spacer(height):return cyl(4.5,height).cut(cyl(1.7,height+2,(0,0,-1)))
record('05_bed_spacer_20mm_print_4',spacer(20),qty=4)
for x in [-150,-48]:
    for y in [-30,30]:place('05_bed_spacer_20mm_print_4',(x,y,3))

# Seat pedestal with bolt-on bench; underside access for two M3 nuts.
stand=union(box(44,114,3,(0,0,22)),box(44,8,25,(0,-45,0)),box(44,8,25,(0,45,0)))
for y in [-45,45]: stand=stand.cut(box(22,10,16,(0,y,4)))
stand=drill(stand,[(x,y) for x in [-15,15] for y in [-45,45]])
for y in [-24,24]:stand=stand.fuse(cyl(5.5,5,(0,y,17)))
stand=drill(stand,[(0,-24),(0,24)])
for y in [-24,24]:stand=insert_pocket(stand,(0,y,25))
record('06_seat_pedestal',stand,rotation=((1,0,0),180))
place('06_seat_pedestal',(-5,0,3))
cushion=cq.Workplane(obj=rounded(50,120,8,5)).edges('>Z').fillet(1.2).val()
back=cq.Workplane(obj=rounded(6,120,43,2,(-22,0,5))).edges('>Z').fillet(0.8).val()
bench=union(cushion,back)
bench=bench.cut(rounded(44,112,7,2,(0,0,-1)))
bench=bench.cut(box(4.2,112,34,(-23.1,0,10))).clean()
# Shallow upholstery seams leave the cushion and back skins intact.
for y in [-38,0,38]:
    bench=bench.cut(cyl(0.45,35,(-13,y,7.9),(1,0,0)))
    bench=bench.cut(box(0.6,0.8,28,(-19.05,y,13)))
# Two compression bosses carry the bench bolts through the hollow cushion.
for y in [-24,24]:bench=bench.fuse(cyl(4.5,7,(0,y,0)))
bench=drill(bench,[(0,-24),(0,24)],z=-1,h=11)
# Armrest bolt pads sit inside the sidewalls; holes are at cushion mid-height.
for x in [-14,20]:
    for y in [-60,52]:
        boss=cyl(4.5,8,(x,y,4),(0,1,0)).intersect(box(60,130,8,(0,0,0)))
        bench=bench.fuse(boss)
    bench=bench.cut(cyl(1.7,130,(x,-65,4),(0,1,0)))
for x in [-14,20]:
    for sign in [-1,1]:bench=insert_pocket(bench,(x,sign*60,4),(0,-sign,0))
bench=bench.clean()
record('07_bench_seat',bench,'cream',rotation=((1,0,0),90),note='Print on bench end; inspect new bosses/supports. Insert pockets in four side pads. Armrest M3x8, bench to pedestal M3x16.')
place('07_bench_seat',(-5,0,28))
arm=union(box(43,3.2,4,(0,0,23)),box(4,3.2,25,(-19.5,0,0)),box(4,3.2,25,(19.5,0,0)))
arm=cq.Workplane(obj=arm).edges('|Y').fillet(1.1).val()
for x in [-17,17]:
    arm=arm.fuse(cyl(4.5,3.2,(x,-1.6,-2),(0,1,0)))
    arm=arm.cut(cyl(1.7,8,(x,-4,-2),(0,1,0)))
arm=arm.clean()
record('08_armrest_print_2',arm,qty=2,rotation=((1,0,0),90),note='Print flat as supplied. Two M3 x8 through side lugs into bench inserts. Fit before attaching bench.')
for y in [-61.6,61.6]:place('08_armrest_print_2',(-2,y,34))

# Roof pillars with 4 mm locating pegs; sockets are nominal 4.4 mm.
def pillar(offset):
    pts=[(-3,3),(3,3),(3,106),(offset+3,125),(offset+3,132),(offset-3,132),(offset-3,127),(-3,108)]
    rod=cq.Workplane('XZ').polyline(pts).close().extrude(4).translate((0,2,0)).val()
    rod=cq.Workplane(obj=rod).edges('|Y').fillet(0.8).val()
    foot=drill(rounded(24,10,3,2),[(-8,0),(8,0)])
    lug=box(10,4,8,(offset,0,124))
    result=union(rod,foot,lug,box(4,4,5,(0,0,-5)),box(4,4,4,(offset,0,132)))
    result=result.cut(cyl(1.7,10,(offset,-5,128),(0,1,0)))
    if offset==20:
        # Symmetrical ears: use only the inward hole on each side of the cart.
        for z in [62,100]:
            result=result.fuse(rounded(8,20,8,1,(-1,0,z-4)))
            for y in [-6.5,6.5]:
                result=result.cut(cyl(1.7,12,(-6,y,z),(1,0,0)))
                result=insert_pocket(result,(-5,y,z),(1,0,0))
    return result.clean()
record('09_rear_roof_post_print_2',pillar(-8),qty=2,rotation=((1,0,0),90),note='Print on side; supports may be needed under wider foot/ears. Pegs locate; two M3x8 bolts fix foot; one M3x16 fixes roof clevis. Front ears accept inserts from rear side.')
record('10_front_roof_post_print_2',pillar(20),qty=2,rotation=((1,0,0),90),note='Print on side; supports may be needed under wider foot/ears. Pegs locate; two M3x8 bolts fix foot; one M3x16 fixes roof clevis. Front ears accept inserts from rear side.')
for y in [-65,65]:
    place('09_rear_roof_post_print_2',(-28,y,3))
    place('10_front_roof_post_print_2',(62,y,3))
# Shallow transverse crown: top center Z=10, outer edges about Z=4.94.
# A 1.6-mm curved shell, skirt and ribs keep added weight modest.
outer=cyl(700,170,(-85,0,-690),(1,0,0))
inner=cyl(698.4,172,(-86,0,-690),(1,0,0))
outline=rounded(158,168,12,12)
roof=outer.cut(inner).intersect(outline)
rim=rounded(158,168,12,12).cut(rounded(154.8,164.8,14,10.4,(0,0,-1))).intersect(outer)
roof=union(roof,rim)
# Ribs meet the curved shell; socket locations and mounting plane stay fixed.
roof=union(roof,box(154,1.6,10).intersect(outer),box(1.6,164,10).intersect(outer))
for x in [-59,59]:
    for y in [-65,65]:
        roof=roof.fuse(box(10,10,10,(x,y,0)).intersect(outer))
        roof=roof.cut(box(4.4,4.4,4.4,(x,y,-0.01)))
# Clevis cheeks drop below the skirt for unobstructed screwdriver access.
for x in [-59,59]:
    for y in [-65,65]:
        sign=1 if y>0 else -1
        roof=roof.fuse(box(10,2,9.2,(x,y-sign*3.2,-9)))
        roof=roof.fuse(box(10,8,9.2,(x,y+sign*6.2,-9)))
        roof=roof.cut(cyl(1.7,24,(x,y-12,-4),(0,1,0)))
        roof=insert_pocket(roof,(x,y+sign*10.2,-4),(0,-sign,0))
record('11_roof',roof.clean(),'tan',note='Crown UP, clevis feet DOWN. Use brim and build-plate supports under roof. Clear peg sockets and cross holes. Four M3x16 cross bolts enter from inward cheeks, into inserts in outer cheeks. Install inserts before roof assembly.')
place('11_roof',(23,0,135))

# Dashboard shell on two legs. A diagonal bore accepts steering-column stem.
dash=rounded(18,116,24,3,(0,0,30))
dash=dash.cut(box(12,104,18,(4,0,32))) # hollow from front +X
dash=union(dash,box(12,8,32,(0,-45,0)),box(12,8,32,(0,45,0)))
for y in [-45,45]:dash=dash.fuse(box(18,14,3,(-12,y,0)))
dash=drill(dash,[(-14,-45),(-14,45)])
axis=(-2**-.5,0,2**-.5)
anchor=np.array([-2.,-28.,42.]);av=np.array(axis)
# Back of this angled boss is accessible through the hollow rear of the dash.
dash=dash.fuse(cyl(5,18,tuple(anchor-av*8),axis))
dash=dash.cut(cyl(3.2,19,tuple(anchor),axis))
dash=dash.cut(cyl(1.7,30,tuple(anchor-av*10),axis)).clean()
dash=insert_pocket(dash,tuple(anchor-av*8),axis)
# Tool-access relief behind the insert mouth; leaves the insert boss intact.
dash=dash.cut(cyl(4.5,18,tuple(anchor-av*8.02),tuple(-av))).clean()
# Shallow top cup recesses and a driver-facing gauge / glovebox detail.
for y in [-16,16]:dash=dash.cut(cyl(4.5,2,(0,y,53)))
for y in [2,17]:
    bezel=cyl(5.4,1.0,(-9.7,y,43),(1,0,0)).cut(cyl(4.1,0.75,(-9.75,y,43),(1,0,0)))
    dash=dash.fuse(bezel)
    dash=dash.fuse(box(0.6,4.6,0.7,(-9.2,y,42.65)))
# Engraved glovebox rectangle, with a raised handle.
frame=box(0.6,22,11,(-8.9,40,36)).cut(box(1,20.4,9.4,(-8.9,40,36.8)))
dash=dash.cut(frame).fuse(rounded(1.1,7,1.2,0.45,(-9.15,40,42))).clean()
record('12_dashboard',dash,rotation=((0,1,0),90),note='Enable supports for the recessed dashboard face and leg details; inspect slicer preview')
place('12_dashboard',(55,0,3))
wheel=cyl(12,3).cut(cyl(9,5,(0,0,-1)))
wheel=cq.Workplane(obj=wheel).edges().fillet(0.65).val()
wheel=wheel.fuse(cyl(4,3))
for angle in [0,120,240]:wheel=wheel.fuse(box(20,2.5,3).rotate((0,0,0),(0,0,1),angle))
wheel=union(wheel,cyl(3,24,(0,0,-24)))
wheel=wheel.cut(cyl(1.7,30,(0,0,-25))).clean()
record('13_steering_wheel_and_column',wheel,rotation=((1,0,0),180),note='Wheel face DOWN, column UP. M3x35 through hub/column into insert installed at rear of dash boss. Decorative fixed wheel.')
place('13_steering_wheel_and_column',(36.03,-28,61.97),rotation=((0,1,0),-45))

# Front cradle for the hollow pumpkin hood, with low retaining rim.
hood=rounded(76,88,2.4,9).cut(rounded(60,70,5,6,(0,0,-1)))
hood=union(hood,box(8,76,2.4,(-30,0,0)),box(8,76,2.4,(30,0,0)),box(64,6,2.4))
hood=union(hood,rounded(76,88,6,9).cut(rounded(71.2,83.2,8,6.6,(0,0,-1))))
hood=cq.Workplane(obj=hood).edges('>Z').fillet(0.55).val()
hood=drill(hood,[(x,y) for x in [-30,30] for y in [-30,30]])
record('14_hood_pumpkin_carrier',hood)
place('14_hood_pumpkin_carrier',(130,0,12))
record('15_hood_spacer_9mm_print_4',spacer(9),qty=4)
for x in [100,160]:
    for y in [-30,30]:place('15_hood_spacer_9mm_print_4',(x,y,3))

# End-mount prototypes: two rows separate chassis screws from floor bolts.
# Upper row x=+5, y=+/-18; chassis row x=-5, y=+/-half spacing.
# Chassis slot length 12 allows each screw center +/-4.3 mm across the car.
# The floor's 26 mm fore/aft slots allow +/-11.3 mm adjustment per end.
def end_adapter(spacing,thickness):
    a=rounded(30,spacing+22,thickness,3)
    a=drill(a,[(5,-18),(5,18)],z=-1,h=thickness+2)
    if thickness>=INSERT_DEPTH:
        for y in [-18,18]:a=insert_pocket(a,(5,y,thickness))
    for y in [-spacing/2,spacing/2]:
        cut=cq.Workplane('XY').center(-5,y).slot2D(12,HOLE,angle=90).extrude(thickness+2).translate((0,0,-1)).val()
        a=a.cut(cut)
    return a.clean()
record('16A_front_end_adapter_TRIAL',end_adapter(FRONT_CHASSIS_SPACING,ADAPTER_THICKNESS),note='8 mm trial adapter; front chassis slots nominal 36 mm centers. Fit template 00C first. Chassis screw thread/length not yet confirmed.')
record('16B_rear_end_adapter_TRIAL',end_adapter(REAR_CHASSIS_SPACING,ADAPTER_THICKNESS),note='8 mm trial adapter; rear chassis slots nominal 86 mm centers. Fit template 00D first. Chassis screw thread/length not yet confirmed.')
record('17_mount_shim_12mm_print_4',cyl(6,MOUNT_SHIM_HEIGHT).cut(cyl(1.7,MOUNT_SHIM_HEIGHT+2,(0,0,-1))),qty=4,note='12 mm provisional spacer between adapter and floor underside. Adjust height only after checking clearances under load.')
record('17B_mount_shim_2mm_OPTIONAL',cyl(6,2).cut(cyl(1.7,4,(0,0,-1))),qty=0,note='Optional 2 mm adjustment washer. Print only as required; use equal stacks left/right. Longer bolts may be needed.')
adapter_z=WEB_BOTTOM-MOUNT_SHIM_HEIGHT-ADAPTER_THICKNESS
place('16B_rear_end_adapter_TRIAL',(-MOUNT_X-5,0,adapter_z))
place('16A_front_end_adapter_TRIAL',(MOUNT_X+5,0,adapter_z),rotation=((0,0,1),180))
for x in [-MOUNT_X,MOUNT_X]:
    for y in [-18,18]:place('17_mount_shim_12mm_print_4',(x,y,WEB_BOTTOM-MOUNT_SHIM_HEIGHT))
record('00C_front_mount_TEMPLATE_2mm',end_adapter(FRONT_CHASSIS_SPACING,2),note='PRINT FIRST. Thin fit template ONLY, never use to carry the cart. Chassis holes are the slotted row; round holes belong to floor bolts.')
record('00D_rear_mount_TEMPLATE_2mm',end_adapter(REAR_CHASSIS_SPACING,2),note='PRINT FIRST. Thin fit template ONLY, never use to carry the cart. Chassis holes are the slotted row; round holes belong to floor bolts.')

# Small optional detail parts.
bezel=union(cyl(5,2),cyl(3.7,5,(0,0,1))).cut(cyl(2.65,10,(0,0,-1)))
for x in [-6.5,6.5]:
    bezel=bezel.fuse(rounded(5,5,2,1,(x,0,0)))
    bezel=bezel.cut(cyl(.9,4,(x,0,-1)))
bezel=bezel.clean()
record('18_5mm_LED_bezel_print_2',bezel,qty=2,note='Optional: thread through flange ears to retain bezel in rind. Actual LED fit/retention must be checked; wiring not supplied.')
for y in [-29,29]:place('18_5mm_LED_bezel_print_2',(164,y,31),rotation=((0,1,0),90))
plaque=rounded(65,17,1.2,2)
letters=cq.Workplane('XY').text('IT DEPT',10,0.8,font='DejaVu Sans',kind='bold',halign='center',valign='center',combine=True).translate((0,0,1.1)).val()
plaque=union(plaque,letters)
for x in [-37.5,37.5]:
    plaque=plaque.fuse(rounded(10,12,1.6,2,(x,0,0)))
    for y in [-3,3]:plaque=plaque.cut(cyl(1.4,4,(x,y,-1)))
plaque=plaque.clean()
record('19_IT_DEPT_plaque_print_2',plaque,qty=2,note='Paint raised letters white. Two narrow ties/thread loops per plaque pass through paired ear/bed holes, with rind between. Do not cinch against wet rind.')
for y,ang in [(-72.2,90),(72.2,-90)]:place('19_IT_DEPT_plaque_print_2',(-99,y,44),rotation=((1,0,0),ang))
bumper=cq.Workplane(obj=rounded(12,98,5,4)).edges('not |Z').fillet(0.8).val()
bumper=drill(bumper,[(0,-30),(0,30)])
record('20A_front_bumper',bumper,note='M3x10 into front floor inserts; original footprint retained.')
place('20A_front_bumper',(171,0,3))
# Rear beam sits behind floor; two narrow arms reach forward to adjustable mounts.
rear_bumper=rounded(12,98,5,4)
for y in [-REAR_BUMPER_SLOT_Y,REAR_BUMPER_SLOT_Y]:
    rear_bumper=rear_bumper.fuse(rounded(32,6,5,2,(12,y,0)))
    rear_bumper=rear_bumper.fuse(cyl(4,5,(20,y,0)))
rear_bumper=drill(rear_bumper,[(20,-REAR_BUMPER_SLOT_Y),(20,REAR_BUMPER_SLOT_Y)])
record('20B_rear_bumper_adjustable',rear_bumper.clean(),note='Two M3x20 bolts with washers through arms and floor slots into 20C blocks. Nominal travel 16.6 mm; fit on actual chassis.')
place('20B_rear_bumper_adjustable',(-184,0,3))
slider=drill(rounded(10,10,8,2),[(0,0)],z=-1,h=10)
slider=insert_pocket(slider,(0,0,8))
record('20C_rear_bumper_insert_block_print_2',slider,qty=2,note='Install insert in top face. Block rests below rear reinforced slot at Z=-8; hold while starting bolt, slide bumper then snug.')
for y in [-REAR_BUMPER_SLOT_Y,REAR_BUMPER_SLOT_Y]:place('20C_rear_bumper_insert_block_print_2',(REAR_BUMPER_SLOT_X,y,-16))

# Screw-on windshield pressure plates. Sheet is not a printed component.
clip=drill(rounded(8,10,2,1),[(0,0)])
record('21_windshield_plate_print_4',clip,qty=4,note='Flat face DOWN. Four M3x10 bolts clamp thin clear sheet to inward holes on front post ears. Sheet nominal 0.75 mm; adjust hardware to actual thickness.')
for y in [-58.5,58.5]:
    for z in [65,103]:place('21_windshield_plate_print_4',(65.75,y,z),rotation=((0,1,0),90))

# First print: isolated peg/socket coupon. No chassis dimensions assumed.
coupon=box(48,22,3)
for x,w in [(-14,4.2),(0,4.4),(14,4.6)]:coupon=coupon.cut(box(w,w,5,(x,0,-1)))
# Asymmetric notch identifies the 4.2 mm end even after the part leaves the bed.
coupon=coupon.cut(cyl(2,5,(-24,0,-1)))
record('00_fit_coupon',coupon,note='Print FIRST with 00b: slots from notched end are 4.2/4.4/4.6 mm')
record('00b_fit_peg',union(box(12,12,3),box(4,4,5,(0,0,3))),note='Print FIRST with 00: use this separate 4.0 mm peg to test the slots')

# Insert fit coupon: seven through-relieved blind pockets, labeled by CAD diameter.
fit=rounded(160,22,9,2)
for i,dia in enumerate([3.8,3.9,4.0,4.1,4.2,4.3,4.4,4.5,4.6,4.7,4.8]):
    x=-70+i*14
    fit=fit.cut(cyl(1.7,11,(x,3,-1)))
    fit=insert_pocket(fit,(x,3,9),diameter=dia)
    label=cq.Workplane('XY').text(f'{dia:.1f}',3.2,.5,font='DejaVu Sans',combine=True).translate((x,-6,9)).val()
    fit=fit.fuse(label)
record('00E_M3_insert_fit_test',fit.clean(),note='Test 4.0 mm first. Pockets 3.8 to 4.8 mm, depth 6.7, for assumed 5.7 mm insert. Choose secure fit without bulging; measure longer/larger inserts before use.')

# Assembly STEP is a reference assembly in world coordinates, not a print plate.
assembly=cq.Assembly(name='IT_DEPT_Pumpkin_Cart_v06')
for i,(name,s,color) in enumerate(instances):
    assembly.add(s,name=f'{name}_{i}',color=cq.Color(color))
assembly.export(str(ROOT/'CAD'/'Pumpkin_Cart_Assembly.step'))

manifest=[]
for name,d in parts.items():
    manifest.append({'file':name+'.stl','quantity':d['qty'],'print_size_mm':d['size'],
        'volume_cm3':round(d['volume_mm3']/1000,2),'solid_PLA_mass_g':round(d['volume_mm3']/1000*1.24,1),'note':d['note']})
(ROOT/'Guides'/'parts_manifest.json').write_text(json.dumps(manifest,indent=2))
with (ROOT/'Guides'/'parts_list.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['STL file','Quantity','Print X mm','Print Y mm','Print Z mm','Solid PLA g each','Notes'])
    for d in manifest:w.writerow([d['file'],d['quantity'],*d['print_size_mm'],d['solid_PLA_mass_g'],d['note']])

# Validate generated binary STL edge incidence; also retain CAD solid checks.
checks=[]
for name,d in parts.items():
    raw=(ROOT/'STL'/f'{name}.stl').read_bytes(); n=struct.unpack_from('<I',raw,80)[0]
    edges={}; deg=0; signedvol=0
    for i in range(n):
        row=struct.unpack_from('<12fH',raw,84+i*50)
        v=np.array(row[3:12]).reshape(3,3)
        keys=[tuple(np.round(a,5)) for a in v]
        if np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))<1e-9:deg+=1
        signedvol+=np.dot(v[0],np.cross(v[1],v[2]))/6
        for a,b in [(0,1),(1,2),(2,0)]:
            key=tuple(sorted([keys[a],keys[b]]));edges[key]=edges.get(key,0)+1
    bad=sum(v!=2 for v in edges.values())
    fit=all(a<=230 for a in d['size'])
    checks.append({'part':name,'CAD_valid':d['shape'].isValid(),'CAD_solids':len(d['shape'].Solids()),'triangles':n,'nonmanifold_edges':bad,'degenerate_triangles':deg,'positive_volume':bool(signedvol>0),'fits_230mm_envelope':fit})
    assert bad==0 and deg==0 and signedvol>0 and fit,(name,checks[-1])
(ROOT/'Guides'/'mesh_validation.json').write_text(json.dumps(checks,indent=2))
print('Created',len(parts),'unique STL files;',len(instances),'assembly instances')
print('Solid PLA envelope mass, excluding coupons:',round(sum(d['volume_mm3']*d['qty']*1.24/1000 for n,d in parts.items() if not n.startswith('00')),1),'g')

# Check for unintended overlap among printable assembly parts (not reference pumpkin/chassis).
overlaps=[]
for i,(na,sa,_) in enumerate(instances):
    a=sa.BoundingBox()
    for nb,sb,_ in instances[i+1:]:
        b=sb.BoundingBox()
        if any(min(getattr(a,k+'max'),getattr(b,k+'max'))-max(getattr(a,k+'min'),getattr(b,k+'min'))<=.001 for k in ['x','y','z']):continue
        v=sa.intersect(sb).Volume()
        if v>.05:overlaps.append({'part_a':na,'part_b':nb,'overlap_mm3':round(v,3)})
(ROOT/'Guides'/'assembly_overlap_check.json').write_text(json.dumps(overlaps,indent=2))
print('Assembly overlaps:',overlaps)
assert not overlaps, 'Unexpected interference between printable assembly parts'

# Actual CAD render: gray wheels/chassis and orange panels are reference volumes only.
if __name__=='__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    refs=[]
    for x in [-WHEELBASE/2,WHEELBASE/2]:
        for y in [-66,66]:
            refs.append((cyl(34,18,(x,y-9,-31),(0,1,0)),'#303538',1))
            refs.append((cyl(17,19,(x,y-9.5,-31),(0,1,0)),'#9ea8ad',1))
    refs.append((box(190,68,20,(0,0,-38)),'#647075',.6))
    for y in [-69.5,69.5]:refs.append((box(128,5,30,(-99,y,25.4)),'#e68022',.72))
    refs.append((box(5,144,30,(-167.5,0,25.4)),'#e68022',.72))
    pumpkin_hood=cq.Workplane(obj=rounded(69,81,30,12,(130,0,16))).edges('>Z').fillet(5).val()
    refs.append((pumpkin_hood,'#e68022',.62))
    # Clear plastic windshield: lower cab portion; template is intentionally cut-to-fit.
    refs.append((box(.75,124,48,(65.375,0,61)),'#9dcbd5',.22))
    def draw(ax,items,elev,azim):
        # Orthographic software z-buffer. Avoids painter-order artifacts on thin CAD faces.
        from PIL import Image
        width,height=1200,880
        el,az=np.radians([elev,azim])
        eye=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
        right=np.array([-np.sin(az),np.cos(az),0.]);up=np.cross(eye,right)
        projection=np.stack([right,up,eye],axis=1)
        triangles=[];colors=[];alphas=[]
        for shape,color,alpha in items:
            vertices,faces=shape.tessellate(.65,.25)
            world=np.array([v.toTuple() for v in vertices])[np.array(faces)]
            normal=np.cross(world[:,1]-world[:,0],world[:,2]-world[:,0])
            normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
            light=.63+.32*np.abs(normal[:,2])+.08*np.abs(normal[:,0])
            rgb=np.array(matplotlib.colors.to_rgb(color))*255
            triangles.extend(world@projection)
            colors.extend(np.clip(light[:,None]*rgb[None,:],0,255))
            # Orange pieces illustrate real rind, not transparent plastic.
            alphas.extend([1. if alpha>.5 else alpha]*len(world))
        triangles=np.array(triangles);colors=np.array(colors);alphas=np.array(alphas)
        lo=triangles[:,:,:2].min(axis=(0,1));hi=triangles[:,:,:2].max(axis=(0,1))
        scale=min((width-90)/(hi[0]-lo[0]),(height-70)/(hi[1]-lo[1]))
        mid=(lo+hi)/2
        triangles[:,:,0]=(triangles[:,:,0]-mid[0])*scale+width/2
        triangles[:,:,1]=height/2-(triangles[:,:,1]-mid[1])*scale
        canvas=np.full((height,width,3),[245,243,239],dtype=float)
        depth=np.full((height,width),-np.inf)
        opaque=np.where(alphas>=1)[0]
        transparent=np.where(alphas<1)[0]
        transparent=transparent[np.argsort(triangles[transparent,:,2].mean(axis=1))]
        for i in np.concatenate([opaque,transparent]):
            a,b,c=triangles[i];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-6:continue
            x0=max(0,int(np.floor(min(a[0],b[0],c[0]))));x1=min(width-1,int(np.ceil(max(a[0],b[0],c[0]))))
            y0=max(0,int(np.floor(min(a[1],b[1],c[1]))));y1=min(height-1,int(np.ceil(max(a[1],b[1],c[1]))))
            if x0>x1 or y0>y1:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            w=1-u-v;z=u*a[2]+v*b[2]+w*c[2]
            target=depth[y0:y1+1,x0:x1+1]
            mask=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(z>target+1e-6)
            patch=canvas[y0:y1+1,x0:x1+1]
            patch[mask]=colors[i]*alphas[i]+patch[mask]*(1-alphas[i])
            if alphas[i]>=1:target[mask]=z[mask]
        ax.imshow(Image.fromarray(canvas.astype(np.uint8)));ax.set_axis_off()
    items=[(s,col,1) for _,s,col in instances]
    fig=plt.figure(figsize=(15,9),facecolor='#f5f3ef')
    ax=fig.add_axes([0,.12,.67,.74],facecolor='#f5f3ef')
    draw(ax,items+refs,23,-132)
    ax2=fig.add_axes([.64,.36,.35,.49],facecolor='#f5f3ef')
    draw(ax2,items,23,-48)
    fig.text(.055,.93,'IT DEPT / PUMPKIN CART',fontsize=25,weight='bold',color='#273436')
    fig.text(.055,.884,'V0.6 INSERT FRAME  •  Photo-based trial end mounts  •  PLA prototype',fontsize=12,color='#606c6c')
    fig.text(.69,.35,'ACTUAL CAD PARTS',fontsize=12,weight='bold',color='#273436')
    fig.text(.69,.25,'6 mm floor + deep underside rails\nFour reinforced splice plates\nSlotted front and rear trial mounts',fontsize=11,linespacing=1.65,color='#606c6c')
    fig.text(.055,.08,'350 mm / 13.8 in long     |     168 mm / 6.6 in roof width     |     213 mm / 8.4 in axle spacing',fontsize=12,color='#273436')
    fig.text(.055,.04,'Orange = pumpkin placeholders. Gray chassis and wheels are assumed envelopes. Mounting and load capacity are unverified.',fontsize=10,color='#7b6450')
    fig.savefig(ROOT/'Guides'/'Assembly_Preview.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    # Side and top layout for measurement discussion.
    fig=plt.figure(figsize=(13,8),facecolor='white')
    a=fig.add_subplot(211);draw(a,items+refs,0,-90)
    b=fig.add_subplot(212);draw(b,items+refs,90,-90)
    fig.suptitle('Prototype layout — all dimensions in millimeters; chassis shown schematically',fontsize=15)
    fig.savefig(ROOT/'Guides'/'Layout_Views.png',dpi=150,bbox_inches='tight');plt.close(fig)

    # Detail views contain only actual printable geometry, not concept art.
    fig=plt.figure(figsize=(14,10),facecolor='#f5f3ef')
    specs=[('11_roof','CROWNED ROOF',24,-135),('07_bench_seat','ROUNDED SEAT + UPHOLSTERY SEAMS',28,40),('04_fixed_dump_bed','FIXED BED + SOFT LIP + FLOOR RIBS',32,-130),('12_dashboard','GAUGES + CUP RECESSES + GLOVEBOX',28,-145)]
    for i,(key,title,el,az) in enumerate(specs):
        ax=fig.add_subplot(2,2,i+1)
        draw(ax,[(parts[key]['shape'],parts[key]['color'],1)],el,az)
        ax.set_title(title,fontsize=12,color='#273436',pad=4)
    fig.suptitle('V0.6 / PRINTABLE DETAIL STUDIES',fontsize=20,color='#273436',weight='bold')
    fig.text(.08,.025,'Actual CAD geometry. Fit, printed finish and RC carrying capacity remain untested.',fontsize=11,color='#606c6c')
    fig.savefig(ROOT/'Guides'/'Detail_Closeups.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
