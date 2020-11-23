"""
3d printed part, has the vacuum hose inserted and duct taped to it, attached
with magnets to vac_brack, and has a tube going up to vac_hangar.
Origin will be bottom center of the spindle's collet nut.
"""


import importlib
import math
import cadquery as cq
import dims
import vac_helpers as vh
importlib.reload(dims)
importlib.reload(vh)

# make top wire
# make bottom wire
# top face is cq.Face.makeFromWire(top_wire)
# bottom face is cq.Face.makeFromWire(bottom_wire)
# vertical face is cq.Face.makeRuledSurface(top_wire, bottom_wire)
# then make shell, solid, cut

# some dimensions:
inner_port_major_rad = dims.vac.inner_rad + dims.vac.wall_thick
outer_port_major_rad = inner_port_major_rad + dims.vac.port.rad * 2
brush_slot_major_radius = (
    outer_port_major_rad + dims.vac.wall_thick
    + 15 + dims.vac.brush.slot_width / 2
)
body_major_radius = (
    brush_slot_major_radius + dims.vac.brush.slot_width / 2
    + dims.vac.wall_thick
)
# the width of material between the edge of the vacuum port and outer edge
vac_port_to_body_outer = (body_major_radius - outer_port_major_rad)

kidney_wire, hose_wire = vh.kidney_and_circle_wires(
    dims.vac.hose.id / 2,
    cq.Vector(dims.vac.hose.plane.origin),
    inner_port_major_rad,
    outer_port_major_rad
)

vert_face = cq.Face.makeRuledSurface(kidney_wire, hose_wire)

bottom_face = cq.Face.makeFromWires(kidney_wire)
rev_hose_wire = cq.Edge(hose_wire.wrapped.Reversed())
top_face = cq.Face.makeFromWires(rev_hose_wire)

shell = cq.Shell.makeShell([bottom_face, vert_face, top_face])
solid = cq.Solid.makeSolid(shell)
vacuum_path = cq.Workplane(solid)

part = (
    cq
    .Workplane()
    .moveTo(dims.vac.mount_face.x_max, dims.vac.mount_face.y)
    .hLineTo(dims.vac.mount_face.x_min)
    .vLineTo(dims.vac.inner_rad)
    .hLineTo(0)
    .tangentArcPoint((0, -dims.vac.inner_rad * 2), relative=True)
    # now I need a tangentArcPoint out to the outer edge, which takes into account the slot for the brush.
)
# y centre of the circle
yc = -inner_port_major_rad - dims.vac.port.rad
# radius of outer edge
r_outer_initial = dims.vac.port.rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick
r_outer = dims.vac.port.rad + vac_port_to_body_outer
# to get to that radius, the line must extend horizontally until
x_start = math.sqrt(r_outer ** 2 - (dims.vac.port.rad + dims.vac.wall_thick) ** 2)
# inner radius of the kidney shape
rk_inner = abs(yc) - dims.vac.port.rad - dims.vac.wall_thick
rk_outer = rk_inner + dims.vac.port.rad + r_outer
part = (
    part
    .spline(
        [(-r_outer_initial - 5, yc)]
        , tangents=[(-1, 0), (0, -1)]
        , includeCurrent=True
    )
    # .radiusArc((0, -body_major_radius), -r_outer)
    .spline(
        [(0, -body_major_radius)],
        tangents=[(0, -1), (1, 0)],
        includeCurrent=True,
    )
    .radiusArc((body_major_radius, 0), -body_major_radius)
    .spline(
        [(dims.vac.mount_face.x_max, dims.vac.mount_face.y)]
        , tangents=[(0, 1), (-1, 0)]
        , includeCurrent=True
    )
    .close()
    .extrude(dims.vac.z)
    .tag('base')
    .faces(">Y")
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, dims.vac.z / 2))
    .pushPoints([(-pos, 0) for pos in dims.vac_brack.holes])
    .circle(dims.vac_brack.hole.cbore_diam / 2 - 0.1)
    .extrude(dims.vac_brack.hole.cbore_depth - 2, taper=10)
    .faces(">Z", tag='base')
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, 0))
    .hole(dims.spindle.bearing_cap.diam + 2, dims.spindle.bearing_cap.height + 2)
)

