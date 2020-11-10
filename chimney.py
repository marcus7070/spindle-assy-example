import cadquery as cq
import dims
import importlib
importlib.reload(dims)

# this chimney should be a sweep over a set of profiles. The outer edge should
# be a straight line, the inner edge should curve quite a bit so that it avoids
# the clamp.
