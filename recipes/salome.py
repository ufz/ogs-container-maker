from ogscm.building_blocks.salome import salome

Stage0.baseimage('nvidia/opengl:1.0-glvnd-runtime-ubuntu18.04')

Stage0 += packages(ospackages=['wget'])
Stage0 += salome()
Stage0 += python()