kidney_wire, hose_wire = vh.kidney_and_circle_wires(
    dims.vac.chimney.main_od / 2 + dims.vac.wall_thick,
    dims.vac.hose.plane.origin,
    rk_inner,
    body_major_radius
)
vert_face = cq.Face.makeRuledSurface(kidney_wire, hose_wire)

bottom_face = cq.Face.makeFromWires(kidney_wire)
reversed_hose_wire = cq.Edge(hose_wire.wrapped.Reversed())
top_face = cq.Face.makeFromWires(reversed_hose_wire)
shell = cq.Shell.makeShell([bottom_face, vert_face, top_face])
vacuum_port_walls = cq.Solid.makeSolid(shell)
upper_vac = (
    cq.Workplane('XY', origin=dims.vac.hose.plane.origin)
    .circle(dims.vac.chimney.main_od / 2 + dims.vac.wall_thick)
    .extrude(dims.vac.wall_thick)
    .tag('base')
    .faces('>Z')
    .workplane()
    .hole(dims.vac.chimney.main_od, dims.vac.wall_thick)
    .faces('>Z', tag='base')
    .workplane()
    .hole(dims.vac.hose.id)
    .union(vacuum_port_walls, clean=False, tol=0.1)
)

brush_offset = dims.vac.wall_thick + dims.vac.brush.slot_width / 2
r_brush_to_port = dims.vac.port.rad + brush_offset
brush_slot_path = (
    cq
    .Workplane()
    .moveTo(dims.vac.mount_face.x_min, r_brush_to_port)
    .hLineTo(abs(yc))
    .spline(
        [(brush_slot_major_radius, 0)],
        tangents=[(1, 0), (0, -1)],
        includeCurrent=True,
    )
    .tangentArcPoint((0, -brush_slot_major_radius), relative=False)
    .spline(
        [(-r_brush_to_port, yc + 5)],
        tangents=[(-1, 0), (0, 1)],
        includeCurrent=True
    )
)
brush_slot = (
    cq
    .Workplane('XZ', origin=brush_slot_path.val().endPoint())
    .center(0, dims.vac.brush.slot_depth / 2)
    .moveTo(-dims.vac.brush.slot_width / 2, -dims.vac.brush.slot_depth / 2)
    .hLine(dims.vac.brush.slot_width)
    .vLine(dims.vac.brush.slot_depth - dims.vac.brush.slot_width)
    .tangentArcPoint((-dims.vac.brush.slot_width, 0), relative=True)
    .close()
    .sweep(brush_slot_path)
)

part = part.union(upper_vac).cut(vacuum_path).cut(brush_slot)
cutters = []
for pos in dims.magnet.positions:
    selector = ">Z" if pos[1] >= 0 else "<Z"
    inverse_selector = "<Z" if pos[1] >= 0 else ">Z"
    cut_depth = dims.vac.z / 2 - max([y for _, y in dims.magnet.positions])
    temp = (
        part
        .faces(selector, tag='base')
        .workplane(
            centerOption='ProjectedOrigin',
            origin=(
                0,
                dims.vac.mount_face.y - dims.magnet.wall_thick - dims.magnet.slot.thick / 2,
                0
            )
        )
        .move(pos[0], 0)
        .rect(dims.magnet.slot.width, dims.magnet.slot.thick, centered=True)
        .extrude(-cut_depth, combine=False)
        .faces(inverse_selector)
        .workplane()
        .center(0, -dims.magnet.slot.thick / 2)
        .rect(dims.magnet.slot.width / 2, dims.magnet.slot.thick, centered=False)
        .revolve(axisEnd=(0, 1))
    )
    cutters.append(temp)
    del temp
for cutter in cutters:
    part = part.cut(cutter)
    del cutter
