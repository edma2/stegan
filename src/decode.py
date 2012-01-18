import gzip, StringIO, hashlib, random, struct
import Crypto.Cipher.Blowfish as blowfish
import stegan

"""Returns byte string decompressed with GZip."""
def decompress(str):
    buf = StringIO.StringIO(str)
    gz = gzip.GzipFile(mode = 'r', fileobj = buf)
    output = gz.read()
    gz.close()
    buf.close()
    return output

"""Decrypts byte string with given key and initialization vector. Outputs
plaintext byte string."""
def decrypt(key, iv, ciphertext):
    cipher = blowfish.new(key, blowfish.MODE_OFB, iv)
    return cipher.decrypt(ciphertext)

"""Returns byte string decoded from image."""
def decode(image, password):
    handle = stegan.Steganographer(image)

    # Decode header
    header = handle.read_str(20, stegan.row_major_positions(image))
    length = struct.unpack('i', header[:4])[0]
    iv = header[4:12]
    seed = header[12:]

    # Decode data
    used = set()
    for x in range(len(header)):
        for y in range(len(header)):
            used.add((x, y, stegan.RED))
    data = handle.read_str(length, stegan.random_positions(image, seed, used))

    # Decrypt and decompress data
    key = hashlib.sha256(password).digest()[:7]
    return decompress(decrypt(key, iv, data))
