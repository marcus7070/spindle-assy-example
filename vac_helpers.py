"""
Some helper functions and classes for vac.py.
"""



# ##########################################################################
# figuring out orientation for directly created surfaces
# even though I think OCC doesn't care about face orientation, I get so many
# kernel errors this can't do anything but help.
# ##########################################################################
# circ1 = cq.Edge.makeCircle(10, angle1=0, angle2=45)
# show_object(circ1)
# print(circ1.startPoint())
# print(circ1.endPoint())

# so angle1=0 places the startpoint on the x axis
# angle1=45 places the endpoint in the +x and +y quadrant
# this should be the orientation of the top circle
# the kidney shaped vacuum port should be flipped compared to this
# then I think the ruled surface between the two will take care of itself.


