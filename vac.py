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
import vac_helpers as vh
importlib.reload(dims)

# make top wire
# make bottom wire
# top face is cq.Face.makeFromWire(top_wire)
# bottom face is cq.Face.makeFromWire(bottom_wire)
# vertical face is cq.Face.makeRuledSurface(top_wire, bottom_wire)
# then make shell, solid, cut

# some classes to simplify this kidney/circle shape relationship, since doing
# this functionally is doing my head in


class Vector(cq.Vector):

    def XY(self):
        return (self.x, self.y)


class Edge(cq.Edge):

    @classmethod
    def makeCirclePnts(
        cls,
        radius: float,
        start: Vector,
        end: Vector,
        pnt=Vector(0, 0, 0),
        dir=Vector(0, 0, 1),
        sense: bool = True,
    ) -> "Edge":
        """
        https://old.opencascade.com/doc/occt-7.4.0/refman/html/class_g_c___make_arc_of_circle.html#aea65b3bf21168147e6547fb725ffbf5f
        """

        def rotation_direction(trimmed_circ, direction=Vector(0, 0, 1)):
            """
            returns true if the trimmed circle (arc) is in the anti-clockwise
            direction around argument direction
            """
            start = Vector(trimmed_circ.StartPoint())
            end = Vector(trimmed_circ.EndPoint())
            product = start.cross(end)
            projection = direction.normalized().dot(product)
            # print(f"this curve has a projection of {projection}")
            return (projection >= 0)

        if not isinstance(pnt, cq.Vector):
            pnt = Vector(pnt)
        if not isinstance(dir, cq.Vector):
            dir = Vector(dir)
        axis = cq.occ_impl.shapes.gp_Ax2(
            pnt.toPnt(),
            dir.toDir(),
            (start - pnt).toDir(),
        )
        circle_gp = cq.occ_impl.shapes.gp_Circ(
            axis,
            radius
        )

        circle_geom = cq.occ_impl.shapes.GC_MakeArcOfCircle(
            circle_gp,
            start.toPnt(),
            end.toPnt(),
            sense
        ).Value()

        # need to make some checks here to see if the trimmed curve needs to be
        # reversed or not

        # if not rotation_direction(circle_geom, Vector(0, 0, -1)):
        #     circle_geom = circle_geom.Reversed()

        return cls(
            cq.occ_impl.shapes.BRepBuilderAPI_MakeEdge(circle_geom).Edge()
        )


class Arc(Edge):
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
        if not isinstance(startpoint, Vector):
            startpoint = Vector(startpoint)
        if not isinstance(endpoint, Vector):
            endpoint = Vector(startpoint)
        edge = (
            cq
            .Workplane()
            .moveTo(*startpoint.XY())
            .radiusArc(endpoint.XY(), radius)
            .val()
        )
        super().__init__(edge.wrapped)
        # wasn't aware of cq's startPoint method when originally writing this
        self.startpoint = startpoint
        self.endpoint = endpoint


class Wire(cq.Wire):
    """
    Use Wire.assembleEdges(list_of_edges) to init.
    """

    @classmethod
    def assembleEdges(cls, list_of_edges):
        # keep track of the edges
        out = super().assembleEdges(list_of_edges)
        out.list_of_edges = list_of_edges
        return out

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
            out.append(edge.Length() / self.Length())
        return out


