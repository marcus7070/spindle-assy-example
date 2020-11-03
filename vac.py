"""
3d printed part, has the vacuum hose inserted and duct taped to it, attached
with magnets to vac_brack, and has a tube going up to vac_hangar.
Origin will be bottom center of the spindle's collet nut.
"""


import importlib
import math
import cadquery as cq
import OCP
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


class Arc(cq.Edge):
    """
    All the edges in the kidney shape and circular shape are made of arcs. This
    class represents an arc.
    """

    def __init__(
            self,
            startpoint=None,
            endpoint=None,
            radius=None):
        """
        Creates an arc between startpoint and endpoint.
        """
        edge = (
            cq
            .Workplane()
            .moveTo(startpoint)
            .radiusArc(endpoint, radius)
            .val()
        )
        super().__init__(edge.wrapped)
        self.startpoint = startpoint
        self.endpoint = endpoint


class Wire(cq.Wire):
    """
    Use Wire.assembleEdges(list_of_edges) to init.
    """
#
#     def add_intermediate_points(self, list_of_proportions):
#         """
#         Creates intermediate points along this wire. Proportion is a
#         float between 0 and 1. Intended to work with the result of
#         `Wire.proportions` from a different wire.
#         """
#         for p in list_of_proportions:
#             self._add_intermediate_point(p)
#
#     def _add_intermediate_point(self, proportion):
#         # get the parameter corresponding to this proportion
#         parameter = self.paramAt(proportion)
#         # get the edge corresponding to this parameter
#         curve = self._geomAdaptor()
#         new_edge_0 = OCP.TopoDS.TopoDS_Edge()
#         edge_parameter = curve.Edge(parameter, new_edge_0)
#         if isinstance(edge_parameter, tuple):
#             edge_parameter = edge_parameter[0]
#         # split the edge in two
#         copier = OCP.BRepBuilderAPI.BRepBuilderAPI_Copy(new_edge_0)
#         new_edge_1 = copier.Shape()
#         # BRepAdaptor_Curve has a trim function, try that
#         new_edge_0_geom = cq.Edge(new_edge_0)._geomAdaptor()
#         new_edge_1_geom = cq.Edge(new_edge_1)._geomAdaptor()
#         new_edge_0 = new_edge_0_geom.Trim(curve.FirstParameter(), edge_parameter, 1e-5)
#         new_edge_1 = new_edge_1_geom.Trim(edge_parameter, curve.LastParameter(), 1e-5)
#         # create new list of edges
#         # reinsert the edge into a list of this object's edges
#         self.wrapped = self.assembleEdges(list_of_edges).wrapped
#         # Begining to think I can't do this. I need to start with an abstract
#         # cicle and subdivide it, it's not worth starting with a wire and
#         # working backwards.

    def proportions(self):
        """
        Calculates the proportion along this wire that the intermediate points
        are.
        Returns a list of floats between 0 and 1.
        """
        out = []
        cumulative_length = 0.0
        for edge in self.Edges()[:-1]:
            cumulative_length += edge.Length()
            out.append(edge_length / self.Length())


