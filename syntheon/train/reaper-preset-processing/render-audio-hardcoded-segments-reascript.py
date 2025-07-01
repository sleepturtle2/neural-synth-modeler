# ReaScript (Python) for Reaper
# Renders three time segments from the current project, saving each as a separate WAV and RPP file.
from reaper_python import *  

# --- USER CONFIGURATION ---
# Prompt for preset name at script start

result = RPR_GetUserInputs("Preset Name", 1, "Enter preset name:", "", 100)
retval, user_input = result[0], result[4]

if retval:
    preset_name = user_input
else:
    preset_name = "unnamed_preset"
    
output_folder = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_preset_audio"
segments = [
    (0, 5),   # Segment 1: 0-5s
    (6, 10),  # Segment 2: 6-10s
    (11, 15)  # Segment 3: 11-15s
]
# --------------------------

project = 0  # 0 = current project

for idx, (start, end) in enumerate(segments, 1):
    # Set time selection
    RPR_GetSet_LoopTimeRange(True, False, start, end, False)
    # Set render bounds to time selection
    RPR_GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 1, True)  # 1 = time selection
    # Set render output filename
    wav_path = f"{output_folder}/{preset_name}_segment{idx}.wav"
    RPR_GetSetProjectInfo_String(project, "RENDER_FILE", wav_path, True)
    # Render project (using most recent settings)
    RPR_Main_OnCommand(41824, 0)  # File: Render project, using the most recent render settings
    RPR_ShowConsoleMsg(f"Rendered: {wav_path}\n")

# Save project once after all segments
rpp_path = f"{output_folder}/{preset_name}.rpp"
RPR_Main_SaveProjectEx(project, rpp_path, False)
RPR_ShowConsoleMsg(f"Project saved as: {rpp_path}\n")

RPR_ShowMessageBox("Batch segment rendering complete!", "Done", 0)