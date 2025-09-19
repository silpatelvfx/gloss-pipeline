## init.py
## loaded by nuke before menu.py




import nuke
import platform
import nukescripts




 
if nuke.NUKE_VERSION_MAJOR < 11:
    # PySide for Nuke up to 10
    from PySide.QtGui import QPushButton
elif nuke.NUKE_VERSION_MAJOR < 16:
    # PySide2 for default Nuke 11
    from PySide2.QtWidgets import QPushButton
else:
    # PySide6 for Nuke 16+
    from PySide6.QtWidgets import QPushButton



#from myflipbook import *


# Define where .nuke directory is on each OS's network.
Win_Dir = "C:/Users/glossadmin/.nuke"
Mac_Dir = ''
Linux_Dir = '/home/benm/.nuke'

# Automatically set global directory
if platform.system() == "Windows":
	dir = Win_Dir
elif platform.system() == "Darwin":
	dir = Mac_Dir
elif platform.system() == "Linux":
	dir = Linux_Dir
else:
	dir = None
    
nuke.pluginAddPath('./gizmos')
nuke.pluginAddPath('./icons')
nuke.pluginAddPath('./python')
#import real_time_timer


nuke.pluginAddPath('./plugins')
nuke.pluginAddPath('./Toolsets')
nuke.pluginAddPath('./dll')


#nuke.pluginAddPath('./NukeSurvivalToolkit')
#nuke.pluginAddPath('./pixelfudger3')

#nuke.pluginAddPath('./Backdrop_Adjust')
nuke.pluginAddPath('./SmoothScrub')
nuke.pluginAddPath('./NukeServerSocket')
nuke.pluginAddPath('./ProfileInspector')
nuke.pluginAddPath('./MOTools')
nuke.pluginAddPath('./Cattery')
nuke.pluginAddPath('./V_Tools')
#nuke.pluginAddPath('./AUTOPROJECT_HELPER_01')
nuke.pluginAddPath('./GLOSS_NY_PIPELINE_v1.0.1')
nuke.pluginAddPath('./MONDAY_FOR_NUKE')
#nuke.pluginAddPath('./nuke_comfyui')

nuke.pluginAddPath('./For_Input_Process_Only')












nuke.pluginAddPath("/Volumes/san-04/GlossUsers/NukeShared")


# ----- SETTING KNOB DEFAULTS ---------------

#nuke.loadToolset("/Users/sheel/.nuke/Toolsets/Freq_Sep_From_Plus.nk")


nuke.knobDefault("Text2.message", "[file tail [metadata input/filename]]\n[metadata input/timecode]")



# Set FPS
nuke.knobDefault('Root.fps', '23.976')

nuke.knobDefault('Viewer.viewerProcess','rec709')
nuke.knobDefault('Viewer.input_process_node', 'Vectorfield1')
nuke.knobDefault('Vectorfield.colorspaceIn', "rec709")
nuke.knobDefault('Vectorfield.colorspaceOut', "rec709")

# Set shutter offset to "centered".
nuke.knobDefault('Tracker4.shutteroffset', "centered")

# Set dynamic label on Tracker to display the value of the "transform" and "reference_frame" knobs.
nuke.knobDefault('Tracker4.label', "Motion: [value transform]\nRef Frame: [value reference_frame]")

nuke.knobDefault('Tracker4.normalize', 'True')  # Adjust for luma changes
nuke.knobDefault('Tracker4.adjust_for_luminance_changes', 'True')  # Set tracking to affine mode



# Any time a Tracker node is created, set the "reference_frame" knob to the value of the current frame.
nuke.addOnUserCreate(lambda:nuke.thisNode()['reference_frame'].setValue(nuke.frame()), nodeClass='Tracker4')


# ----- MOTION BLUR SHUTTER CENTERED ---------------------------
nuke.knobDefault('Tracker4.shutteroffset', "centered")
nuke.knobDefault('TimeBlur.shutteroffset', "centered")
nuke.knobDefault('Transform.shutteroffset', "centered")
nuke.knobDefault('TransformMasked.shutteroffset', "centered")
nuke.knobDefault('CornerPin2D.shutteroffset', "centered")
nuke.knobDefault('MotionBlur2D.shutteroffset', "centered")
nuke.knobDefault('MotionBlur3D.shutteroffset', "centered")
nuke.knobDefault('ScanlineRender.shutteroffset', "centered")
nuke.knobDefault('Card3D.shutteroffset', "centered")

#nuke.knobDefault('Read.label',ccustomread)
nuke.knobDefault('Read.auto_alpha','1')
nuke.knobDefault('Read.frame_mode','offset')
nuke.knobDefault('Read.frame','0')
nuke.knobDefault('Read.label','----------\nFPS:[metadata input/frame_rate]\n\n[metadata quicktime/codec_name]\n\n[metadata input/timecode]')

#nuke.knobDefault('Write.file','[file rootname [file tail [value root.name]]]/[file rootname [file tail [value root.name]]].mov')
nuke.knobDefault('Write.file','[file rootname [file tail [value root.name]]].mov')
nuke.knobDefault('Write.colorspace','rec709')
nuke.knobDefault('Write.file_type','mov')
nuke.knobDefault('Write.mov64_codec','Apple Prores')
nuke.knobDefault('Write.create_directories','True')
nuke.knobDefault('Write.postage_stamp','True')




#blur node
nuke.knobDefault("Blur.label", "size: [value size]")
#Multiply node
nuke.knobDefault("Multiply.label", "value: [value value]")
#Saturation node
nuke.knobDefault("Saturation.label", "saturation: [value saturation]")
#Merge node
nuke.knobDefault("Merge.label", "mix: [value mix] ([value bbox])")
#Dot node - size
nuke.knobDefault("Dot.note_font_size", "35")
#Dot node - colour
nuke.knobDefault("Dot.note_font_color", "0xffffff")
#Shuffle node
nuke.knobDefault("Shuffle.label", "<b>[value in]</b> &rarr; [value out]")
#ShuffleCopy node
nuke.knobDefault("ShuffleCopy.label", "<b>[value in]</b> &rarr; [value out]")
#DeepMerge node
nuke.knobDefault("operation.label", "operation: [value size]")
#Exposure node
nuke.knobDefault("Exposure.label", "[value mode]: [value red]")
#Tracker node
nuke.knobDefault("Tracker.label", "[value transform] <br> Ref Frame:[value reference_frame]")







#nuke.pluginAddPath('./rvnuke')

#import djv_this



