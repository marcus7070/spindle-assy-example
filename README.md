# Spindle and vacuum attachment

This is a model of the vacuum attachment for my Workbee CNC router. There is a mist spray coming from the left hand side of the spindle, blowing chips towards the vacuum port and nylon brush on the right side. It's a bit of an experiment, we'll see how it goes.

The vacuum attachment and brackets are 3D printed from this model.

I'm publishing this on GitHub because I feel there isn't enough examples of complicated [CadQuery](https://github.com/cadquery/cadquery) models. I also learn the most from reading others' code, so I hope someone can get some ideas from reading this. Please do keep in mind that this is just one of an endless list of jobs for me to get done out at work so at the moment the code is a bit of a mess. I hope to get some time to clean it up soon, I'm dreading coming back to this in a years time and trying to reiterate it!

* There are lots of dimensions specified in `dims.py` that I wound up not using,
* `vac.py` contains some unusual classes and programming because I was having a bit of a mental block on how to make a surface between the vacuum port start and end, and I think there is still some small math error in it, and
* the assembly should really be broken down into several subassemblies rather than one flat structure as it currently is, I think some numerical errors in the solver are building up, sometimes that spindle isn't quite centered in the bracket.

![screenshot](https://github.com/marcus7070/spindle-assy-example/raw/master/screenshot.png)

## nix

If you're lucky enough to use NixOS (and can use flakes, currently in the unstable branch but soon to be merged into the main branch), don't bother installing anything, just use this to run cq-editor:
```sh
nix run github:marcus7070/cq-flake/4a19ce0386930e247383e1d2d5ff7c3b676b9986
```
and this to create an environment with a cadquery-aware python-language-server (which will hopefully be picked up by your IDE):
```sh
nix shell github:marcus7070/cq-flake/4a19ce0386930e247383e1d2d5ff7c3b676b9986#cadquery-env
```
These commands will use pinned versions of everything, from CadQuery to glibc, and should be completly reproducible no matter what happens to CadQuery, conda, pypi, NixOS, or even QT. Hooray for nix!
