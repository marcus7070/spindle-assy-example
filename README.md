# Spindle and vacuum attachment

This is a model of the vacuum attachment for my Workbee CNC router. There is a mist spray coming from the left hand side of the spindle, blowing chips towards the vacuum port and nylon brush on the right side. It's a bit of an experiment, we'll see how it goes.

The vacuum attachment and brackets are 3D printed from this model.

I'm publishing this on GitHub because I feel there isn't enough examples of complicated [CadQuery](https://github.com/cadquery/cadquery) models. I also learn the most from reading others' code, so I hope someone can get some ideas from reading this. 

![Old screenshot](https://github.com/marcus7070/spindle-assy-example/raw/master/screenshot2020-09-11-125732.png)

## nix

If you're lucky enough to use NixOS (and can use flakes, currently in the unstable branch but soon to be merged into the main branch), don't bother installing anything, just use this to run cq-editor:
```sh
nix run github:marcus7070/cq-flake/11ef47f5aa465e0b1cf9bbc15999a5ed0b713ba9
```
and this to create an environment with a cadquery-aware python-language-server (which will hopefully be picked up by your IDE):
```sh
nix shell github:marcus7070/cq-flake/11ef47f5aa465e0b1cf9bbc15999a5ed0b713ba9#cadquery-env
```
These commands will use pinned versions of everything, from CadQuery to glibc, and should be completly reproducible no matter what happens to CadQuery, conda, pypi, NixOS, or even QT. Hooray for nix!
