"""
3d printed part, has the vacuum hose inserted and duct taped to it, attached
with magnets to vac_brack, and has a tube going up to vac_hangar.
Origin will be bottom center of the spindle's collet nut.
"""


import importlib
import math
import cadquery as cq
import dims
from itertools import cycle
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

# some classes to simplify this kidney/circle shape relationship, since doing
# this functionally is doing my head in
class Point:
    """
    A point on either the kidney shape or the circle shape.
    """

    def __init__(self, x=None, y=None, z=None, control_point=False, match=None):
        """
        match is a point on the other shape. ruledSurface should draw a line
        between self and match.
        """
        self.x = x
        self.y = y
        self.z = z
        self.control_point = control_point
        self.match = None


class Arc:
    """
    All the edges in the kidney shape and circular shape are made of arcs. This
    class represents an arc.
    """

    def __init__(
            self,
            startpoint=None,
            endpoint=None,
            intermediate_points=None,
            radius=None):
        """
        intermediate points is a list of points along this arc, but there is a
        constant radius between start and endpoint.
        """
        self.startpoint = startpoint
        self.endpoint = endpoint
        self.intermediate_points = intermediate_points
        self.radius = radius

    def wire(self):
        """
        Returns this arc as a cq.Wire object.
        """
        raise NotImplementedError

    def proportions(self):
        """
        Calculates the proportion along this wire that the intermediate points
        are.
        Returns a list of floats between 0 and 1.
        """
        raise NotImplementedError

    def position(self, proportion):
        """
        Adds a point to this arc that is proportion between the start and end
        points.
        """
        raise NotImplementedError


class Loop:
    """
    Either the kidney shape or the circular shape.
    """

    def __init__(self, arcs=None):
        if arcs is None:
            arcs = []
        self.arcs = arcs

    def check(self):
        # check that endpoint of one arc is the startpoint of the next
        # sugggest itertools.cycle for the looping aspect
        raise NotImplementedError('TODO Loop.check()')

    def wire(self):
        """
        Returns all the arcs connected into a cq.Wire
        """
        raise NotImplementedError('TODO Loop.wire()')


def tangential_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos,
        side,
        ):
    """
    Calculate the tangential points between two circles with radius and
    position described by the arguments. This generates several options, pick
    the points according to side.
    """
    pass


def normal_points(
        top_rad,
        top_pos,
        inner_kidney_rad,
        outer_kidney_rad,
        side,
        ):
    """
    Calculate the normal points between a circle and a kidney shape.
    Takes a line between the origin (which is the centre of the kidney's major
    arcs) and the centre of the circle. Where this lines intercepts the kidney
    edge and circular edge are the normal points.
    """
    pass


