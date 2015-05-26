import nuke
import os
import sys
import re

nuke.tprint('running init.py')

homepath = os.path.abspath('/nas/projects/development/pipeline/pipeline.config/nuke_repo')
targetDirs = [os.path.join(homepath, dir) for dir in os.listdir(homepath) if os.path.isdir(os.path.join(homepath, dir))]

nukePattern = re.compile('nuke\.([A-Z]+)$')
sysPattern = re.compile('sys\.([A-Z]+)$')

for i in targetDirs:
    thisDir = os.path.split(i)[1]
    if nukePattern.match(thisDir):
        nuke.pluginAddPath(i)
    if sysPattern.match(thisDir):
        sys.path.append(i)

if not nuke.GUI:
    nuke.tprint('\n\n')
    for i in nuke.pluginPath():
        nuke.tprint(i)
    nuke.tprint('\n\n')
    for i in sys.path:
        nuke.tprint(i)
    nuke.tprint('\n\n')

nuke.ViewerProcess.register("3D LUT", nuke.createNode, ("Vectorfield", "vfield_file /nas/projects/development/pipeline/pipeline.config/nuke_repo/nuke.LUT/logC-Filmlook_display/AlexaV3_EI1600_LogC2Film_EL_nuke3d.cube"))
