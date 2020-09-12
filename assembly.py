import cadquery as cq
import vslot
import clamp as clamp_module
import bracket as bracket_module
import spindle as spindle_module
import vac_brack as vac_brack_module
import vac as vac_module
import dims
import importlib
importlib.reload(dims)
importlib.reload(clamp_module)
importlib.reload(bracket_module)
importlib.reload(spindle_module)
importlib.reload(vac_brack_module)
importlib.reload(vac_module)


back = vslot.cslot(150)
clamp = (
    clamp_module.clamp
    .clean()
    .rotate((0, 0, 0), (0, 0, 1), 180)
    .translate(dims.assembly.clamp.offset)
)
bracket = (
    bracket_module.bracket
    .translate(dims.assembly.bracket.offset)
)
spindle = (
    spindle_module.spindle
    .translate(dims.assembly.spindle.offset)
)
vac_brack = (
    vac_brack_module.bracket
    .translate(dims.assembly.vac_brack.offset)
)
vac = (
    vac_module.part
    .translate(dims.assembly.vac.offset)
)
