import random
import math
import os
from mutagen.id3 import ID3

sign_start = b"signature"
sign_end = b"endsignature"
EXT_FLAG = {
    "txt": 0b000,
    "pdf": 0b001,
    "doc": 0b010,
    "png": 0b011,
    "jpg": 0b100,
    "exe": 0b101,
    "dll": 0b110
}

EXT_FLAG_INV = {v: k for k, v in EXT_FLAG.items()}

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

def embed_flags(cover: bytes, start_idx: int, encrypt: bool, lsb_bits: int, ext: str):
    # manual soalnya kalo ada alignment issue lagi i WILL crash out
    cover_arr = bytearray(cover)
    
    # 1 bit encrypt info
    cover_arr[start_idx] = (cover_arr[start_idx] & 0b11111110) | int(encrypt)
    
    # 2 bit lsb_bits -1 
    lsb = (lsb_bits - 1) & 0b11  
    for i in range(2):
        bit = (lsb >> (1 - i)) & 1
        cover_arr[start_idx + 1 + i] = (cover_arr[start_idx + 1 + i] & 0b11111110) | bit
    
    # 3 bit original extension
    ext_code = EXT_FLAG.get(ext, 0b111)  # 0b111 kalo gaada di list
    print(ext, ext_code)
    for i in range(3):
        bit = (ext_code >> (2 - i)) & 1
        cover_arr[start_idx + 3 + i] = (cover_arr[start_idx + 3 + i] & 0b11111110) | bit

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
    # 6 byte pertama: flags, 1 LSB
    # sisanya (sign_start + secret + sign_end) ditaruh setelah start

    if not (1 <= lsb_bits <= 4):
        raise ValueError("LSB bits can only be between 1 to 4 bits.")
    
    with open(cover_file, "rb") as file:
        cover = file.read()

    with open(secret_file, "rb") as file:
        secret = file.read()

    ext = os.path.splitext(secret_file)[1]
    ext = ext[1:].lower() 

    if (encrypt):
        secret = vig_enc(secret, key)
    
    # hitung needed bytes untuk memastikan cover file cukup panjang
    needed_bytes = math.ceil(8 * (len(secret) + len (sign_end) + len(sign_start)) / lsb_bits) + 6
    if len(cover) < needed_bytes:
        raise ValueError(f"Cover file not big enough, need {needed_bytes/1000}KB of cover")
    print(f"Need {needed_bytes/1024}KB of cover")

    # cari panjang metadata
    header = ID3(cover_file)
    flag_byte = header.size + 1

    start = 1000
    if (randstart):
        start = gen_start(flag_byte + 6, len(cover), needed_bytes, key)

    # pertama, embed flags
    stego = embed_flags(cover, flag_byte, encrypt, lsb_bits, ext)
    
    # kedua, embed secret dan sign
    stego = embed(stego, sign_start + secret + sign_end, start, lsb_bits)

    with open(outname, "wb+") as file:
        file.write(stego)

def find_flags(steg_file: str, steg: bytes):
    header = ID3(steg_file)
    idx = header.size + 1

    encrypt = bool(int(steg[idx]&1))

    lsb = 0
    for i in range(2):
        bit = steg[idx + 1 + i] & 1
        lsb = (lsb << 1) | bit
    lsb_bits = lsb + 1  

    ext = 0
    for i in range(3):
        bit = steg[idx + 3 + i] & 1
        ext = (ext << 1) | bit
    extension = EXT_FLAG_INV.get(ext, "unk")

    return encrypt, lsb_bits, extension

def extract_message(steg_file: str, key: str):
    with open(steg_file, "rb") as file:
        steg = file.read()
    
    encrypt, lsb_bits, ext = find_flags(steg_file, steg)
    print(encrypt, lsb_bits, ext)

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
    
    return content, ext


if __name__ == "__main__":
    embed_message("birdbrain.mp3", "payloads/small.pdf", True, False, 3, "password", "generated/hasil.mp3")
    content, ext = extract_message("generated/hasil.mp3", "password")
    filename = "generated/hasil2." + str(ext)
    with open(filename, "wb+") as file:
        file.write(content)