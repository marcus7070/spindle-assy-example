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

def kidney_shape(
        top_rad
        , top_pos
        , bot_inner_rad
        , bot_outer_rad
    ):
    """
    creates a lofted shape from a circle at top_pos with radius top_rad down to
    a kidney shape centered at the origin and with inner radius bot_inner_rad
    and outer radius bot_outer_rad.
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


inner_port_major_rad = dims.vac.inner_rad + dims.vac.wall_thick
outer_port_major_rad = inner_port_major_rad + dims.vac.port.rad * 2
bottom_wire = (
    cq
    .Workplane()
    .moveTo(inner_port_major_rad, 0)
    .radiusArc(
        (outer_port_major_rad, 0)
        , radius=dims.vac.port.rad
    )
    .radiusArc((0, -outer_port_major_rad), radius=outer_port_major_rad)
    .radiusArc((0, -inner_port_major_rad), radius=dims.vac.port.rad)
    .radiusArc((inner_port_major_rad, 0), radius=-inner_port_major_rad)
    .wire()
    .val()
)
offset = dims.vac.hose.id / 2 * math.sin(math.pi / 4)
top_edge_angles = (
    (67.5, 135)
    , (135, 315)
    , (315, 22.5)
    , (22.5, 67.5)
)
top_edges = [
    cq.Edge.makeCircle(
        dims.vac.hose.id / 2
        , dims.vac.hose.plane.origin
        # , (inner_port_major_rad, -inner_port_major_rad, 20)
        , dir=(0, 0, -1)
        , angle1=a1
        , angle2=a2
    ) for a1, a2 in top_edge_angles
]
top_wire = cq.Wire.assembleEdges(top_edges)
vert_face = cq.Face.makeRuledSurface(bottom_wire, top_wire)
# show_object(vert_face)
bottom_face = cq.Face.makeFromWires(bottom_wire)
top_face = cq.Face.makeFromWires(top_wire)
shell = cq.Shell.makeShell([bottom_face, vert_face, top_face])
# show_object(shell)
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
part = (
    part
    .spline(
        [(-r_outer, yc)]
        , tangents=[(-1, 0), (0, -1)]
        , includeCurrent=True
    )
    .radiusArc((0, yc - dims.vac.port.rad - dims.vac.wall_thick - dims.vac.brush.slot_width - dims.vac.wall_thick), -(dims.vac.port.rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick))
    .radiusArc((outer_port_major_rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick, 0), -(outer_port_major_rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick))
    .spline(
        [(dims.vac.mount_face.x_max, dims.vac.mount_face.y)]
        , tangents=[(0, 1), (-1, 0)]
        , includeCurrent=True
    )
    .close()
    .extrude(dims.vac.z)
    # .wire()
)

hose_adaptor = (
    cq
    .Workplane('XY', origin=dims.vac.hose.plane.origin)
    .circle(dims.vac.hose.socket.od / 2)
    .extrude(dims.vac.hose.insertion)
)
# upper_spline = [
#     cq.Vector(
#         dims.vac.hose.plane.origin[0] + dims.vac.hose.socket.od / 2 + 2
#         , dims.vac.hose.plane.origin[1]
#     ), cq.Vector(
#         dims.vac.hose.plane.origin[0]
#         , dims.vac.hose.plane.origin[1] - dims.vac.hose.socket.od / 2 - 2
#     ), cq.Vector(
#         dims.vac.mount_face.x_max * math.cos(math.radians(180 + 45))
#         , dims.vac.mount_face.x_max * math.sin(math.radians(180 + 45))
#     )
# ]
# lower_spline = [
#     (upper_spline[0] + cq.Vector(dims.vac.mount_face.x_max, 0, 0)) / 2
#     , (upper_spline[1] + cq.Vector(-dims.vac.hose.socket.od / 2, -dims.vac.hose.socket.od / 2, 0)) / 2
#     , upper_spline[2]
# ]
# 
# part = (
#     cq
#     .Workplane()
#     .moveTo(dims.vac.mount_face.x_min, dims.vac.mount_face.y)
#     .hLineTo(dims.vac.mount_face.x_max)
#     .lineTo(lower_spline[0].x, lower_spline[0].y)
# )
# # # an arc around the spindle axis with radius dims.vac.mount_face.x_max
# start_tangent = part.val().tangentAt(1)
# end_tangent = cq.Vector(-1, 1, 0).normalized()
# part = (
#     part
#     .spline(
#         listOfXYTuple=lower_spline
#         , tangents=(start_tangent, end_tangent)
#     )
# )
# radius = dims.vac.inner_rad
# endangle = math.radians(180 + 45)
# endpoint = (
#     radius * math.cos(endangle)
#     , radius * math.sin(endangle)
# )
# part = (
#     part
#     .lineTo(*endpoint)
#     .threePointArc(
#         (radius, 0)
#         , (endpoint[0], -endpoint[1])
#     )
#     .close()
# )
# part = (
#     part
#     .copyWorkplane(cq.Workplane("XY", origin=(0, 0, dims.vac.z)))
#     .moveTo(dims.vac.mount_face.x_min, dims.vac.mount_face.y)
#     .hLineTo(dims.vac.mount_face.x_max)
#     .lineTo(upper_spline[0].x, upper_spline[0].y)
# )
# start_tangent = part.val().tangentAt(1)
# end_tangent = cq.Vector(-1, 1, 0).normalized()
# part = (
#     part
#     .spline(
#         listOfXYTuple=upper_spline
#         , tangents=(start_tangent, end_tangent)
#     )
#     .lineTo(
#         dims.vac.inner_rad * math.cos(math.radians(180 + 45))
#         , dims.vac.inner_rad * math.sin(math.radians(180 + 45))
#     )
#     .threePointArc(
#         (dims.vac.inner_rad, 0)
#         , (
#             dims.vac.inner_rad * math.cos(math.radians(180 + 45))
#             , -dims.vac.inner_rad * math.sin(math.radians(180 + 45))
#         )
#     )
#     .close()
#     .loft()
#     .tag('base')
#     .faces(">Z")
#     .workplane(centerOption='ProjectedOrigin', origin=(0, 0, 0))
#     .hole(dims.spindle.bearing_cap.diam + 2, dims.spindle.bearing_cap.height + 2)
#     .copyWorkplane(cq.Workplane("XY"))
#     .transformed(offset=dims.vac.hose.plane.origin)
#     .circle(dims.vac.hose.socket.od / 2)
#     .extrude(dims.vac.hose.insertion)
#     .faces(">Z")
#     .workplane()
#     .tag('hose_bottom')
#     .hole(dims.vac.hose.od, dims.vac.hose.insertion - dims.vac.wall_thick)
#     .workplaneFromTagged('hose_bottom')
#     .hole(dims.vac.hose.id, dims.vac.hose.insertion)
#     .workplaneFromTagged('hose_bottom')
#     .polygon(4, dims.vac.hose.socket.od)
#     .extrude(dims.vac.hose.tape_width)
#     .faces(">Z")
#     .workplane()
#     .hole(dims.vac.hose.od + 2, dims.vac.hose.tape_width)
# )
# 
# vac_path = (
#     cq
#     .Workplane()
#     .moveTo(dims.vac.mount_face.x_max, dims.vac.mount_face.y)
#     .lineTo(lower_spline[0].x, lower_spline[0].y)
# )
# # # an arc around the spindle axis with radius dims.vac.mount_face.x_max
# start_tangent = vac_path.val().tangentAt(1)
# end_tangent = cq.Vector(-1, 1, 0).normalized()
# vac_path = (
#     vac_path
#     .spline(
#         listOfXYTuple=lower_spline
#         , tangents=(start_tangent, end_tangent)
#     )
# )
# radius = dims.vac.inner_rad
# endangle = math.radians(180 + 45)
# endpoint = (
#     radius * math.cos(endangle)
#     , radius * math.sin(endangle)
# )
# vac_path = (
#     vac_path
#     .lineTo(*endpoint)
# )
# endangle = math.radians(45)
# vac_path = (
#     vac_path
#     .threePointArc(
#         (radius, 0)
#         , (radius * math.cos(endangle), radius * math.sin(endangle))
#     )
#     .close()
#     .offset2D(-dims.vac.wall_thick)
#     .copyWorkplane(cq.Workplane("XY"))
#     .transformed(offset=dims.vac.hose.plane.origin)
#     .circle(dims.vac.hose.id / 2)
#     .loft()
# )
# part = (
#     part
#     .cut(vac_path)
#     .faces(">Y")
#     .workplane(centerOption='ProjectedOrigin', origin=(0, 0, dims.vac.z / 2))
#     .pushPoints([(-pos, 0) for pos in dims.vac_brack.holes])
#     .circle(dims.vac_brack.hole.cbore_diam / 2 - 0.1)
#     .extrude(dims.vac_brack.hole.cbore_depth - 2, taper=10)
# )
# cutters = []
# for pos in dims.magnet.positions:
#     selector = ">Z" if pos[1] >= 0 else "<Z"
#     inverse_selector = "<Z" if pos[1] >= 0 else ">Z"
#     cut_depth = dims.vac.z / 2 - max([y for _, y in dims.magnet.positions])
#     temp = (
#         part
#         .faces(selector, tag='base')
#         .workplane(centerOption='ProjectedOrigin', origin=(0, dims.vac.mount_face.y - dims.magnet.wall_thick - dims.magnet.slot.thick / 2, 0))
#         .move(pos[0], 0)
#         .rect(dims.magnet.slot.width, dims.magnet.slot.thick, centered=True)
#         .extrude(-cut_depth, combine=False)
#         .faces(inverse_selector)
#         .workplane()
#         .center(0, -dims.magnet.slot.thick / 2)
#         .rect(dims.magnet.slot.width / 2, dims.magnet.slot.thick, centered=False)
#         .revolve(axisEnd=(0, 1))
#     )
#     cutters.append(temp)
# outer_cutter = (
#     cq
#     .Workplane()
#     .moveTo(dims.vac.hose.plane.origin[0] + dims.vac.hose.socket.od / 2 + 1e-4, 20)
#     .vLineTo(upper_spline[0].y)
#     .radiusArc((
#             dims.vac.hose.plane.origin[0]
#             , dims.vac.hose.plane.origin[1] - dims.vac.hose.socket.od / 2 - 1e-4
#         )
#         , dims.vac.hose.socket.od / 2 + 1e-4)
#     .hLine(-100)
#     .vLine(-20)
#     .hLine(200)
#     .close()
#     .extrude(dims.vac.z + 5)
# )
# # cutters.append(outer_cutter)  # removes the top surface, fuck it
# for cutter in cutters:
#     part = part.cut(cutter)
# del cutter, temp, vac_path, outer_cutter


