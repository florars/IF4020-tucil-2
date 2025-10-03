import librosa
import numpy as np

def psnr(original_file, stego_file):
    # Load audio files
    y_orig, sr_orig = librosa.load(original_file, sr=None, mono=True)
    y_stego, sr_stego = librosa.load(stego_file, sr=None, mono=True)

    # Ensure same length
    min_len = min(len(y_orig), len(y_stego))
    y_orig = y_orig[:min_len]
    y_stego = y_stego[:min_len]

    # MSE
    mse = np.mean((y_orig - y_stego) ** 2)
    if mse == 0:
        return float("inf")  # INF only if same signals

    MAX = 1.0  # librosa normalizes audio between -1 and 1
    psnr = 10 * np.log10((MAX ** 2) / mse)

    return psnr

# # Compute PSNR
# print("PSNR:", psnr("flos.mp3", "hasil.mp3"), "dB")