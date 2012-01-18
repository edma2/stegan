# stegan.py
# Author: Eugene Ma
import sys, os, struct, random, gzip, StringIO, hashlib
import Image
import Crypto.Cipher.Blowfish as blowfish

RED, GREEN, BLUE = 0, 1, 2

"""An ImageHandle provides an interface for embedding raw bytes into image
pixels and recovery of data."""
class ImageHandle:
    """Initialize with Image object and an iterator yielding (x, y, channel)
    tuples. The iterator parameter allows different encoding formats to be
    used."""
    def __init__(self, image):
        self.image = image
        self.pixels = image.load()

    """Embeds bit in image by settings the LSB of a channel on or off."""
    def embed_bit(self, bit):
        (x, y, ch) = self.positions.next()
        pixel = list(self.pixels[x, y])
        pixel[ch] = (pixel[ch] | 1) if bit else (pixel[ch] & ~1)
        self.pixels[x, y] = tuple(pixel)

    """Recover the next encoded bit."""
    def recover_bit(self):
        (x, y, ch) = self.positions.next()
        pixel = self.pixels[x, y]
        bit = pixel[ch] & 1
        return bit

    """Embeds byte into image starting with the LSB."""
    def embed_byte(self, byte):
        for i in range(8):
            self.embed_bit((byte & (1<<i)) >> i)

    """Recover the next 8 encoded bits and return as byte."""
    def recover_byte(self):
        byte = 0
        for i in range(8):
            bit = self.recover_bit()
            byte |= bit << i
        return byte

    """Embeds byte string into image. The ordering of pixels used is specified
    by the @positions iterator."""
    def embed_bytestr(self, bytestr, positions):
        self.positions = positions
        for byte in bytestr:
            self.embed_byte(ord(byte))

    """Recover the next length bytes and return as string, using @positions as
    pixel iterator."""
    def recover_bytestr(self, length, positions):
        self.positions = positions
        bytestr = ''
        for i in range(length):
            bytestr += chr(self.recover_byte())
        return bytestr

"""Returns byte string compressed with GZip."""
def compress(bytestr):
    buf = StringIO.StringIO()
    gz = gzip.GzipFile(mode = 'w', fileobj = buf)
    gz.write(bytestr)
    gz.close()
    output = buf.getvalue()
    buf.close()
    return output

"""Returns byte string decompressed with GZip."""
def decompress(bytestr):
    buf = StringIO.StringIO(bytestr)
    gz = gzip.GzipFile(mode = 'r', fileobj = buf)
    output = gz.read()
    gz.close()
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

"""Decrypts byte string with given key and initialization vector. Outputs
plaintext byte string."""
def decrypt(key, iv, ciphertext):
    cipher = blowfish.new(key, blowfish.MODE_OFB, iv)
    return cipher.decrypt(ciphertext)

"""Encode byte string into image."""
def encode(image, password, bytestr):
    handle = ImageHandle(image)

    # Compress and encrypt data with password
    key = hashlib.sha256(password).digest()[:7]
    iv = struct.pack("Q", random.getrandbits(64))
    data = encrypt(key, iv, compress(bytestr))

    # Encode header in row-major order
    # header:  length (4), iv (8), seed (8)
    seed = struct.pack("Q", random.getrandbits(64))
    header = struct.pack('i', len(data)) + iv + seed
    handle.embed_bytestr(header, row_major_positions(image))

    # Encode payload in random order
    used = set()
    for x in range(len(header)):
        for y in range(len(header)):
            used.add((x, y, RED))
    handle.embed_bytestr(data, random_positions(image, seed, used))

"""Returns byte string decoded from image."""
def decode(image, password):
    handle = ImageHandle(image)

    # Decode header
    header = handle.recover_bytestr(20, row_major_positions(image))
    length = struct.unpack('i', header[:4])[0]
    iv = header[4:12]
    seed = header[12:]

    # Decode data
    used = set()
    for x in range(len(header)):
        for y in range(len(header)):
            used.add((x, y, RED))
    data = handle.recover_bytestr(length, random_positions(image, seed, used))

    # Decrypt and decompress data
    key = hashlib.sha256(password).digest()[:7]
    return decompress(decrypt(key, iv, data))

"""Generates row-major order pixel coordinates on the red channel."""
def row_major_positions(image):
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            yield (x, y, RED) # TODO: throw exception when out of bounds

"""Generates random positions given an initial seed and a set of pixels already
used"""
def random_positions(image, seed, used):
    random.seed(seed)
    while True:
        x = random.randint(0, image.size[0]-1)
        y = random.randint(0, image.size[1]-1)
        channel = random.randint(0, 2) # RED, GREEN, BLUE
        pos = (x, y, channel)
        if pos in used:
            continue
        used.add(pos)
        yield pos
