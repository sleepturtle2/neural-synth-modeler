# ReaScript (Python) for Reaper
# Renders three time segments from the current project, saving each as a separate WAV and RPP file.
from reaper_python import *  
import os
import json

# --- CONSTANTS ---
VITAL_ROOT = "/Users/sayantanm/Music/Vital"
PRESET_MAP_PATH = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/preset_map.json"
OUTPUT_FOLDER = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_preset_audio"

# --- UTILS ---
def clean_name(filename):
    return filename.replace(' ', '-').lower().rstrip('-')

def load_preset_map():
    if os.path.exists(PRESET_MAP_PATH):
        with open(PRESET_MAP_PATH, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_preset_map(preset_map):
    with open(PRESET_MAP_PATH, 'w') as f:
        json.dump(preset_map, f, indent=2)

def find_vital_preset_file(training_name):
    # training_name follows preset preprocessing convention 
    for root, dirs, files in os.walk(VITAL_ROOT):
        for file in files:
            if clean_name(file) == training_name:
                return os.path.join(root, file)
    return None

def get_segments_for_style(style, preset_data=None):
    style = (style or "").lower().strip()
    if style == "bass":
        return [8,9,10,11,12,13,14,15,16] # c3 and above 
    elif style == "lead":
        return [8,9,10,11,12,13,14,15,16] # c3 and above 
    elif style == "pad":
        # Check for fast/slow attack
        attack_threshold = 0.5 # seconds 
        attack_keys = [f"env_{i}_attack" for i in range(1,7)]
        attacks = []
        if preset_data:
            for k in attack_keys:
                v = preset_data.get(k)
                if v is not None:
                    attacks.append(float(v))
        if any(a < attack_threshold for a in attacks):
            # Pad: fast attack, using all segments
            return list(range(6, 17))
        else:
            # Pad: slow attack detected, using sustain segments only
            return [7,9,11,13,15,16]
    elif style in ["keys", "sequence", "percussion", "none", ""]:
        return list(range(8, 17))
    elif style in ["sfx", "experiment"]:
        return list(range(6,17)) 
    else:
        return list(range(8, 17))

# --- USER CONFIGURATION ---
# Prompt for preset name or number at script start

result = RPR_GetUserInputs("Preset Name or Number", 1, "Enter preset name or number:", "", 100)
retval, user_input = result[0], result[4]

if not retval:
    print("User cancelled preset naming. Script ended.")
else:
    # Load preset map
    if os.path.exists(PRESET_MAP_PATH):
        with open(PRESET_MAP_PATH, 'r') as f:
            preset_map = json.load(f)
    else:
        preset_map = {}

    preset_name = user_input.strip()
    # Check if input is an integer (number selection)
    try:
        preset_num = str(int(preset_name))
        if preset_num in preset_map:
            entry = preset_map[preset_num]
            preset_name = entry['cleaned_name']
            print(f"Selected preset #{preset_num}: {entry['actual_name']} (cleaned: {preset_name})")
        else:
            print(f"Error: No preset found for number {preset_num}. Script ended.")
            raise SystemExit
    except ValueError:
        # Not an int, treat as string and clean
        preset_name = clean_name(preset_name)
        RPR_ShowConsoleMsg(f"Using user-entered preset name: {preset_name}\n")

    if not preset_name:
        # Find the next available unnamed_N directory
        i = 1
        while os.path.exists(os.path.join(OUTPUT_FOLDER, f"unnamed_{i}")):
            i += 1
        preset_name = f"unnamed_{i}"
    preset_dir = os.path.join(OUTPUT_FOLDER, preset_name)
    if os.path.exists(preset_dir):
        # Prompt user if they want to overwrite
        resp = RPR_ShowMessageBox(f"Preset audio folder '{preset_dir}' already exists. Overwrite?", "Overwrite Preset Audio", 4)  # 4 = Yes/No
        if resp == 6:  # Yes
            import shutil
            try:
                shutil.rmtree(preset_dir)
                RPR_ShowConsoleMsg(f"Deleted existing folder: {preset_dir}\n")
            except Exception as e:
                RPR_ShowConsoleMsg(f"Error deleting folder {preset_dir}: {e}\n")
        else:
            RPR_ShowConsoleMsg(f"Skipping rendering for preset '{preset_name}' (user chose not to overwrite).\n")
            raise SystemExit
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)
    # two variations have been added for each octave -> pluck, sustain
    # last segment #16 is middle c sustain
    segments = [
        (0, 6),   #0 -> c-1-c0
        (8, 14),  #1
        (16, 21), #2 -> c0-c1
        (24, 31), #3
        (32, 39), #4-> c1-c2
        (40, 48), #5
        (52, 60), #6-> c2-c3
        (62, 67), #7
        (68, 75), #8 -> c3-c4
        (76, 81), #9
        (84, 91), #10 -> c4-c5
        (92, 96), #11
        (98, 105), #12 -> c5-c6
        (108, 112), #13
        (114, 121), #14 -> c6-c7
        (122, 126), #15
        (128, 132)  #16 -> keep this always 
    ]
    project = 0  # 0 = current project

    # Read preset_style from JSON if available
    preset_json_path = os.path.join(preset_dir, f"{preset_name}.json")
    preset_style = ""
    preset_data = None
    if os.path.exists(preset_json_path):
        try:
            with open(preset_json_path, 'r') as f:
                preset_data = json.load(f)
            preset_style = preset_data.get("preset_style", "").strip().lower()
        except Exception as e:
            print(f"Could not read preset style from {preset_json_path}: {e}")

    # Determine which segment indices to render based on style
    segment_indices = get_segments_for_style(preset_style, preset_data)
    print(f"Rendering segments for style '{preset_style}': {segment_indices}")
    RPR_ShowConsoleMsg(f"Rendering segments for style '{preset_style}': {segment_indices}\n")

    # --- USER SEGMENT SELECTION ---
    # Show dialog with default indices as suggestion
    default_indices_str = ','.join(str(idx) for idx in segment_indices)  # 1-based for user
    seg_prompt_title = "Segment Selection"
    seg_prompt_caption = f"Enter segment numbers (comma-separated) or leave blank for default: [{default_indices_str}]"
    seg_result = RPR_GetUserInputs(seg_prompt_title, 1, seg_prompt_caption, default_indices_str, 200)
    seg_retval, seg_user_input = seg_result[0], seg_result[4]
    if seg_retval and seg_user_input.strip():
        # Parse user input (expecting comma-separated numbers)
        try:
            user_indices = [int(x.strip()) for x in seg_user_input.split(',') if x.strip()]
            # Validate indices
            valid_indices = [idx for idx in user_indices if 0 <= idx < len(segments)]
            if valid_indices:
                segment_indices = valid_indices
                RPR_ShowConsoleMsg(f"Using user-selected segments: {[idx for idx in segment_indices]}\n")
            else:
                RPR_ShowConsoleMsg("No valid segment indices entered. Using default.\n")
        except Exception as e:
            RPR_ShowConsoleMsg(f"Error parsing segment input: {e}. Using default.\n")
    else:
        RPR_ShowConsoleMsg(f"Using default segments: {[idx for idx in segment_indices]}\n")

    for seg_idx in segment_indices:
        start, end = segments[seg_idx]
        # Set time selection
        RPR_GetSet_LoopTimeRange(True, False, start, end, False)
        # Set render bounds to time selection
        RPR_GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 2, True)  # 2 = Render time selection
        # Set render output filename (no subdirectory, just the file)
        wav_path = os.path.join(preset_dir, f"{preset_name}_segment{seg_idx}.wav")
        print(f"Rendering segment {seg_idx}: start={start}s, end={end}s -> {wav_path}")
        RPR_ShowConsoleMsg(f"Rendering segment {seg_idx}: start={start}s, end={end}s -> {wav_path}\n")
        RPR_GetSetProjectInfo_String(project, "RENDER_FILE", wav_path, True)
        # Render project (using most recent settings)
        RPR_Main_OnCommand(41824, 0)  # File: Render project, using the most recent render settings
        RPR_ShowConsoleMsg(f"Rendered and saved: {wav_path}\n")
        # Save project with segment info

    # Save the project file after all renders
    rpp_path = os.path.join(preset_dir, f"{preset_name}.rpp")
    RPR_Main_SaveProjectEx(project, rpp_path, False)
    RPR_ShowConsoleMsg(f"Saved reaper project to {rpp_path}\n")
    RPR_ShowConsoleMsg("Batch segment rendering complete!")

    # --- REMOVE FROM REMAINING MAP ---
    REMAINING_MAP_PATH = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/preset_render_remaining_map.json"
    # Try to remove the rendered preset's id from the remaining map (nested structure)
    try:
        if os.path.exists(REMAINING_MAP_PATH):
            with open(REMAINING_MAP_PATH, 'r') as f:
                remaining_map = json.load(f)
            # Load preset map to get osc and style
            if os.path.exists(PRESET_MAP_PATH):
                with open(PRESET_MAP_PATH, 'r') as f:
                    preset_map = json.load(f)
                # Determine preset_id
                preset_id = None
                try:
                    preset_id = str(int(user_input.strip()))
                except Exception:
                    for idx, entry in preset_map.items():
                        if entry['cleaned_name'] == preset_name:
                            preset_id = idx
                            break
                if preset_id:
                    # Find osc and style for this preset
                    entry = preset_map.get(preset_id, {})
                    osc_count = None
                    preset_style = None
                    if entry:
                        # Try to infer osc key
                        osc_count = None
                        try:
                            from syntheon.train.vital.vital_preprocessor import count_oscillators
                        except ImportError:
                            pass
                        src_file = entry.get('full_path', None)
                        if src_file:
                            try:
                                osc_count = count_oscillators(src_file)
                            except Exception:
                                osc_count = None
                        if osc_count is None:
                            osc_key = 'unknown_osc'
                        else:
                            osc_key = f'has_{osc_count}_osc'
                        preset_style = entry.get('preset_style', '').strip() or 'unknown_style'
                        # Remove from nested map
                        if osc_key in remaining_map and preset_style in remaining_map[osc_key]:
                            if preset_id in remaining_map[osc_key][preset_style]:
                                remaining_map[osc_key][preset_style].remove(preset_id)
                                RPR_ShowConsoleMsg(f"Removed preset id {preset_id} from remaining map under {osc_key}/{preset_style}.\n")
                                # Clean up empty lists/dicts
                                if not remaining_map[osc_key][preset_style]:
                                    del remaining_map[osc_key][preset_style]
                                if not remaining_map[osc_key]:
                                    del remaining_map[osc_key]
                                with open(REMAINING_MAP_PATH, 'w') as f:
                                    json.dump(remaining_map, f, indent=2)
                            else:
                                RPR_ShowConsoleMsg(f"Preset id {preset_id} not found in remaining map under {osc_key}/{preset_style}.\n")
                        else:
                            RPR_ShowConsoleMsg(f"Preset id {preset_id} not found in remaining map (osc/style missing).\n")
                    # Fallback: search all osc/style for the id and remove if found
                    found = False
                    for osc_key in list(remaining_map.keys()):
                        for style_key in list(remaining_map[osc_key].keys()):
                            if preset_id in remaining_map[osc_key][style_key]:
                                remaining_map[osc_key][style_key].remove(preset_id)
                                found = True
                                RPR_ShowConsoleMsg(f"Fallback: Removed preset id {preset_id} from {osc_key}/{style_key}.\n")
                                # Clean up empty lists/dicts
                                if not remaining_map[osc_key][style_key]:
                                    del remaining_map[osc_key][style_key]
                                if not remaining_map[osc_key]:
                                    del remaining_map[osc_key]
                                with open(REMAINING_MAP_PATH, 'w') as f:
                                    json.dump(remaining_map, f, indent=2)
                                break
                        if found:
                            break
                    if not found:
                        RPR_ShowConsoleMsg(f"Preset id {preset_id} could not be found in any osc/style category.\n")
            # After removal, reload the map and print the new total unrendered count
            with open(REMAINING_MAP_PATH, 'r') as f:
                updated_remaining_map = json.load(f)
            new_unrendered = sum(len(ids) for osc in updated_remaining_map.values() for ids in osc.values())
            # Count rendered
            render_dir = "/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_preset_audio"
            rendered_count = 0
            if os.path.exists(render_dir):
                rendered_count = len([d for d in os.listdir(render_dir) if os.path.isdir(os.path.join(render_dir, d))])
            # Count total in preset map
            total_count = len(preset_map)
            RPR_ShowConsoleMsg(f"After removal: Unrendered: {new_unrendered}, Rendered: {rendered_count}, Total: {total_count}\n")
            if rendered_count + new_unrendered != total_count:
                RPR_ShowConsoleMsg("ERROR: Rendered + Unrendered does not equal total presets!\n")
    except Exception as e:
        RPR_ShowConsoleMsg(f"Error updating remaining map: {e}\n")