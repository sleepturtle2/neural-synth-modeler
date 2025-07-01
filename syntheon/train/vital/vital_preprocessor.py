import os
import shutil
import json

# Helper to count oscillators in a Vital preset file
# Assumes .vital is a JSON (if not, will skip file)
def count_oscillators(vital_path):
    try:
        with open(vital_path, 'r') as f:
            data = json.load(f)
        # Check for Vital's oscillator keys, if value = 1.0
        osc_keys = ['osc_1_on', 'osc_2_on', 'osc_3_on']
        count = 0
        settings = data.get("settings", {})
        for k in osc_keys:
            if k in settings and settings[k] == 1.0:
                count += 1
                #print(f"Found oscillator: {k}, count: {count}")
        return count if count > 0 else 1
    except Exception as e:
        print(f"Could not parse {vital_path}: {e}")
        return None

def import_vital_presets_flat(src_dir, dest_dir):
    """
    Recursively copy all .vital files from src_dir to syntheon/data/vital_presets/has_x_osc.
    While copying, replace spaces with '-' and make filenames lowercase.
    """

    count = 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.vital'):
                src_file = os.path.join(root, file)
                # Clean filename
                clean_name = file.replace(' ', '-').lower().rstrip('-')
                # Count oscillators
                osc_count = count_oscillators(src_file)
                if osc_count is None:
                    print(f"Skipping {src_file} (could not determine oscillator count)")
                    continue
                if osc_count == 1:
                    osc_folder = 'has_1_osc'
                elif osc_count == 2:
                    osc_folder = 'has_2_osc'
                elif osc_count == 3:
                    osc_folder = 'has_3_osc'
                else:
                    osc_folder = f'has_{osc_count}_osc'
                dest_subdir = os.path.join(dest_dir, osc_folder)
                os.makedirs(dest_subdir, exist_ok=True)
                dest_file = os.path.join(dest_subdir, clean_name)
                # If the string-transformed filename is already present, skip copying
                if os.path.exists(dest_file):
                    print(f"Skipping {src_file} (already exists as {dest_file})")
                    continue
                shutil.copy2(src_file, dest_file)
                print(f"Copied: {src_file} -> {dest_file}")
                count += 1
    print(f"Total .vital files copied: {count}")

if __name__ == "__main__":
    source_vital_dir = "/Users/sayantanm/Music/Vital"  

    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
    dest_dir = os.path.join(project_root, 'syntheon', 'data', 'vital_presets')
    # dest_vital_dir is now always set by the function
    import_vital_presets_flat(source_vital_dir, dest_dir)