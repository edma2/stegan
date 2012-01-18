# stegan.py
# Author: Eugene Ma
import Image, random

RED, GREEN, BLUE = 0, 1, 2

"""An Steganographer provides an interface for reading and writing raw bytes
into image pixels."""
class Steganographer:
    def __init__(self, image):
        self.image = image
        self.pixels = image.load()

    """Embeds bit in image by settings the LSB of a channel on or off."""
    def write_bit(self, bit):
        (x, y, ch) = self.positions.next()
        pixel = list(self.pixels[x, y])
        pixel[ch] = (pixel[ch] | 1) if bit else (pixel[ch] & ~1)
        self.pixels[x, y] = tuple(pixel)

    """Read the next encoded bit."""
    def read_bit(self):
        (x, y, ch) = self.positions.next()
        pixel = self.pixels[x, y]
        bit = pixel[ch] & 1
        return bit

    """Embeds byte into image starting with the LSB."""
    def write_byte(self, byte):
        for i in range(8):
            self.write_bit((byte & (1<<i)) >> i)

    """Read the next 8 encoded bits and return as byte."""
    def read_byte(self):
        byte = 0
        for i in range(8):
            bit = self.read_bit()
            byte |= bit << i
        return byte

    """Embeds byte string into image."""
    def write_str(self, str, positions):
        self.positions = positions
        for byte in str:
            self.write_byte(ord(byte))

    """Read the next length bytes and return as string."""
    def read_str(self, length, positions):
        self.positions = positions
        str = ''
        for i in range(length):
            str += chr(self.read_byte())
        return str

"""Generates row-major order pixel coordinates on the red channel, starting
from (0, 0). """
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
