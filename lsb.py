def embed(cover, secret, start, lsb_bits = 1):
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

