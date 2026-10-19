from pathlib import Path
import numpy as np
import cadquery as cq
from PIL import Image,ImageDraw,ImageFont
WORK=None
GRAY='#a5b3b5'; DARK='#53666b'; TEAL='#137b78'; ORANGE='#d97933'; TAN='#c9b594'; CREAM='#e4d7bc'; METAL='#7a8b93'
mesh_cache={}
def mesh(shape):
    k=id(shape)
    if k not in mesh_cache:
        v,f=shape.tessellate(.25,.16)
        xyz=np.array([p.toTuple() for p in v])[np.array(f)]
        # Store reference as well, preventing object ID reuse.
        mesh_cache[k]=(shape,xyz)
    return mesh_cache[k][1]
def select(prefixes,shift=(0,0,0),color=TEAL):
    ans=[]
    for name,shape,col in instances:
        if any(name.startswith(p) for p in prefixes):ans.append((shape,np.array(shift),col if color is None else color))
    return ans
def part(prefix):
    return next(v['shape'] for k,v in parts.items() if k.startswith(prefix))
def pitem(prefix,shift=(0,0,0),color=TEAL,rot=None):
    sh=part(prefix)
    if rot:sh=sh.rotate((0,0,0),rot[0],rot[1])
    return (sh,np.array(shift),color)
def bolt(x,y,top,length=20):
    # Schematic M3 screw: shaft extends downward from the underside of its head.
    return (union(cyl(2.75,2,(x,y,top)),cyl(1.5,length,(x,y,top-length))),np.zeros(3),METAL)
def nut(x,y,z):
    sh=cq.Workplane('XY').polygon(6,6.4).extrude(2.4).val().cut(cyl(1.7,5,(0,0,-1))).translate((x,y,z))
    return sh,np.zeros(3),METAL
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=ImageFont.truetype(BOLD,25)
def render(name,items,labels=(),arrows=(),view=(25,-132),width=1200,height=740):
    el,az=np.radians(view);eye=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.array([-np.sin(az),np.cos(az),0]);up=np.cross(eye,right);proj=np.stack([right,up,eye],axis=1)
    tris=[];colors=[]
    lightvec=np.array([-.35,-.5,.79]);lightvec/=np.linalg.norm(lightvec)
    for shape,shift,color in items:
        tri=mesh(shape)+shift
        normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        rgb=np.array([int(color[i:i+2],16) for i in [1,3,5]])
        brightness=.62+.32*np.maximum(normals@lightvec,0)+.12*np.abs(normals[:,2])
        tris.extend(tri@proj);colors.extend(np.clip(brightness[:,None]*rgb,0,255))
    tris=np.array(tris);colors=np.array(colors)
    lo=tris[:,:,:2].min((0,1));hi=tris[:,:,:2].max((0,1));mid=(lo+hi)/2
    scale=min((width-230)/(hi[0]-lo[0]),(height-150)/(hi[1]-lo[1]))
    tris[:,:,0]=(tris[:,:,0]-mid[0])*scale+width/2
    tris[:,:,1]=height/2-(tris[:,:,1]-mid[1])*scale
    def pt(v):
        q=np.array(v)@proj;return np.array([(q[0]-mid[0])*scale+width/2,height/2-(q[1]-mid[1])*scale])
    canvas=np.full((height,width,3),[247,248,246],float);depth=np.full((height,width),-np.inf)
    for tri,rgb in zip(tris,colors):
        a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-7:continue
        x0=max(0,int(np.floor(min(a[0],b[0],c[0]))));x1=min(width-1,int(np.ceil(max(a[0],b[0],c[0]))))
        y0=max(0,int(np.floor(min(a[1],b[1],c[1]))));y1=min(height-1,int(np.ceil(max(a[1],b[1],c[1]))))
        if x0>x1 or y0>y1:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
        z=u*a[2]+v*b[2]+w*c[2];target=depth[y0:y1+1,x0:x1+1]
        mask=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(z>target+1e-6)
        canvas[y0:y1+1,x0:x1+1][mask]=rgb;target[mask]=z[mask]
    im=Image.fromarray(canvas.astype('uint8'));d=ImageDraw.Draw(im)
    for start,end in arrows:
        a=pt(start);b=pt(end);delta=b-a;norm=np.linalg.norm(delta)
        if norm<6:continue
        unit=delta/norm;perp=np.array([-unit[1],unit[0]])
        for q in np.arange(0,norm-10,14):
            q2=min(q+8,norm-10);d.line([tuple(a+unit*q),tuple(a+unit*q2)],fill=ORANGE,width=3)
        d.polygon([tuple(b),tuple(b-unit*13+perp*5),tuple(b-unit*13-perp*5)],fill=ORANGE)
    for label,target,pos in labels:
        a=pt(target);b=np.array([pos[0]*width,pos[1]*height]);bw=max(54,int(d.textlength(label,font=font))+18);bh=38
        d.line([tuple(a),tuple(b)],fill='#33484d',width=2)
        d.ellipse([a[0]-4,a[1]-4,a[0]+4,a[1]+4],fill='#33484d')
        d.rounded_rectangle([b[0]-bw/2,b[1]-bh/2,b[0]+bw/2,b[1]+bh/2],radius=10,fill='#137b78')
        d.text(tuple(b),label,font=font,anchor='mm',fill='white')
    path=WORK/(name+'.png');im.save(path);print('Rendered',name,flush=True);return path


