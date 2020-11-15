import cadquery as cq
import vslot
import clamp as clamp_module
import bracket as bracket_module
import spindle as spindle_module
import vac_brack as vac_brack_module
import vac as vac_module
import chimney as chimney_module
import dims
import importlib
importlib.reload(dims)
importlib.reload(clamp_module)
importlib.reload(bracket_module)
importlib.reload(spindle_module)
importlib.reload(vac_brack_module)
importlib.reload(vac_module)
importlib.reload(chimney_module)

assy = cq.Assembly()

back = vslot.cslot(250)
assy.add(back, name="back", color=cq.Color(0.8, 0.8, 0.8))
assy.add(bracket_module.bracket, name="bracket", color=cq.Color(0.9, 0.9, 0.95))
# Make the constraint between the centre of the bottom back edge of the bracket
# and the centre of the bottom front edge of the back aluminium profile plus an
# offset
backpoint = back.faces("<Z", tag="unslotted").edges("<Y").translate((0, 0, dims.bottom_of_vslot_to_bottom_of_bracket)).val()
bracketpoint = bracket_module.bracket.faces("<Z").edges(">Y").val()
# assy.constrain("bracket@faces@>Y", "back@faces@<Y", "Plane")
assy.constrain("back", backpoint, "bracket", bracketpoint, "Point")
assy.constrain("back", back.faces("<Y", tag="unslotted").val(), "bracket", bracket_module.bracket.faces(">Y").val(), "Axis")
assy.constrain("back", back.faces("<Z", tag="unslotted").val(), "bracket", bracket_module.bracket.faces(">Z").val(), "Axis")

clamp = clamp_module.clamp.rotate((0, 0, 0), (0, 0, 1), 180)
assy.add(clamp, name="clamp")
assy.constrain("bracket@faces@<Y", "clamp@faces@>Y", "Plane")
assy.constrain("bracket@faces@<Z", "clamp@faces@>Z", "Axis")

spindle = spindle_module.spindle
assy.add(spindle, name="spindle", color=cq.Color(0.9, 0.7, 0.8))
spindle_lower_face = spindle.faces(cq.NearestToPointSelector((0, 0, dims.spindle.body.length / 2))).edges("<Z").val()
clamp_lower_face = clamp.faces("<Z").edges("%CIRCLE").val()
assy.constrain("clamp", clamp_lower_face, "spindle", spindle_lower_face.translate((0, 0, dims.spindle.body.clamp_end_offset)), "Plane")

vac_brack = vac_brack_module.bracket
assy.add(vac_brack, name="vac_brack", color=cq.Color(0.2, 0.2, 0.2, 0.8))
backpoint2 = back.faces("<Z", tag="unslotted").edges("<Y").vertices(">X").val()
vac_brack_point = vac_brack.faces("<Z").edges(">Y").vertices(">X").val()
assy.constrain("back", backpoint2, "vac_brack", vac_brack_point, "Point")
assy.constrain("back@faces@<Z", "vac_brack@faces@>Z", "Axis")
assy.constrain("back", back.faces("<Y", tag="unslotted").val(), "vac_brack", vac_brack.faces(">Y").val(), "Axis")

vac = vac_module.part
assy.add(vac, name="vac", color=cq.Color(0.3, 0.2, 0.3, 0.8))
vac_brack_front_bottom_left = vac_brack.faces("<Y").edges("<X").vertices("<Z").val()
vac_back_bottom_left = vac.faces(">Y", tag="base").edges("<X").vertices("<Z").val()
assy.constrain("vac_brack", vac_brack_front_bottom_left, "vac", vac_back_bottom_left, "Point")
assy.constrain("vac_brack", vac_brack.faces("<Y").val(), "vac", vac.faces(">Y", tag="base").val(), "Axis")
assy.constrain("vac_brack", vac_brack.faces("<Z").val(), "vac", vac.faces("<Z").val(), "Axis", param=0)

chimney = chimney_module.chimney
assy.add(chimney, name="chimney", color=cq.Color(0.3, 0.2, 0.3, 0.8))
assy.constrain(
    "vac",
    vac.edges("%CIRCLE").edges(cq.NearestToPointSelector(dims.vac.hose.plane.origin)).val(),
    "chimney",
    chimney.faces("<Z").edges("%CIRCLE").val(),
    "Plane",
    param=0,
)
assy.constrain(
    "back",
    back.faces("<Y", tag="unslotted").val(),
    "chimney",
    chimney.faces(">(1, 1, 0)", tag="mountbase").val(),
    "Axis",
    param=180,
)

try:
    assy.solve()
except Exception as e:
    print(e)
    raise e
show_object(assy)
dir(assy)
for name, child in assy.traverse():
    print(f"name: {name}, obj: {child}")
print(assy.objects["chimney"].loc)
part_a = chimney.faces(">(1, 1, 0)", tag='mountbase').val().located(assy.objects["chimney"].loc)
show_object(part_a)
show_object(assy.objects["chimney"].obj)
