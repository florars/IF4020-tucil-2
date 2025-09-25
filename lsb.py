from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import random

def embed(cover, secret, start, lsb_bits):
    if not (1 <= lsb_bits <= 4):
        raise ValueError("LSB bits can only be between 1 to 4 bits.")

    secret_bits = ''.join(f'{byte:08b}' for byte in secret)

    needed_bytes = (len(secret_bits) + lsb_bits - 1) // lsb_bits
    if start + needed_bytes > len(cover):
        raise ValueError("Audio file is not long enough. Change the audio file or change the LSB method.")

    cover_arr = bytearray(cover)

    bit_index = 0
    for i in range(start, start + needed_bytes):
        chunk = secret_bits[bit_index:bit_index + lsb_bits]
        if len(chunk) < lsb_bits:
            chunk = chunk.ljust(lsb_bits, '0') 

        # Clear LSBs and insert secret bits
        cover_arr[i] = (cover_arr[i] & (~((1 << lsb_bits) - 1))) | int(chunk, 2)

        bit_index += lsb_bits

    return bytes(cover_arr)

def extract(steg, start, lsb_bits, length):
    if not (1 <= lsb_bits <= 4):
        raise ValueError("LSB bits can only be between 1 to 4 bits.")

    total_bits = length * 8
    needed_bytes = (total_bits + lsb_bits - 1) // lsb_bits

    bits = []
    for i in range(start, start + needed_bytes):
        chunk = steg[i] & ((1 << lsb_bits) - 1)
        bits.append(f'{chunk:0{lsb_bits}b}')

    all_bits = ''.join(bits)[:total_bits]

    secret = int(all_bits, 2).to_bytes(length, byteorder='big')
    return secret

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

def min_start(cover_file):
    with open(cover_file, "rb") as f:
        header = f.read(10)
        if header[0:3] == b"ID3":
            size_bytes = header[6:10]
            size = ((size_bytes[0] & 0x7F) << 21) | \
                   ((size_bytes[1] & 0x7F) << 14) | \
                   ((size_bytes[2] & 0x7F) << 7) | \
                   (size_bytes[3] & 0x7F)
            return 10 + size
        else:
            return 0 

def gen_start(cover_file, coverlen, secretlen, key):
    seed = 0
    seed += sum(int(x) for x in key)
    rng = random.Random(seed)
    return rng.randint(min_start(cover_file), (secretlen - coverlen))


def embed_message(cover_file: str, secret_file: str, encrypt: bool, randstart: bool, lsb_bits: int, key: str, outname: str):
    with open(cover_file, "rb") as file:
        cover = file.read()
    with open(secret_file, "rb") as file:
        secret = file.read()

    print(len(cover), len(secret))
    if (encrypt):
        secret = vig_enc(secret, key)
    
    start = 1000
    if (randstart):
        start = gen_start(cover_file, len(cover), len(secret))

    res = embed(cover, secret, start, lsb_bits)

    with open(outname, "wb+") as file:
        file.write(res)
