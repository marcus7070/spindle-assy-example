"""
3d printed part, has the vacuum hose inserted and duct taped to it, attached
with magnets to vac_brack, and has a tube going up to vac_hangar.
Origin will be bottom center of the spindle's collet nut.
"""


import importlib
import math
import cadquery as cq
import dims
importlib.reload(dims)

# ##########################################################################
# figuring out orientation for directly created surfaces
# even though I think OCC doesn't care about face orientation, I get so many
# kernel errors this can't do anything but help.
# ##########################################################################
# circ1 = cq.Edge.makeCircle(10, angle1=0, angle2=45)
# show_object(circ1)
# print(circ1.startPoint())
# print(circ1.endPoint())

# so angle1=0 places the startpoint on the x axis
# angle1=45 places the endpoint in the +x and +y quadrant
# this should be the orientation of the top circle
# the kidney shaped vacuum port should be flipped compared to this
# then I think the ruled surface between the two will take care of itself.


# make top wire
# make bottom wire
# top face is cq.Face.makeFromWire(top_wire)
# bottom face is cq.Face.makeFromWire(bottom_wire)
# vertical face is cq.Face.makeRuledSurface(top_wire, bottom_wire)
# then make shell, solid, cut

def kidney_and_circle_wires(
        top_rad
        , top_pos
        , bot_inner_rad
        , bot_outer_rad
    ):
    """
    creates the wires required for a lofted shape from a circle at top_pos with
    radius top_rad down to a kidney shape centered at the origin and with inner
    radius bot_inner_rad and outer radius bot_outer_rad.
    """
    # calculate tangential points between the two shapes, these will become
    # "control points"
    # draw a line between the origin and top_pos, where it intersect with the
    # kidney shape will become two more "control points"
    # make sure ruledSurface matches the circle's right side tangential point
    # with the kidney shape's right side tangential point, and the same for the
    # rest of the control points
    # inner centre control point of the kidney shape is the start point, points
    # will continue clockwise (opposite to the circle test above)
    # if there is a point 2/3 of the way along the perimeter between the first
    # and second control points, create another point 2/3 of the way along the
    # perimeter between the first and second control point of the circle.
    kidney_control_points = []
    hose_control_points = []
    # first point is inner centre of kidney
    # what's the angle to the vacuum hose?
    angle = math.atan(top_pos[1] / top_pos[0]) + math.pi
    # kidney control point
    x0, y0 = bot_inner_rad * math.sin(angle), bot_inner_rad * math.cos(angle)
    kidney_control_points.append((x0, y0))
    # hose control point
    x0 = top_pos[0] + top_rad * math.sin(angle + math.pi)
    y0 = top_pos[1] + top_rad * math.cos(angle + math.pi)
    hose_control_points.append((x0, y0))
    # tangential points
    # https://en.wikipedia.org/wiki/Tangent_lines_to_circles#Outer_tangent
    # radius at the tip of the kidney shape
    r1 = (bot_outer_rad - bot_inner_rad) / 2
    x1, y1 = bot_inner_rad + r1, 0
    r2 = top_rad
    x2, y2 = top_pos[0], top_pos[1]
    gamma = -math.atan((y2 - y1) / (x2 - x1))
    beta = math.asin((r2 - r1) / math.sqrt(
        (x2 - x1) ** 2 + (y2 - y1) ** 2
    ))
    alpha = gamma - beta
    x3 = x1 + r1 * math.sin(alpha)
    y3 = y1 + r1 * math.cos(alpha)
    x4 = x2 + r2 * math.sin(alpha)
    y4 = y2 + r2 * math.cos(alpha)
    # print(f"kidney tangent point = {x3}, {y3}")
    # print(f"hose tangent point = {x4}, {y4}")
    kidney_control_points.append((x3, y3))
    hose_control_points.append((x4, y4))
    # third point is outer edge of kidney
    # kidney control point
    x0, y0 = bot_outer_rad * math.sin(angle), bot_outer_rad * math.cos(angle)
    kidney_control_points.append((x0, y0))
    # hose control point
    x0 = top_pos[0] + top_rad * math.sin(angle)
    y0 = top_pos[1] + top_rad * math.cos(angle)
    hose_control_points.append((x0, y0))
    # fourth point is opposite tangent
    x1, y1 = 0, -(bot_inner_rad + r1)
    gamma = -math.atan((y2 - y1) / (x2 - x1))
    beta = math.asin((r2 - r1) / math.sqrt(
        (x2 - x1) ** 2 + (y2 - y1) ** 2
    ))
    alpha = gamma + beta
    x3 = x1 - r1 * math.sin(alpha)
    y3 = y1 - r1 * math.cos(alpha)
    x4 = x2 - r2 * math.sin(alpha)
    y4 = y2 - r2 * math.cos(alpha)
    kidney_control_points.append((x3, y3))
    hose_control_points.append((x4, y4))
    # so let's try fluent api first
    # clockwise
    kidney_points = [
        kidney_control_points[0]
        , (bot_inner_rad, 0)
        , kidney_control_points[1]
        , (bot_outer_rad, 0)
        , kidney_control_points[2]
        , (0, -bot_outer_rad)
        , kidney_control_points[3]
        , (0, -bot_inner_rad)
    ]
    temp_k = (cq.Workplane()
        .moveTo(*kidney_points[0])
        .radiusArc(kidney_points[1], -bot_inner_rad)
        .radiusArc(kidney_points[2], r1)
        .radiusArc(kidney_points[3], r1)
        .radiusArc(kidney_points[4], bot_outer_rad)
        .radiusArc(kidney_points[5], bot_outer_rad)
        .radiusArc(kidney_points[6], r1)
        .radiusArc(kidney_points[7], r1)
        .radiusArc(kidney_points[0], -bot_inner_rad)
    )
    kidney_wire = temp_k.wire().val()
    # now to evenly space points on the hose circle
    kidney_edges = kidney_wire.Edges()
    hose_points = [hose_control_points[0]]
    for idx in range(4):
        # how long is the edge from control point 0 to 1?
        length_first_section = kidney_edges[2 * idx % 8].Length()
        length_control_point_section = length_first_section + kidney_edges[(2 * idx + 1) % 8].Length()
        proportion = length_first_section / length_control_point_section
        # create an arc for subdividing
        hose_control_point_section = (
            cq
            .Workplane('XY', origin=(0, 0, top_pos[2]))
            .moveTo(*hose_control_points[idx])
            .radiusArc(hose_control_points[(idx + 1) % 4], r2)
            .val()
        )
        point = hose_control_point_section.positionAt(proportion).toTuple()
        hose_points.append(point)
        hose_points.append(hose_control_points[(idx + 1) % 4])
    hose_wire = (
        cq
        .Workplane('XY', origin=(0, 0, top_pos[2]))
        .moveTo(*hose_control_points[0])
    )
    for point in hose_points[1:]:
        hose_wire = hose_wire.radiusArc((point[0], point[1]), r2)
    hose_wire = hose_wire.wire().val()
    # return cq.Workplane(kidney_wire), cq.Workplane(hose_wire)
    return kidney_wire, hose_wire


