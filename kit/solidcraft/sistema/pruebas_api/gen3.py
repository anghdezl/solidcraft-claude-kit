import json,sys
pre=sys.argv[1]
def c(cmd,**p): return {"command":cmd,"params":p}
box=c("solid.box",length=40,width=30,height=20,corner=[0,0,0],name="B",body_name="B")
sk=lambda n="s1",pl="XY",**k:c("sketch.create",name=n,plane=pl,**k)
fin=c("sketch.finish")
import os
D=os.path.dirname(os.path.abspath(__file__))+os.sep
T={}
def t(i,*x): T[i]=list(x)
t("bogus_param",c("solid.box",length=40,width=30,height=20,foo=123,name="B",body_name="B"))
t("bogus_cmd",c("solid.cuboid",length=1))
t("sk_par",sk(),c("sketch.line",points=[[0,0],[30,0]]),c("sketch.line",points=[[0,10],[30,14]]),c("sketch.constraint.parallel",a="l1",b="l2"),fin)
t("sk_perp",sk(),c("sketch.line",points=[[0,0],[30,0]]),c("sketch.line",points=[[0,0],[5,20]]),c("sketch.constraint.perpendicular",a="l1",b="l2"),fin)
t("sk_equal",sk(),c("sketch.line",points=[[0,0],[30,0]]),c("sketch.line",points=[[0,10],[25,10]]),c("sketch.constraint.equal",a="l1",b="l2"),fin)
t("sk_concentric",sk(),c("sketch.circle.center",center=[0,0],radius=5),c("sketch.circle.center",center=[2,0],radius=9),c("sketch.constraint.concentric",a="c1",b="c2"),fin)
t("sk_pat_rect",sk(),c("sketch.circle.center",center=[0,0],radius=2),c("sketch.pattern.rectangular",entities=["c1"],count=3,spacing=10),fin)
t("sk_extend",sk(),c("sketch.line",points=[[0,0],[30,0]]),c("sketch.line",points=[[40,-5],[40,5]]),c("sketch.extend",curve="l1",at=[30,0]),fin)
t("sk_trim",sk(),c("sketch.line",points=[[0,0],[30,0]]),c("sketch.line",points=[[10,-5],[10,5]]),c("sketch.trim",curve="l1",at=[5,0]),fin)
t("sk_project",box,sk("p","XY",offset=20),c("sketch.project",refs=[{"edge":[20,0,20]}]),fin)
t("sk_slotcp",sk(),c("sketch.slot.center_point",center=[0,0],end=[20,0],width=6),fin)
t("sk_export_dxf",sk(),c("sketch.circle.center",center=[0,0],radius=5),c("sketch.export_dxf",path=D+"t.dxf"),fin)
t("do_metadata",c("document.metadata.set",key="author",value="usuario"),c("document.metadata"))
t("pa_fastener",box,c("parts.fastener",family="socket_head_cap_screw",size="M3",length=10,point=[100,0,0],direction=[0,0,1]))
t("mesh_conv",c("file.insert_mesh",path=D+"t.stl"),c("select.set",items=[{"type":"body","name":"t"}]),c("mesh.convert"))
t("jo_hinge",c("component.create",name="Ca"),c("solid.box",length=40,width=30,height=10,corner=[0,0,0],name="A",body_name="A"),c("component.create",name="Cb",parent=None),c("solid.box",length=40,width=30,height=10,corner=[50,0,0],name="Bb",body_name="Bb"),c("inspect.measure"))
t("jo_origin",c("component.create",name="Ca"),c("solid.box",length=40,width=30,height=10,corner=[0,0,0],name="A",body_name="A"),c("joint.origin",name="oa",occurrence="Ca",face=[20,15,10]))
for k,v in T.items(): json.dump({"pasos":[["cmd",x] for x in v]},open("trabajos/%s_%s.json"%(pre,k),"w"))
print(len(T))
