import cadquery as cq
import dims
import importlib
importlib.reload(dims)


brace = (
    cq
    .Workplane()
    .moveTo(-dims.brace.width / 2, 0)
    .vLine(-dims.bracket.thick)
    .hLineTo(dims.brace.profile1[0] - dims.chimney.mountface.width / 2)
    .lineTo(dims.brace.mount_face[0] - dims.chimney.mountface.width / 2, dims.brace.mount_face[1])
    .hLine(dims.chimney.mountface.width)
    .lineTo(dims.brace.profile1[0] + dims.chimney.mountface.width / 2, 0)
    .close()
    .extrude(dims.brace.profile1[2] + dims.chimney.mountface.height)
)
cutters = []
cutters.append(
    cq
    .Workplane('YZ')
    .moveTo(dims.brace.mount_face[1], 0)
    .lineTo(-dims.bracket.thick, dims.brace.profile1[2])
    .hLineTo(0)
    .vLineTo(0)
    .close()
    .extrude(dims.brace.width + dims.chimney.mountface.width, both=True)
)
cutters.append(
    cq
    .Workplane('YZ')
    .moveTo(dims.brace.mount_face[1], dims.chimney.mountface.height)
    .lineTo(
        -dims.bracket.thick,
        dims.brace.profile1[2] + dims.chimney.mountface.height
    )
    .hLineTo(dims.brace.mount_face[1])
    .close()
    .extrude(dims.brace.width + dims.chimney.mountface.width, both=True)
)
for cutter in cutters:
    brace = brace.cut(cutter)
del cutter
cutters = []
brace = (
    brace
    .tag('mountbase')
    .edges("|Z")
    .edges(
        cq.NearestToPointSelector((
            dims.brace.profile1[0] - dims.chimney.mountface.width / 2,
            -dims.bracket.thick,
            dims.brace.profile1[1] + dims.chimney.mountface.height / 2
        ))
    )
    .fillet(10)
    .edges("|Z")
    .edges(">(1, 1, 0)")
    .fillet(10 + dims.bracket.thick)
    .faces(">Y[1]", tag='mountbase')
    .workplane(
        centerOption='ProjectedOrigin',
        origin=(0, 0, dims.brace.profile1[2] + dims.chimney.mountface.height / 2)
    )
    .tag('bolt plane')
    .pushPoints([(-30, 0), (30, 0)])
    .cboreHole(
        dims.vac_brack.hole.diam
        , dims.vac_brack.hole.cbore_diam
        , dims.vac_brack.hole.cbore_depth
    )
    # .workplaneFromTagged('bolt plane')
    # .pushPoints([(-30, 0), (30, 0)])
    # .circle(dims.vac_brack.hole.cbore_diam / 2)
    # .cutBlind(25)
)
for sign in [-1, 1]:
    brace = (
        brace
        .faces("<Y", tag="mountbase")
        .workplane()
        .moveTo(
            sign * (dims.chimney.mountface.align.hole.diam + dims.vac.wall_thick) / 2,
            0
        )
        .circle(dims.chimney.mountface.align.hole.diam / 2)
        .cutBlind(
            -dims.chimney.mountface.align.stub.length + 0.1,
            taper=dims.chimney.mountface.align.stub.taper
        )
    )

magnet_cutter = (
    cq
    .Workplane('XZ', origin=(0, 0, 0))
    .moveTo(dims.magnet.slot.width / 2, dims.magnet.diam)
    .vLineTo(0)
    .tangentArcPoint((-dims.magnet.slot.width / 2, 0), relative=False)
    .vLineTo(dims.magnet.diam)
    .close()
    .extrude(dims.magnet.slot.thick)
    .rotate((0, 0, 0), (0, 0, 1), 180)
)
ys = [pos[1] for pos in dims.chimney.mountface.magnet.position]
y_mid = (min(ys) + max(ys)) / 2
plane = brace.faces("<Y", tag="mountbase").workplane().plane
for pos in dims.chimney.mountface.magnet.position:
    angle = 180 if (pos[1] < y_mid) else 0
    final_pos = plane.toWorldCoords((pos[0], pos[1], -dims.magnet.wall_thick))
    cutters.append(
        magnet_cutter
        .rotate((0, 0, 0), (0, 1, 0), angle)
        .translate(final_pos)
    )
    # show_object(cutters[-1])
del magnet_cutter
for cutter in cutters:
    brace = brace.cut(cutter)
del cutter
# brace = (
#     cq
#     .Workplane(
#         'XZ', origin=(dims.brace.mount_face[0], dims.brace.mount_face[1], 0)
#     )
#     .rect(
#         dims.chimney.mountface.width,
#         dims.chimney.mountface.height,
#         centered=True,
#     )
#     .copyWorkplane(cq.Workplane('XZ', origin=(dims.brace.profile1)))
#     # getting some flaky behaviour when cutting the holes, perhaps a wire goes
#     # in the wrong direction?
#     .workplane(invert=True)
#     .rect(
#         dims.chimney.mountface.width,
#         dims.chimney.mountface.height,
#         centered=True,
#     )
#     .loft()
#     .faces(">Y")
#     .workplane()
#     .rect(
#         dims.chimney.mountface.width,
#         dims.chimney.mountface.height,
#         centered=True,
#     )
#     .extrude(dims.bracket.thick)
#     .faces("<X")
#     .workplane(
#         centerOption='ProjectedOrigin',
#         origin=(0, -dims.bracket.thick / 2, dims.brace.profile1[2]),
#         invert=True,
#     )
# )
# centre = brace.val()
# extrude_length = dims.bracket.width / 2 + centre.x
# brace = (
#     brace
#     .rect(dims.bracket.thick, dims.chimney.mountface.height, centered=True)
#     .extrude(-extrude_length)
# #     .clean()
#     .faces(">Y[1]")
#     .workplane(centerOption='ProjectedOrigin', origin=(0, 0, dims.brace.profile1[2]))
#     .sphere(1)
# #     # .pushPoints([(x, 0) for x in dims.vac_brack.holes])
# #     # .cboreHole(
# #     #     dims.vac_brack.hole.diam
# #     #     , dims.vac_brack.hole.cbore_diam
# #     #     , dims.vac_brack.hole.cbore_depth
# #     # )
# )
