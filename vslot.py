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
        .tag("unslotted")
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


def cbeam_dxf(length=100):
    """
    Alternate to the above method, but this one imports a dxf for the profile.
    """
    # I'm actually laughing out loud at this process.
    # create the base face and tag it as unslotted
    part = (
        cq
        .Workplane()
        .tag("base")
        .box(
            dims.outer.x, dims.base_depth, length, centered=(True, False, False)
        )
        .workplaneFromTagged("base")
        .center(dims.outer.x / 2 - dims.base_depth / 2, 0)
        .box(
            dims.base_depth, dims.outer.y, length, centered=(True, False, False)
        )
        .workplaneFromTagged("base")
        .center(-dims.outer.x / 2 + dims.base_depth / 2, 0)
        .box(
            dims.base_depth, dims.outer.y, length, centered=(True, False, False)
        )
        .tag("unslotted")
    )
    # import dxf
    imported = (
        cq.importers.importDXF('C-Beam-DXF.dxf')
        .translate((0, dims.base_depth, 0))
        .wires()
        .toPending()
        .extrude(length)
    )
    # completely replace everything I just made with the imported version, but
    # this will still preserve the unslotted tag, so I can use that in my
    # assembly constraints
    part = part.newObject(imported.objects)
    return part


cslot0 = cbeam_dxf()
