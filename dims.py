import math
from types import SimpleNamespace as d


clamp = d()
clamp.bolt = d()
clamp.bolt.stickout = 7.1
clamp.bolt.thread = "M8"
clamp.bolt.spacing = (80, 34)
clamp.dims = (101.5, 78.6, 62.1)
clamp.chamfer = 3
clamp.shoulder = d()
clamp.shoulder.outer_x = 65 / 2
clamp.shoulder.inner_x = 31 / 2
clamp.shoulder.delta_y = clamp.dims[1] - 62.7
clamp.upper = (98.3, 40)
clamp.lower = (clamp.dims[0], clamp.dims[1] - clamp.shoulder.delta_y - clamp.upper[1])
clamp.hole = d()
clamp.hole.diam = 62
clamp.hole.pos = (0, 70.2 - clamp.hole.diam / 2 - 3, 0)

bracket = d()
bracket.thick = 13
bracket.width = 100
bracket.height = 95
bracket.tee_nut_spacing = 30
bracket.m5 = d()
bracket.m5.v_slot_face_to_top = 10.4 + 0.6  # actual measurement + clearance

spindle = d()
spindle.body = d()
spindle.body.diam = 62
spindle.body.length = 170
spindle.body.clamp_end_offset = 16
spindle.bearing_cap = d()
spindle.bearing_cap.diam = 46
spindle.bearing_cap.height = 5.1
spindle.shaft = d()
spindle.shaft.diam = 14
spindle.shaft.length = 15  # to the back of the nut
spindle.nut = d()
spindle.nut.diam = 19
spindle.nut.flats = 17
spindle.nut.length = 12

# OK, so I want the bottom face of the nut to be even with the bottom of the
# bottom of the bracket on the underside of the v-slot. That bracket is 6mm
# thick (can't be assed modelling it). 

bottom_of_vslot_to_bottom_of_bracket = (
    -6
    + spindle.nut.length
    + spindle.shaft.length
    + spindle.bearing_cap.height
    + spindle.body.clamp_end_offset
    + clamp.dims[2] / 2
    - bracket.height / 2
)

vac_brack = d()
vac_brack.holes = [-10 + 20 * idx for idx in range(3)]
vac_brack.x_centre = vac_brack.holes[1]
vac_brack.x_min = min(vac_brack.holes) - 10
vac_brack.x_max = max(vac_brack.holes) + 10
vac_brack.x = vac_brack.x_max - vac_brack.x_min
vac_brack.z = bottom_of_vslot_to_bottom_of_bracket - 1
vac_brack.wall_thick = 9
vac_brack.hole = d()
vac_brack.hole.diam = 5 * 1.2
vac_brack.hole.cbore_diam = 10
vac_brack.y = bracket.thick
vac_brack.hole.cbore_depth = vac_brack.y - vac_brack.wall_thick

vac = d()
vac.hose = d()
vac.hose.od = 42
vac.hose.id = 32.7
vac.hose.socket = d()
vac.hose.socket.od = vac.hose.od + 5 * 2
vac.hose.insertion = vac.hose.od / 2
vac.hose.tape_width = 50
vac.hose.plane = d()
radius = spindle.body.diam / 2 + vac.hose.socket.od / 2 + 10
angle = math.radians(-45)
vac.hose.plane.origin = (
    math.cos(angle) * radius
    , math.sin(angle) * radius - 10
    , vac_brack.z
)
# vac.hose.plane.rotation = (10, 10, 0)  # kernel twists this weirldly
vac.hose.plane.rotation = (0, 0, 0)
vac.mount_face = d()
vac.mount_face.x_min = vac_brack.x_min
vac.mount_face.x_max = vac_brack.x_max
vac.mount_face.y = clamp.hole.pos[1] + bracket.thick - vac_brack.y
vac.inner_rad = spindle.nut.diam / 2 + 4
vac.z = vac_brack.z
vac.wall_thick = 2
vac.port = d()
vac.port.rad = vac.hose.id / 2 * 1.2
vac.brush = d()
vac.brush.slot_width = 5.5
vac.brush.slot_depth = 10  # brush has 20mm canvas on top
vac.chimney = d()
vac.chimney.main_od = vac.hose.id + vac.wall_thick * 2
vac.chimney.height = 100


magnet = d()
magnet.diam = 3.9
magnet.slot = d()
magnet.slot.width = magnet.diam * 1.2
magnet.thick = 4.9
magnet.wall_thick = 1.0
magnet.slot.thick = magnet.thick * 1.2
magnet.positions = []
magnet.seperation = magnet.slot.width + 3 * magnet.wall_thick
magnet.number = math.floor((vac_brack.x_max - vac_brack.x_min) / magnet.seperation)
centre = (vac_brack.x_max + vac_brack.x_min) / 2
leftmost_offset = centre - (magnet.number - 1) * magnet.seperation / 2
for y in [1, -1]:
    for x in range(magnet.number):
        magnet.positions.append((
            leftmost_offset + x * magnet.seperation
            , y * (vac_brack.z / 2 - magnet.diam / 2 * 1.2)
        ))
del centre, leftmost_offset

assembly = d()
assembly.bracket = d()
assembly.bracket.offset = (0, 0, bottom_of_vslot_to_bottom_of_bracket + bracket.height / 2)
assembly.clamp = d()
assembly.clamp.offset = (0, -bracket.thick, assembly.bracket.offset[2])
assembly.spindle = d()
assembly.spindle.offset = (0, assembly.clamp.offset[1] - clamp.hole.pos[1], assembly.clamp.offset[2] - clamp.dims[2] / 2)
assembly.vac_brack = d()
assembly.vac_brack.offset = (0, 0, vac_brack.z / 2)
assembly.vac_brack.z_min = assembly.vac_brack.offset[2] - vac_brack.z / 2
assembly.vac = d()
assembly.vac.offset = (assembly.spindle.offset[0], assembly.spindle.offset[1], assembly.vac_brack.z_min)
