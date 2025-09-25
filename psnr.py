import librosa
import numpy as np

def mp3_to_array(filename):
    # Load audio (librosa loads as float32, mono by default)
    samples, sr = librosa.load(filename, sr=None, mono=False)
    # If stereo, shape will be (2, n_samples), transpose to (n_samples, 2)
    if samples.ndim == 2:
        samples = samples.T
    return samples.astype(np.float64)

def psnr(cover, stego):
    """
    cover: converted numpy array of original audio samples
    stego: converted numpy array of stego audio samples
    """
    P0 = np.sum(cover**2)
    P1 = np.sum(stego**2)
    diff = (P1 - P0) ** 2
    if diff == 0: # Prevent division by zero
        return float('inf')
    return 10 * np.log10(P1**2 / diff)

# # Load two MP3 files (cover and stego)
# cover_samples = mp3_to_array("flos.mp3")
# stego_samples = mp3_to_array("hasil.mp3")

# # Compute PSNR
# print("PSNR:", psnr(cover_samples, stego_samples), "dB")