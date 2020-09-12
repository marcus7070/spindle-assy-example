import cadquery as cq
import importlib
import dims
importlib.reload(dims)


output = False

bracket = (
    cq
    .Workplane("XZ")
    .tag('base')
    .box(dims.bracket.width, dims.bracket.height, dims.bracket.thick, centered=(True, True, False))
    .workplaneFromTagged('base')
    .workplane(offset=dims.bracket.thick)
    .tag('holeplane')
    .rect(*dims.clamp.bolt.spacing, forConstruction=True)
    .vertices()
    .hole(8)
)
if output:
    print("\nM8 threaded hole at:")
    for p in (cq.Workplane().rect(*dims.clamp.bolt.spacing).vertices().vals()):
        print("x: " + str(p.X) + ", y: " + str(p.Y))

# v_slot_x = [(-1.5 + idx) * 20 for idx in range(4)]
v_slot_x = [(-1.5 + idx) * 20 for idx in [0, 3]]
tee_nut_holes_y = [(idx - 1) * dims.bracket.tee_nut_spacing for idx in range(3)]
points = []
for xval in v_slot_x:
    for yval in tee_nut_holes_y:
        points.append((xval, yval))
if output:
    print("Diam 5.5 hole with counterbore at diam 10, leave 9mm thick of material after counterbore")
    for p in points:
        print("x: " + str(p[0]) + ", y: " + str(p[1]))
bracket = (
    bracket
    .pushPoints(points)
    .cboreHole(5 * 1.2, 10, dims.bracket.thick - dims.bracket.m5.v_slot_face_to_top)
    .faces(">Y")
    .edges("|Z")
    .chamfer(5)
)
