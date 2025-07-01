import os
import random
import subprocess
from pathlib import Path

# USER CONFIGURATION
PRESET_FOLDER = Path("/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_presets")  # .vital preset folder
OUTPUT_FOLDER = Path("/Users/sayantanm/code/neural-synth-modeler/syntheon/data/vital_preset_audio")   # output folder
REAPER_PATH = "/Applications/REAPER.app/Contents/MacOS/REAPER"  # Reaper executable
VITAL_VST_PATH = "/Library/Audio/Plug-Ins/VST3/Vital.vst3"  # Vital VST3
PROJECT_FILE = Path("/Users/sayantanm/code/neural-synth-modeler/syntheon/train/reaper-preset-processing/training.RPP")  # Single Reaper project with Vital loaded
NUM_VARIATIONS = 3  # Number of random renders per preset
SILENCE_PROB = 0.2  # Probability of rendering silence
MIDI_CHANNEL = 0     # MIDI channel (0 = channel 1)

# MIDI note range and duration
MIN_NOTE = 36  # C2
MAX_NOTE = 96  # C7
MIN_DURATION = 1.0  # seconds
MAX_DURATION = 4.0  # seconds
MIN_VELOCITY = 80
MAX_VELOCITY = 127

# Ensure output folder exists
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Helper to get all .vital files
preset_files = list(PRESET_FOLDER.glob("*.vital"))
if not preset_files:
    raise FileNotFoundError(f"No .vital presets found in {PRESET_FOLDER}")

# Helper to write a simple MIDI file (single note)
def write_midi(filename, note, velocity, duration, channel=0, tempo=120):
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # Set tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))
    # Note on
    track.append(mido.Message('note_on', note=note, velocity=velocity, time=0, channel=channel))
    # Note off
    ticks = int(mido.second2tick(duration, mid.ticks_per_beat, mido.bpm2tempo(tempo)))
    track.append(mido.Message('note_off', note=note, velocity=0, time=ticks, channel=channel))
    mid.save(filename)

# Main loop
for preset_path in preset_files:
    preset_name = preset_path.stem
    for v in range(1, NUM_VARIATIONS + 1):
        do_silence = random.random() < SILENCE_PROB
        # Prepare MIDI if not silence
        midi_file = None
        if not do_silence:
            note = random.randint(MIN_NOTE, MAX_NOTE)
            velocity = random.randint(MIN_VELOCITY, MAX_VELOCITY)
            duration = random.uniform(MIN_DURATION, MAX_DURATION)
            midi_file = OUTPUT_FOLDER / f"{preset_name}_var{v}.mid"
            write_midi(midi_file, note, velocity, duration, channel=MIDI_CHANNEL)
        # Edit the single project file to:
        # - Load the correct Vital preset
        # - Insert the MIDI file if needed
        # (This requires parsing and editing the RPP file, which is text-based)
        with open(PROJECT_FILE, 'r') as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            # Replace preset path placeholder
            if "VITAL_PRESET_PATH" in line:
                line = line.replace("VITAL_PRESET_PATH", str(preset_path))
            # Replace MIDI file placeholder
            if "MIDI_FILE_PATH" in line and midi_file is not None:
                line = line.replace("MIDI_FILE_PATH", str(midi_file))
            new_lines.append(line)
        # Set render output path explicitly in the RPP
        render_path = OUTPUT_FOLDER / f"{preset_name}_var{v}{'_silence' if do_silence else ''}.wav"
        for i, line in enumerate(new_lines):
            if line.strip().startswith('RENDER_FILE'):
                new_lines[i] = f'  RENDER_FILE "{render_path}"'
        # Write the modified project to a temp file
        temp_project_file = OUTPUT_FOLDER / "_temp_render_project.RPP"
        with open(temp_project_file, 'w') as f:
            f.writelines(new_lines)
        # Call Reaper in batch mode to render
        cmd = [REAPER_PATH, '-renderproject', str(temp_project_file)]
        print(f"Rendering {render_path}...")
        subprocess.run(cmd, check=True)
        print(f"Rendered: {render_path}")
        # Clean up temp project file
        temp_project_file.unlink()
        # Remove MIDI file if silence
        if do_silence and midi_file is not None and midi_file.exists():
            midi_file.unlink()

print("Batch rendering complete!") 