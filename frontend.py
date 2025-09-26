import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
# Import LSB functions
from lsb import embed_message, extract_message

# init pygame mixer
pygame.mixer.init()

# global untuk track audio
current_audio = None

def browse_file(entry_widget, filetypes):
    filename = filedialog.askopenfilename(filetypes=filetypes)
    if filename:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, filename)

def save_file(entry_widget, default_ext=".mp3"):
    filename = filedialog.asksaveasfilename(defaultextension=default_ext)
    if filename:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, filename)

def play_audio(path_entry):
    global current_audio
    filepath = path_entry.get()
    if filepath:
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            current_audio = filepath
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memutar audio:\n{e}")

def stop_audio():
    pygame.mixer.music.stop()

# main window

# Color theme
BG_YELLOW = "#FFF8B7"  # LemonChiffon
BG_GREEN = "#CCFCCC"   # LightGreen
ACCENT = "#B6FF00"     # Vivid yellow-green
FG_DARK = "#2E4600"    # Dark green for text

root = tk.Tk()
root.title("Audio Steganography - Multiple LSB")
root.geometry("650x450")
root.configure(bg=BG_YELLOW)

# Style for ttk widgets
style = ttk.Style()
style.theme_use('default')
style.configure('TNotebook', background=BG_YELLOW, borderwidth=0)
style.configure('TNotebook.Tab', background=BG_GREEN, foreground=FG_DARK, font=('Segoe UI', 10, 'bold'))
style.map('TNotebook.Tab', background=[('selected', ACCENT)], foreground=[('selected', FG_DARK)])
style.configure('TFrame', background=BG_YELLOW)
style.configure('TLabel', background=BG_YELLOW, foreground=FG_DARK, font=('Segoe UI', 10))
style.configure('TButton', background=BG_GREEN, foreground=FG_DARK, font=('Segoe UI', 10, 'bold'))
style.map('TButton', background=[('active', ACCENT)])
style.configure('TCheckbutton', background=BG_YELLOW, foreground=FG_DARK, font=('Segoe UI', 10))

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---------------- EMBED ----------------
embed_frame = ttk.Frame(notebook, style='TFrame')
notebook.add(embed_frame, text="Embed Message")