inner_port_major_rad = dims.vac.inner_rad + dims.vac.wall_thick
outer_port_major_rad = inner_port_major_rad + dims.vac.port.rad * 2

kidney_wire, hose_wire = kidney_and_circle_wires(dims.vac.hose.id / 2, dims.vac.hose.plane.origin, inner_port_major_rad, outer_port_major_rad)

vert_face = cq.Face.makeRuledSurface(kidney_wire, hose_wire)

bottom_face = cq.Face.makeFromWires(kidney_wire)
top_wire = (
    cq
    .Workplane('XY', origin=dims.vac.hose.plane.origin)
    .circle(dims.vac.hose.id / 2)
    .wire()
    .val()
)
top_face = cq.Face.makeFromWires(top_wire)

shell = cq.Shell.makeShell([bottom_face, vert_face, top_face])
vacuum_path = cq.Workplane(cq.Solid.makeSolid(shell))

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
r_outer = dims.vac.port.rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick
# to get to that radius, the line must extend horizontally until
x_start = math.sqrt(r_outer ** 2 - (dims.vac.port.rad + dims.vac.wall_thick) ** 2)
# inner radius of the kidney shape
rk_inner = abs(yc) - dims.vac.port.rad - dims.vac.wall_thick
# rk_outer = rk_inner + dims.vac.port.rad + r_outer
rk_outer = abs(yc) + r_outer + 5
part = (
    part
    .spline(
        [(-r_outer, yc)]
        , tangents=[(-1, 0), (0, -1)]
        , includeCurrent=True
    )
    .radiusArc((0, -rk_outer), -r_outer)
    .radiusArc((rk_outer, 0), -rk_outer)
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
cutters = []
for pos in dims.magnet.positions:
    selector = ">Z" if pos[1] >= 0 else "<Z"
    inverse_selector = "<Z" if pos[1] >= 0 else ">Z"
    cut_depth = dims.vac.z / 2 - max([y for _, y in dims.magnet.positions])
    temp = (
        part
        .faces(selector, tag='base')
        .workplane(centerOption='ProjectedOrigin', origin=(0, dims.vac.mount_face.y - dims.magnet.wall_thick - dims.magnet.slot.thick / 2, 0))
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

# This has to become a long pipe with a ring on the end to sit in the upper vac
# mount
chimney = (
    cq
    .Workplane('XY', origin=dims.vac.hose.plane.origin)
    .circle(dims.vac.chimney.main_od / 2)
    .extrude(dims.vac.chimney.height)
    .faces('>Z')
    .workplane()
    .hole(dims.vac.hose.id, dims.vac.chimney.height)
)

kidney_wire, hose_wire = kidney_and_circle_wires(dims.vac.chimney.main_od / 2 + dims.vac.wall_thick, dims.vac.hose.plane.origin, rk_inner, rk_outer)
vert_face = cq.Face.makeRuledSurface(kidney_wire, hose_wire)

bottom_face = cq.Face.makeFromWires(kidney_wire)
top_wire = (
    cq
    .Workplane('XY', origin=dims.vac.hose.plane.origin)
    .circle(dims.vac.chimney.main_od / 2 + dims.vac.wall_thick)
    .wire()
    .val()
)
top_face = cq.Face.makeFromWires(top_wire)
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
    .union(vacuum_port_walls)
)

brush_offset = dims.vac.wall_thick + dims.vac.brush.slot_width / 2
r_brush_to_port = dims.vac.port.rad + brush_offset
brush_slot_path = (
    cq
    .Workplane()
    .moveTo(dims.vac.mount_face.x_min, r_brush_to_port)
    .hLineTo(abs(yc))
    .tangentArcPoint((rk_outer - brush_offset, 0), relative=False)
    .tangentArcPoint((0, -rk_outer + brush_offset), relative=False)
    .tangentArcPoint((-r_brush_to_port, r_brush_to_port), relative=True)
)
brush_slot = (
    cq
    .Workplane('XZ', origin=brush_slot_path.val().endPoint())
    .center(0, dims.vac.brush.slot_depth / 2)
    .rect(dims.vac.brush.slot_width, dims.vac.brush.slot_depth, centered=True)
    .sweep(brush_slot_path)
)

part = part.union(upper_vac).cut(vacuum_path)  #.cut(brush_slot)
del vacuum_path, upper_vac, # brush_slot_path, brush_slot
