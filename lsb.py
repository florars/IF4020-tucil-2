import random
import math

sign_start = b"signature"
sign_end = b"endsignature"

def embed(cover: bytes, secret: bytes, start: int, lsb_bits: int):
    secret_bits = ''.join(f'{byte:08b}' for byte in secret)

    needed_bytes = (len(secret_bits) + lsb_bits - 1) // lsb_bits
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

def gen_start(min, coverlen, secretlen, key):
    seed = 0
    seed += sum(int(x) for x in key)
    rng = random.Random(seed)
    return rng.randint(min, (secretlen - coverlen))


def embed_message(cover_file: str, secret_file: str, encrypt: bool, randstart: bool, lsb_bits: int, key: str, outname: str):
    # 5 byte pertama: flags, 1 LSB
    # sisanya (sign_start + secret + sign_end) ditaruh setelah start

    if not (1 <= lsb_bits <= 4):
        raise ValueError("LSB bits can only be between 1 to 4 bits.")
    
    with open(cover_file, "rb") as file:
        cover = file.read()

    with open(secret_file, "rb") as file:
        secret = file.read()

    if (encrypt):
        secret = vig_enc(secret, key)
    
    flag_byte = min_start(cover_file)

    start = 1000
    if (randstart):
        start = gen_start(flag_byte + 5, len(cover), len(sign_start + secret + sign_end))

    # pertama, embed flags
    stego = embed_flags(cover, flag_byte, encrypt, lsb_bits)
    
    # kedua, embed secret dan sign
    stego = embed(stego, sign_start + secret + sign_end, start, lsb_bits)

    with open(outname, "wb+") as file:
        file.write(stego)

def find_flags(steg_file: str, steg: bytes):
    idx = min_start(steg_file)
    encrypt = bool(int(steg[idx]&1))
    lsb_bits = 0
    for i in range(4):
        bit = steg[idx + 1 + i] & 1 
        lsb_bits = (lsb_bits << 1) | bit
    return encrypt, lsb_bits

def extract_message(steg_file: str, key: str):
    with open(steg_file, "rb") as file:
        steg = file.read()
    
    encrypt, lsb_bits = find_flags(steg_file, steg)
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

embed_message("seiza ni naretara.mp3", "mesg", False, False, 3, "password", "hasil.mp3")
print(extract_message("hasil.mp3", "password"))