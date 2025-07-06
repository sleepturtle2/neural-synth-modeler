import os
import yaml
import torch
from torch.utils.data import DataLoader, Dataset, random_split
from neural_synth_modeler.inferencer.vital.models.model import WTSv2
from neural_synth_modeler.inferencer.vital.models.preprocessor import spec, sr, n_mfcc
from neural_synth_modeler.inferencer.vital.models.core import multiscale_fft
import numpy as np
import librosa
from tqdm import tqdm
import datetime

# 1. Load config
# Get project root (2 levels up from this script)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
config_path = os.path.join(project_root, "neural_synth_modeler/inferencer/vital/config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

device = torch.device(config["device"] if torch.cuda.is_available() else "cpu")

# 2. Define your dataset
class VitalAudioParamDataset(Dataset):
    def __init__(self, audio_dir, param_dir):
        self.audio_files = sorted([os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith(".wav")])
        self.param_files = sorted([os.path.join(param_dir, f) for f in os.listdir(param_dir) if f.endswith(".npy")])
        assert len(self.audio_files) == len(self.param_files), "Mismatch in audio/param files"

    def __len__(self):
        return len(self.audio_files)

    def __getitem__(self, idx):
        y, _ = librosa.load(self.audio_files[idx], sr=sr)
        params = np.load(self.param_files[idx], allow_pickle=True).item()
        pitch = torch.tensor(params["pitch"]).float()
        loudness = torch.tensor(params["loudness"]).float()
        times = torch.tensor(params["times"]).float()
        onset_frames = torch.tensor(params["onset_frames"]).long()
        mfcc = torch.tensor(params["mfcc"]).float()
        y = torch.tensor(y).float()
        return y, mfcc, pitch, loudness, times, onset_frames

# 3. Instantiate dataset and train/test split
# Update these paths to be absolute or relative to project root if needed
full_dataset = VitalAudioParamDataset("path/to/audio", "path/to/params")
train_size = int(0.8 * len(full_dataset))
test_size = len(full_dataset) - train_size
train_dataset, test_dataset = random_split(full_dataset, [train_size, test_size])

train_loader = DataLoader(train_dataset, batch_size=config["train"]["batch_size"], shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=config["test"]["batch_size"], shuffle=False)

# 4. Instantiate model
model = WTSv2(
    hidden_size=config["train"]["hidden_size"],
    n_harmonic=config["train"]["n_harmonic"],
    n_bands=config["train"]["n_bands"],
    sampling_rate=config["common"]["sampling_rate"],
    block_size=config["common"]["block_size"],
    mode="wavetable",
    duration_secs=config["common"]["duration_secs"],
    num_wavetables=config["train"]["n_wavetables"],
    wavetable_smoothing=False,
    preload_wt=False,
    enable_amplitude=True,
    is_round_secs=False,
    device=str(device)
).to(device)

# 5. Load checkpoint if exists
checkpoint_path = os.path.join(project_root, "neural_synth_modeler/inferencer/vital/checkpoints/model.pt")
if os.path.exists(checkpoint_path):
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    print(f"Loaded checkpoint weights from {checkpoint_path}!")

optimizer = torch.optim.Adam(model.parameters(), lr=config["train"]["start_lr"])
loss_fn = torch.nn.MSELoss()  # Or use your custom loss, e.g., multiscale_fft

epochs = config["train"]["epochs"]
for epoch in range(epochs):
    model.train()
    train_loss = 0.0
    train_batches = 0
    with tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]", leave=False) as tbar:
        for batch in tbar:
            y, mfcc, pitch, loudness, times, onset_frames = [b.to(device) for b in batch]
            optimizer.zero_grad()
            signal, adsr, final_signal, attention_output, wavetables, wavetables_old, smoothing_coeff = model(
                y, mfcc, pitch, loudness, times, onset_frames
            )
            loss = loss_fn(final_signal, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            train_batches += 1
            tbar.set_postfix(loss=loss.item())
    avg_train_loss = train_loss / train_batches

    # Evaluate on test set
    model.eval()
    test_loss = 0.0
    test_batches = 0
    with torch.no_grad():
        with tqdm(test_loader, desc=f"Epoch {epoch+1}/{epochs} [Test]", leave=False) as tbar:
            for batch in tbar:
                y, mfcc, pitch, loudness, times, onset_frames = [b.to(device) for b in batch]
                signal, adsr, final_signal, attention_output, wavetables, wavetables_old, smoothing_coeff = model(
                    y, mfcc, pitch, loudness, times, onset_frames
                )
                loss = loss_fn(final_signal, y)
                test_loss += loss.item()
                test_batches += 1
                tbar.set_postfix(loss=loss.item())
    avg_test_loss = test_loss / test_batches

    print(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | Test Loss: {avg_test_loss:.4f}")

    # Save checkpoint with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(project_root, f"neural_synth_modeler/inferencer/vital/checkpoints/model_epoch{epoch+1}_{timestamp}.pt")
    torch.save(model.state_dict(), save_path) 