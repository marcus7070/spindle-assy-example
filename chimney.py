import cadquery as cq
import dims
import importlib
importlib.reload(dims)

# this chimney should be a sweep over a set of profiles. The outer edge should
# be a straight line, the inner edge should curve quite a bit so that it avoids
# the clamp.

# base
# midprofile
# mount-base
# top

profiles = (
    cq
    .Workplane()
    # oh dear god I have to rewrite the .workplane method soon, this is hideous
    .tag('0')
    # bottom
    .center(0, dims.chimney.base.od / 2)
    .tag('1')
    .circle(dims.chimney.base.od / 2)
    # straight section for the lip to be cut into
    .extrude(dims.chimney.base.step_z)
    # base of the taper
    .faces(">Z")
    # for some reason the following gets the wrong radius circle!
    # .edges()
    # .toPending()
    .workplane(centerOption='ProjectedOrigin', origin=(0, 0, 0))
    .center(0, dims.chimney.base.od / 2)
    .tag('2')
    .circle(dims.chimney.base.od / 2)
    # mid profile for tapering in to clear the bracket
    .workplaneFromTagged('0')
    .workplane(
        centerOption='ProjectedOrigin',
        origin=(0, 0, 0),
        offset=dims.chimney.midprofile.z
    )
    .center(0, dims.chimney.midprofile.od / 2)
    .tag('3')
    .circle(dims.chimney.midprofile.od / 2)
    # continue tapering in to the base of the mount
    .workplaneFromTagged('0')
    .workplane(
        centerOption="ProjectedOrigin",
        origin=(0, 0, 0),
        offset=dims.chimney.mountbase.z
    )
    .center(0, dims.chimney.mountbase.od / 2)
    .tag('4')
    .circle(dims.chimney.mountbase.od / 2)
)

path = (
    cq
    .Workplane('XZ')
    .moveTo(0, dims.chimney.base.step_z)
    .vLineTo(dims.chimney.mountbase.z)
)

chimney = (
    profiles
    .sweep(path, multisection=True)
    .workplaneFromTagged('0')
    .workplane(
        centerOption="ProjectedOrigin",
        origin=(0, 0, 0),
        offset=dims.chimney.mountbase.z
    )
    .move(0, dims.chimney.mountbase.od / 2)
    .circle(dims.chimney.mountbase.od / 2)
    .extrude(dims.chimney.top.z - dims.chimney.mountbase.z)
)

# mounting face
chimney = (
    chimney
    .copyWorkplane(
        cq.Workplane('YZ', origin=(0, 0, dims.chimney.mountface.origin[2]))
    )
    .moveTo(dims.chimney.mountface.origin[1], dims.chimney.mountface.height / 2)
    .hLineTo(dims.chimney.top.od / 2 + 15)  # adjust to get underside slope to the correct point
    .vLine(dims.chimney.mountbase.z - dims.chimney.mountface.origin[2])
    .lineTo(dims.chimney.mountface.origin[1], -dims.chimney.mountface.height / 2)
    .close()
    .extrude(dims.chimney.mountface.width / 2, both=True)
    .tag('mountbase')
    .faces(">Y")
    .workplane()
    # .pushPoints(
    #     [(
    #         sign * (dims.chimney.mountface.align.hole.diam + dims.vac.wall_thick / 2),
    #         0
    #     ) for sign in [-1, 1]]
    # )
)
for sign in [-1, 1]:
    chimney = (
        chimney
        .faces(">Y", tag="mountbase")
        .workplane()
        .moveTo(
            sign * (dims.chimney.mountface.align.hole.diam + dims.vac.wall_thick) / 2,
            0
        )
        .circle(dims.chimney.mountface.align.stub.diam / 2)
        .extrude(
            dims.chimney.mountface.align.stub.length,
            taper=dims.chimney.mountface.align.stub.taper
        )
    )

cutter = (
    chimney
    .faces("<Z")
    .workplane()
    .circle(dims.chimney.base.od)
    .extrude(-dims.chimney.base.step_z, combine=False)
    .faces("<Z")
    .workplane()
    .hole(dims.chimney.base.step_diam - 0.1)
)
chimney = chimney.cut(cutter)
del cutter

vac_path = (
    cq.Workplane()
    .copyWorkplane(chimney.workplaneFromTagged('2'))
    .circle(dims.chimney.base.id / 2)
    .copyWorkplane(chimney.workplaneFromTagged('3'))
    .circle(dims.chimney.midprofile.id / 2)
    .copyWorkplane(chimney.workplaneFromTagged('4'))
    .circle(dims.chimney.mountbase.id / 2)
    .sweep(path, multisection=True)
    .faces("<Z")
    .workplane()
    .circle(dims.chimney.base.id / 2)
    .extrude(dims.chimney.base.step_z)
    .faces(">Z")
    .workplane()
    .circle(dims.chimney.top.id / 2)
    .extrude(dims.chimney.top.z - dims.chimney.mountbase.z)
)
chimney = chimney.cut(vac_path)
del vac_path

# magnets in the mounting face
cutters = []
# TODO: bottom face can't be selected, so rewrite this to locate a large cutter
# at magnet position
for pos in dims.chimney.mountface.magnets.positions:
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
