# Audio Steganography - Multiple LSB

Deskripsi
-
Program GUI sederhana untuk menyembunyikan (embed) dan mengekstrak (extract) berkas ke/dari file audio MP3 menggunakan teknik LSB. Aplikasi menampilkan dua tab: "Embed Message" untuk menyisipkan berkas rahasia ke audio cover dan "Extract Message" untuk mengambil kembali berkas tersembunyi. Frontend GUI dibuat dengan Tkinter, pemutaran audio menggunakan pygame, dan backend steganografi ditangani oleh modul `lsb.py`.

Tech stack
-
- Bahasa: Python
- GUI: Tkinter
- Audio playback: pygame
- Audio analysis / PSNR: librosa, numpy
- Metadata handling: mutagen (ID3)

Dependensi
-
Daftar paket Python yang diperlukan (terdapat pada `requirements.txt`):
- numpy
- librosa
- pygame
- mutagen

Catatan: `librosa` akan memasang beberapa dependensi tambahan (seperti `scipy`) jika belum tersedia.

Cara menjalankan (Windows)
-
1. Pastikan Python 3.12 terinstall
2. Buat virtual environment (opsional) dan aktifkan:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Pasang dependensi:

```powershell
pip install -r requirements.txt
```

4. Jalankan antarmuka GUI:

```powershell
python frontend.py
```

Penggunaan singkat
-
- Pada tab "Embed Message": pilih file cover (MP3), pilih file rahasia, atur opsi (n-LSB, enkripsi, start acak, stego key), lalu pilih lokasi keluaran untuk stego-audio dan klik "Embed Message".

- Pada tab "Extract Message": pilih file stego (MP3), masukkan kunci jika diperlukan, klik "Extract Message". Setelah ekstraksi berhasil, Anda akan diminta memilih lokasi penyimpanan untuk berkas hasil ekstraksi (default extension akan sesuai tipe berkas yang terdeteksi).
