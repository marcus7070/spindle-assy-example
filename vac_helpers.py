"""
Some helper functions and classes for vac.py.
"""

import cadquery as cq
import math


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


# some classes to simplify this kidney/circle shape relationship, since doing
# this functionally is doing my head in


class Vector(cq.Vector):

    def XY(self):
        return (self.x, self.y)


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
        Code is a bit lazy, but whatever, it works.
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
        # should have just used the method Wire.Edges(), but this now works so
        # I'm not going to touch it again.
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
            # Am I sure these edges are sequential?
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


def kidney_and_circle_wires(
        top_rad,
        top_pos,
        bot_inner_rad,
        bot_outer_rad,
        ):
    """
    Start with the 4 known points, the tangential points and normal points. We
    want to finish with 4 wires per shape going between these 4 points. But the
    kidney shaped wire also has 4 changes in radius, meaning that it must
    consist of 8 edges. To get the correct ruledSurface, make the circle wire
    have the same number of edges as the kidney wire and the start/endpoints at
    the same proportions.
    """
    if not isinstance(top_pos, Vector):
        top_pos = Vector(top_pos)
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
