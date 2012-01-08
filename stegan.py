# stegan.py
# Author: Eugene Ma
import sys, os, struct, random, gzip, StringIO, hashlib
import Image
import Crypto.Cipher.Blowfish as blowfish

"""Encode byte string into image."""
def encode(image, password, bytestr):
    iv = struct.pack("Q", random.getrandbits(64))
    key = hashlib.sha256(password).digest()[:7]
    data = encrypt(key, iv, compress(bytestr))
    handle = ImageHandle(image, row_major_positions(image))
    handle.embed_bytestr(struct.pack('i', len(data)) + iv)
    handle.embed_bytestr(data)

"""Returns byte string decoded from image."""
def decode(image, password):
    handle = ImageHandle(image, row_major_positions(image))
    header = handle.recover_bytestr(12)
    length = struct.unpack('i', header[:4])[0]
    data = handle.recover_bytestr(length)
    iv = header[4:]
    key = hashlib.sha256(password).digest()[:7]
    return decompress(decrypt(key, iv, data))

"""Generates row-major order pixel coordinates."""
def row_major_positions(image):
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            yield (x, y) # TODO: throw exception when out of bounds

"""An ImageHandle provides an interface for embedding raw bytes into image
pixels and recovery of data."""
class ImageHandle:
    """Initialize with Image object and an iterator yielding (x, y) tuples. The
    iterator parameter allows different encoding formats to be used."""
    def __init__(self, image, positions):
        self.image = image
        self.pixels = image.load()
        self.positions = positions

    """Embeds bit in image by settings the LSB of the red channel on or off.""" 
    def embed_bit(self, bit):
        (x, y) = self.positions.next()
        (red, green, blue) = self.pixels[x, y]
        red = (red | 1) if bit else (red & ~1)
        self.pixels[x, y] = (red, green, blue)

    """Recover the next encoded bit."""
    def recover_bit(self):
        (x, y) = self.positions.next()
        (red, green, blue) = self.pixels[x, y]
        bit = red & 1
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

    """Embeds byte string into image."""
    def embed_bytestr(self, bytestr):
        for byte in bytestr:
            self.embed_byte(ord(byte))

    """Recover the next length bytes and return as string."""
    def recover_bytestr(self, length):
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
