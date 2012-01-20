import gzip, StringIO, hashlib, random, struct
import Crypto.Cipher.Blowfish as blowfish
import stegan

"""Returns byte string compressed with GZip."""
def compress(str):
    buf = StringIO.StringIO()
    gz = gzip.GzipFile(mode = 'w', fileobj = buf)
    gz.write(str)
    gz.close()
    output = buf.getvalue()
    buf.close()
    return output

"""Encrypts byte string with given 64-bit key and initialization vector.
Outputs ciphertext byte string."""
def encrypt(key, iv, plaintext):
    cipher = blowfish.new(key, blowfish.MODE_OFB, iv)
    if len(plaintext) == 8:
        padding = ''
    else:
        padding = '\x00' * (8 - len(plaintext) % 8)
    return cipher.encrypt(plaintext + padding)

"""Encode byte string into image."""
def encode(im, password, bytes):
    w, h = im.size
    linear = ((x,y,c) for x in range(w) for y in range(h) for c in range(3))
    writer = stegan.Steganographer(im, linear)

    # Compress and encrypt data with password
    key = hashlib.sha256(password).digest()[:7]
    iv = struct.pack("Q", random.getrandbits(64))
    data = encrypt(key, iv, compress(bytes))

    # Encode header in row-major order
    seed = struct.pack("Q", random.getrandbits(64))
    header = struct.pack('i', len(data)) + iv + seed
    writer.write(header)

    # Encode payload in random order
    writer.randomize(seed)
    writer.write(data)
