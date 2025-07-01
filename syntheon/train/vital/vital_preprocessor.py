import os
import shutil

def import_vital_presets_flat(src_dir, dest_dir):
    """
    Recursively copy all .vital files from src_dir to dest_dir (flat, no subfolders).
    """
    os.makedirs(dest_dir, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.vital'):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                # If duplicate filenames exist, add a unique suffix
                if os.path.exists(dest_file):
                    # base, ext = os.path.splitext(file)
                    # i = 1
                    # while os.path.exists(os.path.join(dest_dir, f"{base}_{i}{ext}")):
                    #     i += 1
                    # dest_file = os.path.join(dest_dir, f"{base}_{i}{ext}")
                    continue
                shutil.copy2(src_file, dest_file)
                print(f"Copied: {src_file} -> {dest_file}")
                count += 1
    print(f"Total .vital files copied: {count}")

if __name__ == "__main__":
    # Set these paths as needed
    source_vital_dir = "/Users/sayantanm/Music/Vital"  
    dest_vital_dir = "syntheon/data/vital_presets"

    import_vital_presets_flat(source_vital_dir, dest_vital_dir)