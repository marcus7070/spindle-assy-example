import importlib
import cadquery as cq
import dims
importlib.reload(dims)

bracket = (
    cq
    .Workplane("XZ")
    .moveTo(dims.vac_brack.x_centre, 0)
    .box(
        dims.vac_brack.x
        , dims.vac_brack.z
        , dims.vac_brack.y
        , centered=(True, True, False)
    )
    .faces("<Y")
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, 0))
    .pushPoints([(x, 0) for x in dims.vac_brack.holes])
    .cboreHole(
        dims.vac_brack.hole.diam
        , dims.vac_brack.hole.cbore_diam
        , dims.vac_brack.hole.cbore_depth
    )
)

cutters = []
for pos in dims.magnet.positions:
    selector = ">Z" if pos[1] >= 0 else "<Z"
    cut_depth = dims.vac_brack.z / 2 - max([y for _, y in dims.magnet.positions])
    temp = (
        bracket
        .faces(selector)
        .workplane(
            centerOption='ProjectedOrigin'
            , origin=(
                pos[0]
                , -dims.vac_brack.y + dims.magnet.wall_thick + dims.magnet.slot.thick / 2
                , 0
            )
        )
    )
    assert abs(cut_depth) > 1e-2, "near zero cut depth, you've fucked up"
    cutters.append(
        temp
        .rect(dims.magnet.slot.width, dims.magnet.slot.thick, centered=True)
        .extrude(-cut_depth, combine=False)
    )
    cutters.append(
        temp
        .workplane(offset=-cut_depth)
        .move(0, -dims.magnet.slot.thick / 2)
        .rect(dims.magnet.slot.width / 2, dims.magnet.slot.thick, centered=False)
        .revolve(axisEnd=(0, 1), combine=False)
    )
for cutter in cutters:
    bracket = bracket.cut(cutter)
del cutter
