import importlib
import cadquery as cq
import dims
importlib.reload(dims)

# origin is the bottom of the clamping range
spindle = (
    cq
    .Workplane()
    .workplane(offset=-dims.spindle.body.clamp_end_offset)
    .circle(dims.spindle.body.diam / 2)
    .extrude(dims.spindle.body.length)
    .faces("<Z")
    .workplane()
    .circle(dims.spindle.bearing_cap.diam / 2)
    .extrude(dims.spindle.bearing_cap.height)
    .faces("<Z")
    .workplane()
    .circle(dims.spindle.shaft.diam / 2)
    .extrude(dims.spindle.shaft.length)
    .faces("<Z")
    .workplane()
    .polygon(6, dims.spindle.nut.diam)
    .extrude(dims.spindle.nut.length)
)