class UpperWire:
    """
    Builds a wire to represent the upper circular edge of the ruled surface.
    """

    circle_dir = Vector(0, 0, 1)
    sense = True

    def __init__(self, centre, radius):
        if not isinstance(centre, Vector):
            centre = Vector(centre)
        self.centre = centre
        self.radius = radius
        # the signed value used for Workplane.radiusArc
        self.radiusArc_radius = radius
        self.fixed_points = [None] * 4
        self.intermediate_points = []
        for idx in range(4):
            self.intermediate_points.append([])

    def calc_radius(self, point):
        return (point - self.centre).Length

    def wire(self):
        """
        Returns the cq.Wire.
        """
        edges = []
        points = self.points()
        points.append(points[0])
        out = (
            cq
            .Workplane('XY', origin=Vector(0, 0, self.centre.z))
            .moveTo(points[0].x, points[0].y)
        )
        for point in points[1:]:
            out = out.radiusArc((point.x, point.y), self.radiusArc_radius)
        out = out.wire().val()
        return out

    def edge_idx(self, idx: int):
        """
        Generates one of the four fixed wires, not including intermediate
        points.
        idx is an integer between 0 and 3 inclusive.
        """
        start = self.fixed_points[idx]
        end = self.fixed_points[(idx + 1) % 4]
        out = (
            cq
            .Workplane('XY', origin=Vector(0, 0, self.centre.z))
            .moveTo(start.x, start.y)
            .radiusArc((end.x, end.y), self.radiusArc_radius)
            .val()
        )
        assert abs((out.startPoint() - self.fixed_points[idx]).Length) < 1e-4
        assert abs((out.endPoint() - self.fixed_points[(idx + 1) % 4]).Length) < 1e-4
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
                # print(f"extending by {self.intermediate_points[idx]}")
                out.extend(self.intermediate_points[idx])
        return out

    def add_fixed_point(self, idx, point):
        """
        Adds one of the 4 fixed points.
        """
        # this point should be on the same z plane as centre
        if abs(point.z - self.centre.z) > 1e-4:
            point = Vector(point.x, point.y, self.centre.z)
        self.check_radius(point)
        self.fixed_points[idx] = point

    def check_radius(self, point):
        """
        Check that point has the correct radius
        """
        vector_centre_to_point = point - self.centre
        if abs(vector_centre_to_point.Length - self.radius) > 1e-4 * self.radius:
            raise ValueError(
                f"Point {point} with coords {(point.x, point.y, point.z)} " +
                f"is too far from centre {self.centre} " +
                f"to have radius {self.radius}"
            )

    def add_intermediate_point(self, idx, proportion):
        """
        Adds a point to wire idx at proportion.
        """
        self.check_fixed_points()
        edge = self.edge_idx(idx)
        new_point = edge.positionAt(proportion)
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
        # return Wire.combine(self.wires)[0]
        list_of_edges = []
        for wire in self.wires:
            list_of_edges.extend(wire.list_of_edges)
        return Wire.assembleEdges(list_of_edges)