class UpperWire:
    """
    Builds a wire to represent the upper circular edge of the ruled surface.
    """

    def __init__(self, centre, radius):
        if not isinstance(centre, cq.Vector):
            centre = cq.Vector(centre)
        self.centre = centre
        self.radius = radius
        self.zero_vector = cq.Vector(radius, 0, 0)
        self.fixed_points = [None] * 4
        self.intermediate_points = [[]] * 4

    def wire(self):
        """
        Returns the cq.Wire.
        """
        edges = []
        points = self.points()
        points.append(self.points[-1])
        points.extend(self.points)
        for a1, a2 in zip(self.points[:-1], self.points[1:]):
            edges.append(cq.Edge.makeCircle(self.radius, self.centre, a1, a2))
        out = cq.Wire.assembleEdges(edges)
        return out

    def points(self):
        """
        Returns a list of the points for the final wire.
        """
        self.check_fixed_points()
        out = []
        for idx in range(4):
            out.append(self.fixed_points[idx])
            if self.intermediate_points[idx]:
                out.extend(self.intermediate_points[idx])
        return out

    def add_fixed_point(self, idx, point):
        """
        Adds one of the 4 fixed points.
        """
        angle = self.convert_to_angle(point)
        self.fixed_points[idx] = angle

    def convert_to_angle(self, point):
        """
        Converts a point to an angle as used in the points list. Needs to be in
        degrees, as used by the wire method.
        """
        vector_centre_to_point = point - self.centre
        if vector_centre_to_point.Length() > 1e-4 * self.radius:
            raise ValueError(
                f"Point {point} with coords {point.XYZ()} " +
                f"is too far from centre {self.centre} " +
                f"to have radius {self.radius}"
            )
        angle = self.zero_vector.Angle(vector_centre_to_point)
        return angle / cq.occ_impl.shapes.DEG2RAD

    def add_intermediate_point(self, idx, proportion):
        """
        Adds a point to wire idx at proportion.
        """
        self.check_fixed_points()
        edge_start = self.fixed_points[idx]
        edge_end = self.fixed_points[(idx + 1) % 4]
        new_point = edge_start + proportion * ((edge_end - edge_start) % 360)
        self.intermediate_points[idx].append(new_point)

    def check_fixed_points(self):
        if not all(self.fixed_points):
            raise RuntimeError(
                'Not all fixed points were supplied before ' +
                'calling a method that needed them'
            )


