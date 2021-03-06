import nuke
#import tractorNukeLib

nuke.tprint('running menu.py')

if nuke.GUI:
    nuke.tprint('\n\n')
    for i in nuke.pluginPath():
        nuke.tprint(i)
    nuke.tprint('\n\n')
    for i in sys.path:
        nuke.tprint(i)
    nuke.tprint('\n\n')
    
    ##
    ##   By Belal Salem
    ##
    
    # Plugins load and menu configurations for them:
    toolbar=nuke.toolbar("Nodes")
    toolbar.addCommand( "Filter/ZFog", "nuke.createNode('Fog')","", icon="ZFog.png" )
    toolbar.addCommand( "Keyer/rgbMatte", "nuke.createNode('RGBmatte')","", icon="" )
    toolbar.addCommand( "Keyer/colorMatte", "nuke.createNode('colorMatte')","", icon="" )
    toolbar.addCommand( "Color/exr2lin", "nuke.createNode('exr2lin')", "", icon="" )
    toolbar.addCommand( "Color/lin2exr", "nuke.createNode('lin2exr')", "", icon="" )
    toolbar.addCommand( "Filter/bokehBlur", "nuke.createNode('Bokeh_Blur')","", icon="" )
    toolbar=nuke.toolbar("Nodes")
    #toolbar.addCommand("Tractor/Open Tractor Panel", "tractorNukeLib.renderPanel(True)", icon="TractorRenderSpool.png")
    
    # Viewer Defaults:
    nuke.knobDefault('Viewer.viewerProcess', 'none')
    nuke.knobDefault('Viewer.useGPUForViewer', 'True')
    nuke.knobDefault('Viewer.disableGPUDitherForViewer', 'True')
    
    # Project settings Defaults:
    # LUTs and default LUTs for file Write/Read nodes:
    nuke.knobDefault("Root.monitorLut", "linear")
    nuke.knobDefault("Root.viewerLut", "linear")
    nuke.knobDefault("Root.int8Lut", "linear")
    nuke.knobDefault("Root.int16Lut", "linear")
    nuke.knobDefault("Root.logLut", "Cineon")
    nuke.knobDefault("Root.floatLut", "linear")
    
    
    # Frame format and FPS:
    nuke.knobDefault('Root.format', '720 576 1.09')
    nuke.knobDefault('Root.fps', '25' )

    # Registering Truelight as Viewer Process
    # nuke.ViewerProcess.register("Truelight", nuke.Node, ("Truelight", ""))

    # 3DEqualizer4 Lens distortion models:

    menubar = nuke.menu("Nodes")
    menubar.addCommand("Filter/tdeLens_classic","nuke.createNode('tde4_ldp_classic_3de_mixed')")	
    menubar = nuke.menu("Nodes")
    menubar.addCommand("Filter/tdeLens_deg_6","nuke.createNode('tde4_ldp_anamorphic_deg_6')")
    menubar = nuke.menu("Nodes")
    menubar.addCommand("Filter/tdeLens_deg_8","nuke.createNode('tde4_ldp_radial_deg_8')")
    menubar = nuke.menu("Nodes")
    menubar.addCommand("Filter/tdeLens_deg_4","nuke.createNode('tde4_ldp_radial_decentered_deg_4')")