def kidney_and_circle_wires2(
        top_rad,
        top_pos,
        bot_inner_rad,
        bot_outer_rad,
        ):
    # calculate tangential points
    circle_tangent_coords_0, kidney_tangent_coords_0 = tangential_points(
            top_rad,
            top_pos,
            port_rad,
            port_pos,
            "+X")
    circle_tangent_point_0 = Point(
            *circle_tangent_coords_0,
            z=top_pos[2],
            control_point=True
            )
    kidney_tangent_point_0 = Point(
            *kidney_tangent_coords_0,
            z=0,
            control_point=True
            )
    circle_tangent_point_0.match = kidney_tangent_point_0
    kidney_tangent_point_0.match = circle_tangent_point_0
    circle_tangent_coords_1, kidney_tangent_coords_1 = tangential_points(
            top_rad,
            top_pos,
            port_rad,
            port_pos,
            "-Y")
    circle_tangent_point_1 = Point(
            *circle_tangent_coords_1,
            z=top_pos[2],
            control_point=True
            )
    kidney_tangent_point_1 = Point(
            *kidney_tangent_coords_1,
            z=0,
            control_point=True
            )
    circle_tangent_point_1.match = kidney_tangent_point_1
    kidney_tangent_point_1.match = circle_tangent_point_1

    # calculate control points
    circle_normal_coords_inner, kidney_normal_coords_inner = normal_points(
            top_rad,
            top_pos,
            port_rad,
            port_pos,
            "+Y")
    circle_normal_point_inner = Point(
            *circle_normal_coords_inner,
            z=top_pos[2],
            control_point=True
            )
    kidney_normal_point_inner = Point(
            *kidney_normal_coords_inner,
            z=0,
            control_point=True
            )
    circle_normal_point_inner.match = kidney_normal_point_inner
    kidney_normal_point_inner.match = circle_normal_point_inner
    circle_normal_coords_outer, kidney_normal_coords_outer = normal_points(
            top_rad,
            top_pos,
            port_rad,
            port_pos,
            "-Y")
    circle_normal_point_outer = Point(
            *circle_normal_coords_outer,
            z=top_pos[2],
            control_point=True
            )
    kidney_normal_point_outer = Point(
            *kidney_normal_coords_outer,
            z=0,
            control_point=True
            )
    circle_normal_point_outer.match = kidney_normal_point_outer
    kidney_normal_point_outer.match = circle_normal_point_outer
    
    # create kidney shape arcs
    kidney_loop = Loop()
    port_rad = (bot_outer_rad - bot_inner_rad) / 2
    k_arc_0 = Arc(
            startpoint=kidney_normal_point_inner,
            endpoint=Point(x=bot_inner_rad, y=0),
            radius=-bot_inner_rad,
            )
    kidney_loop.arcs.append(k_arc_0)
    k_arc_1 = Arc(
            startpoint=k_arc_0.endpoint,
            endpoint=Point(x=bot_outer_rad, y=0),
            radius=port_rad
            )
    kidney_loop.arcs.append(k_arc_1)
    k_arc_2 = Arc(
            startpoint=k_arc_1.endpoint,
            endpoint=Point(x=0, y=-bot_outer_rad),
            radius=bot_outer_rad
            )
    kidney_loop.arcs.append(k_arc_2)
    if kidney_tangent_point_0.y > k_arc_1.endpoint.y:
        k_arc_1.intermediate_points.append(kidney_tangent_point_0)
    else:
        k_arc_2.intermediate_points.append(kidney_tangent_point_0)
    k_arc_3 = Arc(
            startpoint=k_arc_2.endpoint,
            endpoint=Point(x=bot_inner_rad, y=0),
            radius=port_rad
            )
    kidney_loop.arcs.append(k_arc_3)
    if kidney_tangent_point_1.x < k_arc_2.endpoint.x:
        k_arc_2.intermediate_points.append(kidney_tangent_point_1)
    else:
        k_arc_3.intermediate_points.append(kidney_tangent_point_1)
    k_arc_4 = Arc(
            startpoint=k_arc_3.endpoint,
            endpoint=k_arc_0.startpoint,
            radius=bot_inner_rad,
            )
    kidney_loop.arcs.append(k_arc_4)

    # map points onto circular arc
    circle = Loop()




