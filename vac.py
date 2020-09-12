"""
3d printed part, has the vacuum hose inserted and duct taped to it, attached
with magnets to vac_brack, and has a duct going from the vacuum hose to the
work.
Origin will be bottom center of the spindle's collet nut.
    * Define the bottom face, then top face, then loft to form majority of
    body.
    * Offset the bottom face in by the wall thickness, then loft to the vacuum
    hose ID to form the duct.
"""


import importlib
import math
import cadquery as cq
import dims
importlib.reload(dims)


upper_spline = [
    cq.Vector(
        dims.vac.hose.plane.origin[0] + dims.vac.hose.socket.od / 2 + 2
        , dims.vac.hose.plane.origin[1]
    ), cq.Vector(
        dims.vac.hose.plane.origin[0]
        , dims.vac.hose.plane.origin[1] - dims.vac.hose.socket.od / 2 - 2
    ), cq.Vector(
        dims.vac.mount_face.x_max * math.cos(math.radians(180 + 45))
        , dims.vac.mount_face.x_max * math.sin(math.radians(180 + 45))
    )
]
lower_spline = [
    (upper_spline[0] + cq.Vector(dims.vac.mount_face.x_max, 0, 0)) / 2
    , (upper_spline[1] + cq.Vector(-dims.vac.hose.socket.od / 2, -dims.vac.hose.socket.od / 2, 0)) / 2
    , upper_spline[2]
]

part = (
    cq
    .Workplane()
    .moveTo(dims.vac.mount_face.x_min, dims.vac.mount_face.y)
    .hLineTo(dims.vac.mount_face.x_max)
    .lineTo(lower_spline[0].x, lower_spline[0].y)
)
# # an arc around the spindle axis with radius dims.vac.mount_face.x_max
start_tangent = part.val().tangentAt(1)
end_tangent = cq.Vector(-1, 1, 0).normalized()
part = (
    part
    .spline(
        listOfXYTuple=lower_spline
        , tangents=(start_tangent, end_tangent)
    )
)
radius = dims.vac.inner_rad
endangle = math.radians(180 + 45)
endpoint = (
    radius * math.cos(endangle)
    , radius * math.sin(endangle)
)
part = (
    part
    .lineTo(*endpoint)
    .threePointArc(
        (radius, 0)
        , (endpoint[0], -endpoint[1])
    )
    .close()
)
part = (
    part
    .copyWorkplane(cq.Workplane("XY", origin=(0, 0, dims.vac.z)))
    .moveTo(dims.vac.mount_face.x_min, dims.vac.mount_face.y)
    .hLineTo(dims.vac.mount_face.x_max)
    .lineTo(upper_spline[0].x, upper_spline[0].y)
)
start_tangent = part.val().tangentAt(1)
end_tangent = cq.Vector(-1, 1, 0).normalized()
part = (
    part
    .spline(
        listOfXYTuple=upper_spline
        , tangents=(start_tangent, end_tangent)
    )
    .lineTo(
        dims.vac.inner_rad * math.cos(math.radians(180 + 45))
        , dims.vac.inner_rad * math.sin(math.radians(180 + 45))
    )
    .threePointArc(
        (dims.vac.inner_rad, 0)
        , (
            dims.vac.inner_rad * math.cos(math.radians(180 + 45))
            , -dims.vac.inner_rad * math.sin(math.radians(180 + 45))
        )
    )
    .close()
    .loft()
    .tag('base')
    .faces(">Z")
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, 0))
    .hole(dims.spindle.bearing_cap.diam + 2, dims.spindle.bearing_cap.height + 2)
    .copyWorkplane(cq.Workplane("XY"))
    .transformed(offset=dims.vac.hose.plane.origin)
    .circle(dims.vac.hose.socket.od / 2)
    .extrude(dims.vac.hose.insertion)
    .faces(">Z")
    .workplane()
    .tag('hose_bottom')
    .hole(dims.vac.hose.od, dims.vac.hose.insertion - dims.vac.wall_thick)
    .workplaneFromTagged('hose_bottom')
    .hole(dims.vac.hose.id, dims.vac.hose.insertion)
    .workplaneFromTagged('hose_bottom')
    .polygon(4, dims.vac.hose.socket.od)
    .extrude(dims.vac.hose.tape_width)
    .faces(">Z")
    .workplane()
    .hole(dims.vac.hose.od + 2, dims.vac.hose.tape_width)
)

vac_path = (
    cq
    .Workplane()
    .moveTo(dims.vac.mount_face.x_max, dims.vac.mount_face.y)
    .lineTo(lower_spline[0].x, lower_spline[0].y)
)
# # an arc around the spindle axis with radius dims.vac.mount_face.x_max
start_tangent = vac_path.val().tangentAt(1)
end_tangent = cq.Vector(-1, 1, 0).normalized()
vac_path = (
    vac_path
    .spline(
        listOfXYTuple=lower_spline
        , tangents=(start_tangent, end_tangent)
    )
)
radius = dims.vac.inner_rad
endangle = math.radians(180 + 45)
endpoint = (
    radius * math.cos(endangle)
    , radius * math.sin(endangle)
)
vac_path = (
    vac_path
    .lineTo(*endpoint)
)
endangle = math.radians(45)
vac_path = (
    vac_path
    .threePointArc(
        (radius, 0)
        , (radius * math.cos(endangle), radius * math.sin(endangle))
    )
    .close()
    .offset2D(-dims.vac.wall_thick)
    .copyWorkplane(cq.Workplane("XY"))
    .transformed(offset=dims.vac.hose.plane.origin)
    .circle(dims.vac.hose.id / 2)
    .loft()
)
part = (
    part
    .cut(vac_path)
    .faces(">Y")
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, dims.vac.z / 2))
    .pushPoints([(-pos, 0) for pos in dims.vac_brack.holes])
    .circle(dims.vac_brack.hole.cbore_diam / 2 - 0.1)
    .extrude(dims.vac_brack.hole.cbore_depth - 2, taper=10)
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
outer_cutter = (
    cq
    .Workplane()
    .moveTo(dims.vac.hose.plane.origin[0] + dims.vac.hose.socket.od / 2 + 1e-4, 20)
    .vLineTo(upper_spline[0].y)
    .radiusArc((
            dims.vac.hose.plane.origin[0]
            , dims.vac.hose.plane.origin[1] - dims.vac.hose.socket.od / 2 - 1e-4
        )
        , dims.vac.hose.socket.od / 2 + 1e-4)
    .hLine(-100)
    .vLine(-20)
    .hLine(200)
    .close()
    .extrude(dims.vac.z + 5)
)
# cutters.append(outer_cutter)  # removes the top surface, fuck it
for cutter in cutters:
    part = part.cut(cutter)
del cutter, temp, vac_path, outer_cutter
