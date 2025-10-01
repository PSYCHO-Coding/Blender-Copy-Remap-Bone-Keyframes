# Psycho's Helpers

## Swap keyframes between two bones, flip keyframe fcurves or copy bone keyframes between pairs with different orientations.

### Found in the 'N' menu under "Item" and "Psychos Helpers". Yeh, I suk with names. xD

E.g. You, like me, goofed up, made a IK effector bone in a particular orientation, made 20+ animations and then you realize... the copy pose and copy pose flipped keeps messing up because you oriented bones to fit you're 'logic' rather then the softwares way of work.

How do you fix that? Welp, since Blender ofc don't have a reorientation feature...
Either copy old IK keyframes on new one by single channel and adjust/flip as needed or...
Make my own. And I did.
So far it only copies over location XYZ keyframes from one bone to another as that's the only thing I need.
Ya'll can get the idea here and do whatever, edit it to support rotations tho I suk at math and quaterntions so I don't even know where I'd begin to make a proper reorientation code for that.
Or it might be simple like location, X+ to Y+ or Y- etc. Dunno, don't care. Yet.

Also, found myself flipping axis locations or rotations or swapping bone keyframes a lot so this should help with that.

Planned: Swap keyframes/fcurves by channels and auto keyframe/fcurve rotation and value combine.

Here's a video hopefully somewhat explaining how 'copy bone keyframes with different orientations' works:

https://youtu.be/WIf6tv9pAZw


I'll probably just add a bunch of features and stuff that I need as I go and as I need them, realize what I need or what is missing.

![Image](https://github.com/user-attachments/assets/46ebce29-0fc6-4e2a-b981-f124dc4bd81f)

![Image](https://github.com/user-attachments/assets/7ada7f80-cc6d-4639-9cec-0a56e3273ecc)
