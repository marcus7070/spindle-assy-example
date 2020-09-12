import importlib
import cadquery as cq
import dims
importlib.reload(dims)


clamp = (
    cq
    .Workplane()
    .tag('base')
    .box(
        dims.clamp.lower[0]
        , dims.clamp.lower[1]
        , dims.clamp.dims[2]
        , centered=(True, False, True)
    )
    .workplaneFromTagged('base')
    .center(0, dims.clamp.lower[1])
    .tag('lower')
    .box(
        dims.clamp.upper[0]
        , dims.clamp.upper[1]
        , dims.clamp.dims[2]
        , centered=(True, False, True)
    )
    .workplaneFromTagged('lower')
    .center(0, dims.clamp.upper[1])
    .vLine(-1)  # having some trouble with this shape not fusing with the base
    # shape and messing up the hole later
    .hLine(dims.clamp.shoulder.outer_x)
    .vLine(1)
    .lineTo(dims.clamp.shoulder.inner_x, dims.clamp.shoulder.delta_y)
    .hLineTo(0)
    .mirrorY()
    .extrude(dims.clamp.dims[2] / 2, both=True)
)
edges = []
for side in [-1, 1]:
    for y0 in [0, dims.clamp.lower[1], dims.clamp.lower[1] + dims.clamp.upper[1]]:
        edges.append(
            clamp.edges("|Z").edges(cq.NearestToPointSelector((
                side * dims.clamp.dims[0] / 2
                , y0
                , 0
            ))).val()
        )

clamp = (
    clamp
    .newObject(edges)
    .chamfer(dims.clamp.lower[0] / 2 - dims.clamp.upper[0] / 2 - 1e-3)
    .workplaneFromTagged('base')
    .workplane(offset=dims.clamp.dims[2] / 2 + 1)
    .center(dims.clamp.hole.pos[0], dims.clamp.hole.pos[1])
    .hole(dims.clamp.hole.diam, clean=False)
    .faces("<Y")
    .workplane()
    .rect(*dims.clamp.bolt.spacing)
    .vertices()
    .hole(9.3)
)

obj = cq.Workplane().box(1, 1, 1).val()
