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
    .tag('beforemountface')
)

# mounting face
chimney = (
    chimney
    .copyWorkplane(
        cq.Workplane('YZ', origin=(0, dims.chimney.mountbase.od / 2, dims.chimney.mountface.origin[2]))
    )
    .transformed(rotate=(0, -45, 0))
    .moveTo(dims.chimney.mountface.origin[1], dims.chimney.mountface.height / 2)
    .hLineTo(0)
    .vLine(-dims.chimney.mountface.height)
    .lineTo(dims.chimney.mountface.origin[1], -dims.chimney.mountface.height / 2)
    .close()
    .extrude(dims.chimney.mountface.width / 2, both=True)
    .tag('mountbase')
)
for sign in [-1, 1]:
    chimney = (
        chimney
        .faces(">(1, 1, 0)", tag="mountbase")
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

# hose socket
chimney = (
    chimney
    .faces('>Z', tag='beforemountface')
    .workplane()
    .circle(dims.chimney.top.od / 2)
    .workplane(offset=dims.chimney.hose.socket.od - dims.chimney.top.od)
    .circle(dims.chimney.hose.socket.od / 2)
    .loft()
    .faces(">Z")
    .workplane()
    .circle(dims.chimney.hose.socket.od / 2)
    .extrude(dims.vac.wall_thick + dims.chimney.hose.insertion + dims.chimney.hose.tape_width)
    .tag('top holes')
    .faces(">Z")
    .workplane()
    .hole(
        dims.chimney.hose.od,
        depth=dims.chimney.hose.insertion + dims.chimney.hose.tape_width
    )
    # .faces(">Z", tag="top holes")
    # .workplane()
    # .hole(
    #     dims.chimney.hose.id,
    #     depth=dims.vac.wall_thick + dims.chimney.hose.insertion + dims.chimney.hose.tape_width
    # )
    .faces(">Z", tag="top holes")
    .workplane()
    .center(dims.chimney.hose.od / 2, 0)
    .rect(10, dims.chimney.hose.socket.od * 2)
    .cutBlind(-dims.chimney.hose.tape_width)
    .faces(">Z", tag="top holes")
    .workplane()
    .center(-dims.chimney.hose.od / 2, 0)
    .rect(10, dims.chimney.hose.socket.od * 2)
    .cutBlind(-dims.chimney.hose.tape_width)
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

chimney_top = chimney.findSolid().BoundingBox().zmax
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
    .extrude(chimney_top - dims.chimney.mountbase.z)
)
chimney = chimney.cut(vac_path)
del vac_path

# magnets in the mounting face
cutters = []
# TODO: bottom face can't be selected, so rewrite this to locate a large cutter
# at magnet position
magnet_cutter = (
    cq
    .Workplane('XZ', origin=(0, 0, 0))
    .moveTo(dims.magnet.slot.width / 2, dims.magnet.diam)
    .vLineTo(0)
    .tangentArcPoint((-dims.magnet.slot.width / 2, 0), relative=False)
    .vLineTo(dims.magnet.diam)
    .close()
    .extrude(dims.magnet.slot.thick)
)
ys = [pos[1] for pos in dims.chimney.mountface.magnet.position]
y_mid = (min(ys) + max(ys)) / 2
faces =  chimney.faces(">(1, 1, 0)", tag="mountbase").vals()
shell = cq.Shell.makeShell(faces)
mount_origin = shell.Center()
plane = chimney.faces(">(1, 1, 0)", tag="mountbase").workplane().plane
for pos in dims.chimney.mountface.magnet.position:
    angle = 180 if (pos[1] < y_mid) else 0
    final_pos = plane.toWorldCoords((pos[0], pos[1], -dims.magnet.wall_thick))
    cutters.append(
        magnet_cutter
        .rotate((0, 0, 0), (0, 0, 1), -45)
        .rotate((0, 0, 0), (1, 1, 0), angle)
        .translate(final_pos)
    )
del magnet_cutter
for cutter in cutters:
    chimney = chimney.cut(cutter)
    del cutter