# Input cover audio
ttk.Label(embed_frame, text="Cover Audio (MP3):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
cover_entry = ttk.Entry(embed_frame, width=50)
cover_entry.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(embed_frame, text="Browse", command=lambda: browse_file(cover_entry, [("MP3 files", "*.mp3")]), style='TButton', cursor='hand2').grid(row=0, column=2, padx=5, pady=5)

# Audio Player controls for cover audio
player_frame = ttk.Frame(embed_frame, style='TFrame')
player_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
ttk.Button(player_frame, text="Play", command=lambda: play_audio(cover_entry), style='TButton', cursor='hand2').pack(side="left", padx=2)
ttk.Button(player_frame, text="Stop", command=stop_audio, style='TButton', cursor='hand2').pack(side="left", padx=2)

# Input secret file
ttk.Label(embed_frame, text="Secret File:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
secret_entry = ttk.Entry(embed_frame, width=50)
secret_entry.grid(row=2, column=1, padx=5, pady=5)
ttk.Button(embed_frame, text="Browse", command=lambda: browse_file(secret_entry, [("All files", "*.*")]), style='TButton', cursor='hand2').grid(row=2, column=2, padx=5, pady=5)

# Options
encrypt_var = tk.BooleanVar()
ttk.Checkbutton(embed_frame, text="Use Encryption (Vigenère)", variable=encrypt_var, style='TCheckbutton', cursor='hand2').grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")

random_seed_var = tk.BooleanVar()
ttk.Checkbutton(embed_frame, text="Random Start Position (Seed)", variable=random_seed_var, style='TCheckbutton', cursor='hand2').grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")


ttk.Label(embed_frame, text="n-LSB:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
lsb_spin = tk.Spinbox(embed_frame, from_=1, to=4, width=5, bg=BG_GREEN, fg=FG_DARK, font=('Segoe UI', 10))
lsb_spin.grid(row=5, column=1, sticky="w")

# Key input
ttk.Label(embed_frame, text="Stego Key / Seed:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
key_entry = ttk.Entry(embed_frame, width=30)
key_entry.grid(row=6, column=1, padx=5, pady=5, sticky="w")

# Save as
ttk.Label(embed_frame, text="Save Stego-Audio As:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
save_entry = ttk.Entry(embed_frame, width=50)
save_entry.grid(row=7, column=1, padx=5, pady=5)
ttk.Button(embed_frame, text="Browse", command=lambda: save_file(save_entry), style='TButton', cursor='hand2').grid(row=7, column=2, padx=5, pady=5)

# Action button

# --- Embed action ---
def embed_action():
    cover_file = cover_entry.get()
    secret_file = secret_entry.get()
    encrypt = encrypt_var.get()
    randstart = random_seed_var.get()
    try:
        lsb_bits = int(lsb_spin.get())
    except Exception:
        lsb_bits = 1
    key = key_entry.get()
    outname = save_entry.get()
    if not (cover_file and secret_file and outname):
        messagebox.showerror("Error", "Please fill all required fields.")
        return
    try:
        embed_message(cover_file, secret_file, encrypt, randstart, lsb_bits, key, outname)
        messagebox.showinfo("Success", f"Message embedded successfully!\nSaved as: {outname}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to embed message:\n{e}")

ttk.Button(embed_frame, text="Embed Message", command=embed_action, style='TButton', cursor='hand2').grid(row=8, column=0, columnspan=3, pady=15)


# ---------------- EXTRACT ----------------
extract_frame = ttk.Frame(notebook, style='TFrame')
notebook.add(extract_frame, text="Extract Message")

# Input stego audio
ttk.Label(extract_frame, text="Stego Audio (MP3):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
stego_entry = ttk.Entry(extract_frame, width=50)
stego_entry.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(extract_frame, text="Browse", command=lambda: browse_file(stego_entry, [("MP3 files", "*.mp3")]), style='TButton', cursor='hand2').grid(row=0, column=2, padx=5, pady=5)

# Audio Player controls for stego audio
player_frame2 = ttk.Frame(extract_frame, style='TFrame')
player_frame2.grid(row=1, column=1, padx=5, pady=5, sticky="w")
ttk.Button(player_frame2, text="Play", command=lambda: play_audio(stego_entry), style='TButton', cursor='hand2').pack(side="left", padx=2)
ttk.Button(player_frame2, text="Stop", command=stop_audio, style='TButton', cursor='hand2').pack(side="left", padx=2)

# Key input
ttk.Label(extract_frame, text="Stego Key / Seed:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
extract_key_entry = ttk.Entry(extract_frame, width=30)
extract_key_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Save as
ttk.Label(extract_frame, text="Save Secret File As:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
extract_save_entry = ttk.Entry(extract_frame, width=50)
extract_save_entry.grid(row=3, column=1, padx=5, pady=5)
ttk.Button(extract_frame, text="Browse", command=lambda: save_file(extract_save_entry, default_ext=".bin"), style='TButton', cursor='hand2').grid(row=3, column=2, padx=5, pady=5)

# Action button

# --- Extract action ---
def extract_action():
    steg_file = stego_entry.get()
    key = extract_key_entry.get()
    outname = extract_save_entry.get()
    if not (steg_file and outname):
        messagebox.showerror("Error", "Please fill all required fields.")
        return
    try:
        result = extract_message(steg_file, key)
        # Save result to file
        with open(outname, "w", encoding="utf-8") as f:
            f.write(result)
        messagebox.showinfo("Success", f"Message extracted and saved as: {outname}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract message:\n{e}")

ttk.Button(extract_frame, text="Extract Message", command=extract_action, style='TButton', cursor='hand2').grid(row=4, column=0, columnspan=3, pady=15)

root.mainloop()