# I think I would actually prefer the two following functions as a class, init
# from top_rad, top_pos, inner_kidney_rad, outer_kidney_rad and do the
# calculations in methods. A job for the next interation.
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
    For some fucking reason I can't get the correct points out of this method.
    TODO Consider rewriting to use:
        http://jwilson.coe.uga.edu/EMAT6680Su06/Byrd/Assignment
        Six/RBAssignmentSix.html
    """
    if not isinstance(top_pos, Vector):
        top_pos = Vector(top_pos)
    if not isinstance(port_pos, Vector):
        port_pos = Vector(port_pos)
    x1, y1 = port_pos.x, port_pos.y
    r1 = port_rad
    x2, y2 = top_pos.x, top_pos.y
    r2 = top_rad
    gamma = -math.atan((y2 - y1) / (x2 - x1))
    beta = math.asin((r2 - r1) / math.sqrt(
        (x2 - x1) ** 2 + (y2 - y1) ** 2
    ))
    # create results for both the plus and minus case of beta
    results = {}
    for name, sign in zip(["pos", "neg"], [1, -1]):
        alpha = gamma - sign * beta
        results[name] = {
            "x3": x1 + sign * r1 * math.sin(alpha),
            "y3": y1 + sign * r1 * math.cos(alpha),
            "x4": x2 + sign * r2 * math.sin(alpha),
            "y4": y2 + sign * r2 * math.cos(alpha),
        }
    # need to find the result on the correct side
    # this could be done in like 4 lines, but would be harder to read...
    if side.lower() == "+x":
        if results["pos"]["x3"] > results["neg"]["x3"]:
            answer = "pos"
        else:
            answer = "neg"
    elif side.lower() == "-x":
        if results["pos"]["x3"] < results["neg"]["x3"]:
            answer = "pos"
        else:
            answer = "neg"
    elif side.lower() == "+y":
        if results["pos"]["y3"] > results["neg"]["y3"]:
            answer = "pos"
        else:
            answer = "neg"
    elif side.lower() == "-y":
        if results["pos"]["y3"] < results["neg"]["y3"]:
            answer = "pos"
        else:
            answer = "neg"
    else:
        raise ValueError(f"side {side} is not recognised")

    answer0 = results[answer]
    c_point = Vector(answer0["x4"], answer0["y4"], top_pos.z)
    k_point = Vector(answer0["x3"], answer0["y3"], 0)
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
    top_pos = Vector(top_pos)
    top_z = top_pos.z
    top_pos = Vector(top_pos.x, top_pos.y)
    if side.lower() == "+y":
        scale = inner_kidney_rad
        sign = -1
    else:
        scale = outer_kidney_rad
        sign = 1
    k_point = Vector(top_pos.normalized().multiply(scale))
    c_point = top_pos + top_pos.normalized().multiply(sign * top_rad)
    c_point = Vector(c_point.x, c_point.y, top_z)
    return c_point, k_point


def kidney_and_circle_wires2(
        top_rad,
        top_pos,
        bot_inner_rad,
        bot_outer_rad,
        ):
    port_rad = (bot_outer_rad - bot_inner_rad) / 2
    port_pos_x_axis = Vector((bot_inner_rad + bot_outer_rad) / 2, 0)
    port_pos_y_axis = Vector(0, -(bot_inner_rad + bot_outer_rad) / 2)
    # calculate tangential points
    circle_tangent_point_0, kidney_tangent_point_0 = tangential_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos_x_axis,
        "+X"
    )
    circle_tangent_point_1, kidney_tangent_point_1 = tangential_points(
        top_rad,
        top_pos,
        port_rad,
        port_pos_y_axis,
        "-Y"
    )

    # calculate control points
    circle_normal_point_inner, kidney_normal_point_inner = normal_points(
        top_rad,
        top_pos,
        bot_inner_rad,
        bot_outer_rad,
        "+Y"
    )
    circle_normal_point_outer, kidney_normal_point_outer = normal_points(
        top_rad,
        top_pos,
        bot_inner_rad,
        bot_outer_rad,
        "-Y"
    )

    # create kidney shape wires
    kidney_loop = Loop()
    # wire0 goes from the inner normal to tangent 0
    arc0 = Arc(
        startpoint=kidney_normal_point_inner,
        endpoint=Vector(bot_inner_rad, 0),
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
            endpoint=Vector(bot_outer_rad, 0),
            radius=port_rad
        )
        edges0 = [arc0, arc1]
        edges1 = [arc2]
    else:
        # up to the radius change
        arc1 = Arc(
            startpoint=arc0.endpoint,
            endpoint=Vector(bot_outer_rad, 0),
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
    wire1 = Wire.assembleEdges(edges1)
    kidney_loop.wires.append(wire1)
    # wire2 goes from the outer normal point to the second tangential point
    if kidney_tangent_point_1.x > 0:
        # up to tangent_point_1
        arc4 = Arc(
            startpoint=arc3.endpoint,
            endpoint=kidney_tangent_point_1,
            radius=bot_outer_rad,
        )
        edges2 = [arc4]
        arc5 = Arc(
            startpoint=arc4.endpoint,
            endpoint=Vector(0, -bot_outer_rad),
            radius=bot_outer_rad,
        )
        edges3 = [arc5]
    else:
        # up to the radius change
        arc4 = Arc(
            startpoint=arc3.endpoint,
            endpoint=Vector(0, -bot_outer_rad),
            radius=bot_outer_rad,
        )
        # up to tangent_point_1
        arc5 = Arc(
            startpoint=arc4.endpoint,
            endpoint=kidney_tangent_point_1,
            radius=port_rad,
        )
        edges2 = [arc4, arc5]
        edges3 = []
    wire2 = Wire.assembleEdges(edges2)
    kidney_loop.wires.append(wire2)
    arc6 = Arc(
        startpoint=arc5.endpoint,
        endpoint=Vector(0, -bot_inner_rad),
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
    for idx, kwire in enumerate(kidney_loop.wires):
        for proportion in kwire.proportions():
            circle_loop.add_intermediate_point(idx, proportion)
    return kidney_loop.wire(), circle_loop.wire()

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

kidney_wire, hose_wire = kidney_and_circle_wires2(
    dims.vac.hose.id / 2,
    Vector(dims.vac.hose.plane.origin),
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

kidney_wire, hose_wire = kidney_and_circle_wires2(
    dims.vac.chimney.main_od / 2 + dims.vac.wall_thick,
    dims.vac.hose.plane.origin,
    rk_inner,
    body_major_radius
)
vert_face = cq.Face.makeRuledSurface(kidney_wire, hose_wire)

bottom_face = cq.Face.makeFromWires(kidney_wire)
reversed_hose_wire = Edge(hose_wire.wrapped.Reversed())
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
