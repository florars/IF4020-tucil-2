import random
import math
from mutagen.id3 import ID3
import librosa
import numpy as np
import soundfile as sf

sign_start = b"signature"
sign_end = b"endsignature"

def embed(cover: bytes, secret: bytes, start: int, lsb_bits: int):
    secret_bits = ''.join(f'{byte:08b}' for byte in secret)

    needed_bytes = math.ceil(len(secret_bits)/ lsb_bits)
    cover_arr = bytearray(cover)

    bit_index = 0
    for i in range(start, start + needed_bytes):
        chunk = secret_bits[bit_index:bit_index + lsb_bits]
        if len(chunk) < lsb_bits:
            chunk = chunk.ljust(lsb_bits, '0') 
        cover_arr[i] = (cover_arr[i] & (~((1 << lsb_bits) - 1))) | int(chunk, 2)
        bit_index += lsb_bits

    return bytes(cover_arr)

def embed_flags(cover: bytes, start_idx: int, encrypt: bool, lsb_bits: int):
    # manual soalnya kalo ada alignment issue lagi i WILL crash out
    cover_arr = bytearray(cover)
    
    cover_arr[start_idx] = (cover_arr[start_idx] & 0b11111110) | int(encrypt)
    
    for i in range(4):
        bit = (lsb_bits >> (3 - i)) & 1
        cover_arr[start_idx + 1 + i] = (cover_arr[start_idx + 1 + i] & 0b11111110) | bit
    
    return bytes(cover_arr)

def extract(steg: bytes, lsb_bits: int):
    bitstring = ""
    for b in steg:
        bits = bin(b & ((1 << lsb_bits) - 1))[2:].rjust(lsb_bits, "0")
        bitstring += bits

    secret_bytes = bytearray()
    for i in range(0, len(bitstring), 8):
        byte_chunk = bitstring[i:i+8]
        if len(byte_chunk) < 8:
            break  
        secret_bytes.append(int(byte_chunk, 2))

    return bytes(secret_bytes)

def vig_enc(message, key: str):
    keyb = key.encode()
    key_len = len(keyb)
    crypt = bytes((message[i] + keyb[i % key_len]) % 256 for i in range(len(message)))
    return bytes(b ^ 0b01010101 for b in crypt) #menghindari sync words

def vig_dec(cipher, key: str):
    keyb = key.encode()
    key_len = len(key)
    cipher = bytes(b ^ 0b01010101 for b in cipher)
    return bytes((cipher[i] - keyb[i % key_len]) % 256 for i in range(len(cipher)))

def gen_start(min, coverlen, secretlen, key: str):
    seed = 0
    seed += sum(ord(x) for x in key)
    rng = random.Random(seed)
    return (rng.randint(min, (coverlen-secretlen)) // 8 * 8) # rounding to nearest 8th biar alignmentnya ga meledak pas extract


def embed_message(cover_file: str, secret_file: str, encrypt: bool, randstart: bool, lsb_bits: int, key: str, outname: str):
    # 5 byte pertama: flags, 1 LSB
    # sisanya (sign_start + secret + sign_end) ditaruh setelah start

    if not (1 <= lsb_bits <= 4):
        raise ValueError("LSB bits can only be between 1 to 4 bits.")
    
    cover, sr = librosa.load(cover_file)
    
    # scale to cast to int
    cover_int = (cover * 32767).astype(np.int16)
    cover_int = bytearray(cover_int.tobytes())

    with open(secret_file, "rb") as file:
        secret = file.read()

    if (encrypt):
        secret = vig_enc(secret, key)
    
    # hitung needed bytes untuk memastikan cover file cukup panjang
    needed_bytes = math.ceil(8 * (len(secret) + len (sign_end) + len(sign_start)) / lsb_bits) + 5
    if len(cover_int) < needed_bytes:
        raise ValueError(f"Cover file not big enough, need {needed_bytes/1000}KB of cover")
    print(f"Need {needed_bytes/1024}KB of cover")

    start = 1000
    if (randstart):
        start = gen_start(5, len(cover_int), needed_bytes, key)

    # pertama, embed flags
    stego = embed_flags(cover_int, 0, encrypt, lsb_bits)
    
    # kedua, embed secret dan sign
    stego = embed(stego, sign_start + secret + sign_end, start, lsb_bits)

    for i in range (5):
        print(bin(stego[i]))
    print("---")
    
    # balikin ke int terus ke float.... idk man what is this
    stego_int = np.frombuffer(stego, dtype=np.int16)
    stego_float = stego_int.astype(np.float32) / 32767.0

    sf.write(outname, stego_float, sr)

def find_flags(steg: bytes):
    encrypt = bool(int(steg[0]&1))
    lsb_bits = 0
    for i in range(4):
        bit = steg[1 + i] & 1 
        lsb_bits = (lsb_bits << 1) | bit
    return encrypt, lsb_bits

def extract_message(steg_file: str, key: str):
    steg, sr = librosa.load(steg_file)

    # scale to cast to int
    steg = (steg * 32767).astype(np.int16)
    steg = bytearray(steg.tobytes())

    for i in range (5):
        print(bin(steg[i]))

    encrypt, lsb_bits = find_flags(steg)
    print(encrypt, lsb_bits)

    steg = extract(steg, lsb_bits)

    start_idx = steg.find(sign_start)
    if start_idx == -1:
        raise ValueError("Start signature not found")

    end_idx = steg.find(sign_end, start_idx + len(sign_start))
    if end_idx == -1:
        raise ValueError("End signature not found")
    
    content = steg[start_idx + len(sign_start):end_idx]

    if (encrypt):
        content = vig_dec(content, key)
    
    return content.decode()


embed_message("seiza ni naretara.mp3", "payloads/mesg", False, False, 2, "password", "new1.wav")
print(extract_message("new1.wav", "password"))