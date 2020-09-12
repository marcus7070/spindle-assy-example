from types import SimpleNamespace as d
import cadquery as cq

dims = d()
dims.outer = d()
dims.outer.x = 80
dims.outer.y = 40
dims.base_depth = 20


def cslot(length=100):
    out = (
        cq
        .Workplane()
        .tag("base")
        .box(dims.outer.x, dims.base_depth, length, centered=(True, False, False))
        .workplaneFromTagged("base")
        .center(dims.outer.x / 2 - dims.base_depth / 2, 0)
        .box(dims.base_depth, dims.outer.y, length, centered=(True, False, False))
        .workplaneFromTagged("base")
        .center(-dims.outer.x / 2 + dims.base_depth / 2, 0)
        .box(dims.base_depth, dims.outer.y, length, centered=(True, False, False))
    )
    points = []
    for idx in range(4):
        points.append((
            -dims.outer.x / 2 + dims.base_depth / 2 + idx * dims.base_depth  # x
            , 0  # y
            , 0  # rotation
        ))
    for side in [-1, 1]:
        for idx in range(2):
            points.append((
                side * dims.outer.x / 2
                , dims.base_depth / 2 + idx * dims.base_depth
                , 180 - 90 * side
            ))
    for xval, yval, rot in points:
        out = out.cut(
        # out = (
            cq
            .Workplane()
            .center(xval, yval)
            .tag("centered")
            .hLine(9.16 / 2)
            .polarLine(4, 45 + 90)
            .hLineTo(0)
            .mirrorY()
            .extrude(length)
            .workplaneFromTagged("centered")
            .center(0, 1.8 + 1.5 / 2)
            .rect(11, 1.5, centered=True)
            .extrude(length)
            .workplaneFromTagged("centered")
            .center(0, 1.8 + 4.3 / 2)
            .rect(6.5, 4.3, centered=True)
            .extrude(length)
            .edges("|Z")
            .edges(cq.NearestToPointSelector((xval + 6.5 / 2, yval + 1.8 + 1.5, 0)))
            .chamfer(2)
            .edges("|Z")
            .edges(cq.NearestToPointSelector((xval - 6.5 / 2, yval + 1.8 + 1.5, 0)))
            .chamfer(2)
            .rotate((xval, yval, 0), (xval, yval, 1), rot)
        )
    return out


cslot0 = cslot()