def make_previews(root,assemblies,layout):
    global WORK
    WORK=root/'Guides'
    def rb(x,y,z,c=(0,0,0),r=1):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).edges('|Z').fillet(r).translate(c).val()
    def cb(x,y,z,c=(0,0,0)):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(c).val()
    def cy(r,h,p,d):return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*d))
    def scene(name,extra=(0,0,0)):
        out=[(s,np.array(loc)+np.array(extra),color) for s,loc,color in assemblies[name]]
        # Thin reference surfaces indicate proposed paint, not extra STL pieces.
        if name in ['24-port switch','8-port switch']:
            rows,cols,dep,pitch,pw=(2,12,26,3.9,2.8) if name.startswith('24') else (1,8,22,3.25,2.3)
            for row in range(rows):
                for i in range(cols):out.append((cb(pw-.1,.015,2,( (i-(cols-1)/2)*pitch,-dep/2+.615,2.35+row*3.2)),np.array(extra),'#121c20'))
        if name=='Bullet camera':out.append((cy(4.05,.012,(12.61,0,7.2),(1,0,0)),np.array(extra),'#172831'))
        if name=='Dome camera':out.append((cy(1.55,.012,(5.46,0,4.3),(1,0,0)),np.array(extra),'#172831'))
        return out
    render('switches',scene('24-port switch',(-10,12,0))+scene('8-port switch',(18,-24,0)),view=(28,-72),width=950,height=620)
    render('cameras',scene('Bullet camera',(-13,-6,0))+scene('Dome camera',(20,9,0)),view=(24,-40),width=950,height=620)
    render('toolbox',scene('Toolbox'),view=(27,-63),width=950,height=620)
    render('coil',scene('Cable coil'),view=(44,-90),width=950,height=620)
    render('tower',scene('PC tower'),view=(23,-61),width=950,height=620)
    # Schematic copy of the exact bed interior dimensions; no chassis is depicted.
    bed=rb(132,134,36,r=5).cut(rb(127.2,129.2,38,(0,0,2.4),2.6))
    card=cb(120,120,1,(0,0,3.2))
    cargo=[(bed,np.zeros(3),'#65787d'),(card,np.zeros(3),'#c6b48e')]
    for name,loc in layout.items():cargo+=scene(name,(loc[0],loc[1],4.2))
    render('bed_fit',cargo,view=(60,-120),width=1100,height=900)
    # Top-down placement drawing. True positions/sizes; numbered props correspond to STL prefixes.
    render('Cargo_Layout_Top',cargo,labels=[('01',(-27,32,14),(.14,.24)),('02',(-33,0,12),(.13,.45)),('03',(4,-24,18),(.82,.70)),('04',(0,5,13),(.84,.38)),('05',(29,34,23),(.86,.15)),('06',(-32,-38,6),(.17,.82)),('07',(33,-17,45),(.86,.53))],view=(90,-90),width=1200,height=1000)
    # Exploded lids for the four two-piece props. Distances are illustrative.
    lids=[];arrows=[];labels=[]
    for n,pos,tag in [('24-port switch',(-42,28),'01'),('8-port switch',(38,28),'02'),('Toolbox',(-38,-26),'05'),('PC tower',(38,-26),'07')]:
        for i,(sh,loc,col) in enumerate(assemblies[n]):
            shift=np.array([pos[0]+loc[0],pos[1]+loc[1],loc[2]+(12 if i else 0)])
            lids.append((sh,shift,col))
            if i:arrows.append(((pos[0],pos[1],loc[2]+12),(pos[0],pos[1],loc[2])))
        labels.append((tag,(pos[0],pos[1],4),{'01':(.12,.28),'02':(.86,.20),'05':(.12,.77),'07':(.85,.69)}[tag]))
    render('Cargo_Lid_Assembly',lids,labels=labels,arrows=arrows,view=(32,-120),width=1200,height=900)
    # Presentation contact sheet of actual modeled geometry with suggested paint accents.
    canvas=Image.new('RGB',(1800,1940),'#f7f8f6');draw=ImageDraw.Draw(canvas)
    title=ImageFont.truetype(BOLD,48);head=ImageFont.truetype(BOLD,28);small=ImageFont.truetype(FONT,23)
    draw.text((65,45),'IT CART / MINIATURE CARGO',font=title,fill='#203d43')
    draw.text((65,112),'Printable CAD models - suggested colors and painted details',font=small,fill='#577076')
    panels=[('switches','24-PORT + 8-PORT SWITCHES'),('cameras','BULLET + DOME CAMERAS'),('toolbox','TOOLBOX WITH HANDLE'),('coil','CABLE COIL'),('tower','OPTIONAL PC TOWER'),('bed_fit','ALL SEVEN OBJECTS IN THE BED')]
    for i,(filename,titletext) in enumerate(panels):
        x=45+(i%2)*890;y=195+(i//2)*555
        im=Image.open(WORK/(filename+'.png'));im.thumbnail((850,480))
        canvas.paste(im,(x+(850-im.width)//2,y+40+(480-im.height)//2))
        draw.text((x+20,y),titletext,font=head,fill='#203d43')
    draw.text((65,1870),'Decorative miniatures. Geometry checked; print quality and RC load remain untested.',font=small,fill='#577076')
    canvas.save(WORK/'Accessory_Preview.png')
    print('Accessory previews complete',flush=True)
