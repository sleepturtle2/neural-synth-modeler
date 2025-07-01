# ReaScript (Python) for Reaper
# Renders three time segments from the current project, saving each as a separate WAV and RPP file.
from reaper_python import *  
import os

# --- USER CONFIGURATION ---
# Prompt for preset name at script start

result = RPR_GetUserInputs("Preset Name", 1, "Enter preset name:", "", 100)
retval, user_input = result[0], result[4]

if not retval:
    RPR_ShowConsoleMsg("User cancelled preset naming. Script ended.\n")
else:
    preset_name = user_input
    output_folder = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_preset_audio"
    preset_dir = os.path.join(output_folder, preset_name)
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)
    segments = [
        (0, 4),   # Segment 1: 0-4s
        (4, 8),   # Segment 2: 4-8s
        (8, 12)    # Segment 3: 8-12s
    ]
    project = 0  # 0 = current project

    for idx, (start, end) in enumerate(segments, 1):
        # Set time selection
        RPR_GetSet_LoopTimeRange(True, False, start, end, False)
        # Set render bounds to time selection
        RPR_GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 0, True)  # 0 = Render master mix
        # Set render output filename (no subdirectory, just the file)
        wav_path = os.path.join(preset_dir, f"{preset_name}_segment{idx}.wav")
        print(f"Rendering segment {idx}: start={start}s, end={end}s -> {wav_path}")
        RPR_ShowConsoleMsg(f"Rendering segment {idx}: start={start}s, end={end}s -> {wav_path}\n")
        RPR_GetSetProjectInfo_String(project, "RENDER_FILE", wav_path, True)
        # Render project (using most recent settings)
        RPR_Main_OnCommand(41824, 0)  # File: Render project, using the most recent render settings
        RPR_ShowConsoleMsg(f"Rendered and saved: {wav_path}\n")
        # Save project with segment info

    rpp_path = os.path.join(preset_dir, f"{preset_name}_segment{idx}.rpp")
    RPR_Main_SaveProjectEx(project, rpp_path, False)
    RPR_ShowConsoleMsg(f"Saved reaper project to {rpp_path}\n")
    RPR_ShowMessageBox("Batch segment rendering complete!", "Done", 0)