class Loop:
    """
    ~~Either the kidney shape or the circular shape.~~
    Now just the kidney shape.
    """

    def __init__(self, wires=None):
        if wires is None:
            wires = []
        self.wires = wires

    def check(self):
        # check that endpoint of one arc is the startpoint of the next
        # sugggest itertools.cycle for the looping aspect
        raise NotImplementedError('TODO Loop.check()')

    def wire(self):
        """
        Returns all the wires connected into a single cq.Wire
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
    x1, y1 = port_pos.x, port_pos.y
    x2, y2 = top_pos.x, top_pos.y
    gamma = -math.atan((y2 - y1) / (x2 - x1))
    beta = math.asin((r2 - r1) / math.sqrt(
        (x2 - x1) ** 2 + (y2 - y1) ** 2
    ))
    results = {}
    for name, beta0 in zip(["pos", "neg"], [beta, -beta]):
        alpha = gamma - beta0
        results[name] = {
            "x3": x1 + r1 * math.sin(alpha),
            "y3": y1 + r1 * math.cos(alpha),
            "x4": x2 + r2 * math.sin(alpha),
            "y4": y2 + r2 * math.cos(alpha),
        }



    return c_point, k_point


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
    top_pos = cq.Vector(top_pos)
    if side.lower() == "+y":
        scale = inner_kidney_rad
        sign = -1
    else:
        scale = outer_kidney_rad
        sign = 1
    k_point = top_pos.normalized().multiply(scale)
    c_point = top_pos + sign * top_pos.normalized().multiply(top_rad)
    return c_point, k_point


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
        "+X"
    )
    circle_tangent_point_0 = cq.Vector(
        *circle_tangent_coords_0,
        z=top_pos[2],
    )
    kidney_tangent_point_0 = cq.Vector(
        *kidney_tangent_coords_0,
        z=0,
    )
    circle_tangent_coords_1, kidney_tangent_coords_1 = tangential_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos,
        "-Y"
    )
    circle_tangent_point_1 = cq.Vector(
        *circle_tangent_coords_1,
        z=top_pos[2],
    )
    kidney_tangent_point_1 = cq.Vector(
        *kidney_tangent_coords_1,
        z=0,
    )

    # calculate control points
    circle_normal_coords_inner, kidney_normal_coords_inner = normal_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos,
        "+Y"
    )
    circle_normal_point_inner = cq.Vector(
        *circle_normal_coords_inner,
        z=top_pos[2],
    )
    kidney_normal_point_inner = cq.Vector(
        *kidney_normal_coords_inner,
        z=0,
        control_point=True
    )
    circle_normal_coords_outer, kidney_normal_coords_outer = normal_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos,
        "-Y"
    )
    circle_normal_point_outer = cq.Vector(
        *circle_normal_coords_outer,
        z=top_pos[2],
    )
    kidney_normal_point_outer = cq.Vector(
        *kidney_normal_coords_outer,
        z=0,
    )

    # create kidney shape wires
    kidney_loop = Loop()
    port_rad = (bot_outer_rad - bot_inner_rad) / 2
    # wire0 goes from the inner normal to tangent 0
    arc0 = Arc(
        startpoint=kidney_normal_point_inner,
        endpoint=Point(x=bot_inner_rad, y=0),
        radius=-bot_inner_rad,
    )
    if kidney_tangent_point_0.y > 0:
        # up to tangent_point_0
        arc1 = Arc(
            startpoint=arc0.endpoint,
            endpoint=kidney_tangent_point_0,
            radius=port_rad,
        )
        # up to the radius change, this belongs in wire1
        arc2 = Arc(
            startpoint=arc1.endpoint,
            endpoint=Point(x=bot_outer_rad, y=0),
            radius=port_rad
        )
        edges0 = [arc0, arc1]
        edges1 = [arc2]
    else:
        # up to the radius change
        arc1 = Arc(
            startpoint=arc0.endpoint,
            endpoint=Point(x=bot_outer_rad, y=0),
            radius=port_rad
        )
        # up to tangent_point_0, still in wire0
        arc2 = Arc(
            startpoint=arc1.endpoint,
            endpoint=kidney_tangent_point_0,
            radius=port_rad
        )
        edges0 = [arc0, arc1, arc2]
        edges1 = []
    wire0 = Wire.assembleEdges(edges0)
    kidney_loop.wires.append(wire0)
    # wire1 goes from the first tangential point to the second normal point
    # edges1 might already have an arc in it
    arc3 = Arc(
        startpoint=arc2.endpoint,
        endpoint=kidney_normal_point_outer,
        radius=bot_outer_rad,
    )
    edges1.append(arc3)
    wire1 = Wires.assembleEdges(edges1)
    kidney_loop.wires.append(wire1)
    # wire2 goes from the outer normal point to the second tangential point
    if kidney_tangent_point_1.x > 0:
        # up to tangent_point_1
        arc4 = Arc(
            startpoint=arc3.endpoint,
            endpoint=tangent_point_1,
            radius=bot_outer_rad,
        )
        edges2 = [arc4]
        arc5 = Arc(
            startpoint=arc4.endpoint,
            endpoint=Point(x=0, y=-bot_outer_rad),
            radius=bot_outer_rad,
        )
        edges3 = [arc5]
    else:
        # up to the radius change
        arc4 = Arc(
            startpoint=arc3.endpoint,
            endpoint=Point(x=0, y=-bot_outer_rad),
            radius=bot_outer_rad,
        )
        # up to tangent_point_1
        arc5 = Arc(
            startpoint=arc4.endpoint,
            endpoint=tangent_point_1,
            radius=port_rad,
        )
        edges2 = [arc4, arc5]
        edges3 = []
    wire2 = Wire.assembleEdges(edges2)
    kidney_loop.wires.append(wire2)
    arc6 = Arc(
        startpoint=arc5.endpoint,
        endpoint=Point(x=0, y=-bot_inner_rad),
        radius=port_rad,
    )
    edges3.append(arc6)
    arc7 = Arc(
        startpoint=arc6.endpoint,
        endpoint=arc0.startpoint,
        radius=-bot_inner_rad,
    )
    edges3.append(arc7)
    wire3 = Wire.assembleEdges(edges3)
    kidney_loop.wires.append(wire3)
    # map points onto circular arc
    circle_loop = UpperWire(top_pos, top_rad)
    pnts = [
        circle_normal_point_inner,
        circle_tangent_point_0,
        circle_normal_point_outer,
        circle_tangent_point_1,
    ]
    for idx, pnt in enumerate(pnts):
        circle_loop.add_fixed_point(idx, pnt)
    for idx, kwire in kidney_loop.wires():
        for proportion in kwire.proportions():
            circle_loop.add_intermediate_point(idx, proportion)
    return kidney_loop.wire(), circle_loop.wire()


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