def get_angle(centre, point):
    x = point[0] - centre[0]
    y = point[1] - centre[1]
    return math.atan2(y, x)


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
    # clockwise when looking from above
    # need two flows here, one for if the tangential control point on the kidney is above the y axis (in which case it comes first) and another for if it is below the y axis
    kcp_pos_y = kidney_control_points[1][1] > 0
    kcp_pos_x = kidney_control_points[3][0] > 0
    # kidney points is in the form [ (point, radius, constant point) ]
    # constant point are the 4 points that don't move depending on top circle position
    kidney_points = [
        (kidney_control_points[0], None, False),
        ((bot_inner_rad, 0), -bot_inner_rad, True),
    ]
    if kcp_pos_y:
        kidney_points.extend([
            (kidney_control_points[1], r1, False),
            ((bot_outer_rad, 0), r1, True),
        ])
    else:
        kidney_points.extend([
            ((bot_outer_rad, 0), r1, True), 
            (kidney_control_points[1], bot_outer_rad, False)
        ])
    kidney_points.append((kidney_control_points[2], bot_outer_rad, False))
    # same reordering as above
    if kcp_pos_x:
        kidney_points.extend([
            ((0, -bot_outer_rad), bot_outer_rad, True), 
            (kidney_control_points[3], r1, False),
        ])
    else:
        kidney_points.extend([
            (kidney_control_points[3], bot_outer_rad, False), 
            ((0, -bot_outer_rad), bot_outer_rad, True)
        ])
    kidney_points.append(((0, -bot_inner_rad), r1, True))
    kidney_points.append((kidney_points[0][0], -bot_inner_rad, False))
    temp_k = cq.Workplane().moveTo(*kidney_points[0][0])
    for point, radius, _ in kidney_points[1:]:
        temp_k = temp_k.radiusArc(point, radius)
    del point, radius, _
    kidney_wire = temp_k.wire().val()
    # now to evenly space points on the hose circle
    # still have TODO the sort depending on which side the kidney tangent
    # points wound up on
    # TODO draw a diagram of what needs to be done here. This is a fucking
    # disaster, consider starting from scratch
    kidney_edges = kidney_wire.Edges()
    # so let's make a map of what has to be done
    # we have 4 points that have to be positioned
    # their position falls on 4 wires (constant wires regardless of kcp_pos_x or kcp_pos_y)
    # but which wire they fall on changes depending on kcp_pos_x or y
    hose_points = [hose_control_points[0]]
    # for idx in range(4):
    #     # how long is the edge from control point 0 to 1?
    #     length_first_section = kidney_edges[2 * idx % 8].Length()
    #     length_control_point_section = length_first_section + kidney_edges[(2 * idx + 1) % 8].Length()
    #     proportion = length_first_section / length_control_point_section
    #     # create an arc for subdividing
    #     hose_control_point_section = (
    #         cq
    #         .Workplane('XY', origin=(0, 0, top_pos[2]))
    #         .moveTo(*hose_control_points[idx])
    #         .radiusArc(hose_control_points[(idx + 1) % 4], r2)
    #         .val()
    #     )
    #     point = hose_control_point_section.positionAt(proportion).toTuple()
    #     hose_points.append(point)
    #     hose_points.append(hose_control_points[(idx + 1) % 4])
    # first variable point
    if kcp_pos_y:
        kwire = cq.Wire.assembleEdges(kidney_edges[:3])
    else:
        kwire = cq.Wire.assembleEdges(kidney_edges[:2])
    print(f"should be y=0: {kwire.endPoint()}")
    length_first_section = kidney_edges[0].Length()
    proportion = length_first_section / kwire.Length()
    hose_wire = (
        cq
        .Workplane('XY', origin=(0, 0, top_pos[2]))
        .moveTo(*hose_control_points[0])
    )
    hose_points.append(hose_wire.positionAt(proportion))
    if kcp_pos_y:
        proportion = (kidney_edges[0].Length() + kidney_edges[1].Length()) / kwire.Length())
        hose_points.append(hose_wire.positionAt(proportion))
    # second and possibly third variable point
    edges = []
    if not kcp_pos_y:
        edges.append(kidney_edges[3])
    edges.append(kidney_edges[4])
    kwire = cq.Wire.assembleEdges(edges)
    hose_edge = (
        cq
        .Workplane('XY', origin=(0, 0, top_pos[2]))
        .moveTo(*hose_control_points[1])
        .radiusArc(hose_control_points[2], r2)
        .val()
    )
    if not kcp_pos_y:
        length_to_point = kidney_edges[2].Length()
        proportion length_to_point / kwire.Length()
        hose_points.append(hose_wire.positionAt(proportion))
    # middle point
    hose_points.append(hose_control_points[2])
    # third variable point
    if kcp_pos_x:


    # create the final hose wire
    for point in hose_points[1:]:
        # print(f"reduced point = {point[0] - top_pos[0]}, {point[1] - top_pos[1]}")
        hose_wire = hose_wire.radiusArc((point[0], point[1]), r2)
    hose_wire = hose_wire.wire().val()
    # return cq.Workplane(kidney_wire), cq.Workplane(hose_wire)
    return kidney_wire, hose_wire


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
# r_outer = dims.vac.port.rad + dims.vac.wall_thick + dims.vac.brush.slot_width + dims.vac.wall_thick
r_outer = dims.vac.port.rad + vac_port_to_body_outer
# to get to that radius, the line must extend horizontally until
x_start = math.sqrt(r_outer ** 2 - (dims.vac.port.rad + dims.vac.wall_thick) ** 2)
# inner radius of the kidney shape
rk_inner = abs(yc) - dims.vac.port.rad - dims.vac.wall_thick
# rk_outer = rk_inner + dims.vac.port.rad + r_outer
part = (
    part
    .spline(
        [(-r_outer, yc)]
        , tangents=[(-1, 0), (0, -1)]
        , includeCurrent=True
    )
    .radiusArc((0, -body_major_radius), -r_outer)
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

# # This has to become a long pipe with a ring on the end to sit in the upper vac
# # mount
# chimney = (
#     cq
#     .Workplane('XY', origin=dims.vac.hose.plane.origin)
#     .circle(dims.vac.chimney.main_od / 2)
#     .extrude(dims.vac.chimney.height)
#     .faces('>Z')
#     .workplane()
#     .hole(dims.vac.hose.id, dims.vac.chimney.height)
# )

kidney_wire, hose_wire = kidney_and_circle_wires(dims.vac.chimney.main_od / 2 + dims.vac.wall_thick, dims.vac.hose.plane.origin, rk_inner, body_major_radius)
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
    .tangentArcPoint((-r_brush_to_port, r_brush_to_port), relative=True)
)
brush_slot = (
    cq
    .Workplane('XZ', origin=brush_slot_path.val().endPoint())
    .center(0, dims.vac.brush.slot_depth / 2)
    .rect(dims.vac.brush.slot_width, dims.vac.brush.slot_depth, centered=True)
    .sweep(brush_slot_path)
)

part = part.union(upper_vac).cut(vacuum_path).cut(brush_slot)
# del vacuum_path, upper_vac, # brush_slot_path, brush_slot
