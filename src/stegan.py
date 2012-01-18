import Image, random

# RGB color model
RED, GREEN, BLUE = 0, 1, 2

class Steganographer:
    """Provides an interface for reading and writing raw bytes into image
    pixels. @image is the image to be used as the container, a PIL Image
    object, using the RGB color model. @positions is a position iterator
    yielding (x, y, channel) coordinates upon request. @positions is not
    required to return unique coordinates. However, we keep a set of
    coordinates already used. If @positions returns a coordinate mapped to a
    bit already read or written, it is skipped."""

    def __init__(self, image, positions):
        self.image = image
        self.pixels = image.load()
        self.positions = positions
        self.used = set() # (x, y, channel)

    def next_position(self):
        """Returns the next available position."""
        while True:
            pos = self.positions.next()
            if pos not in self.used:
                self.used.add(pos)
                break
        return pos

    def write_bit(self, bit):
        """Embeds bit in image by settings the LSB of a channel on or off."""
        (x, y, ch) = self.next_position()
        pixel = list(self.pixels[x, y])
        pixel[ch] = (pixel[ch] | 1) if bit else (pixel[ch] & ~1)
        self.pixels[x, y] = tuple(pixel)

    def read_bit(self):
        """Reads the next encoded bit."""
        (x, y, ch) = self.next_position()
        pixel = self.pixels[x, y]
        bit = pixel[ch] & 1
        return bit

    def write_byte(self, byte):
        """Embeds byte into image starting with the LSB."""
        for i in range(8):
            self.write_bit((byte & (1<<i)) >> i)

    def read_byte(self):
        """Reads the next 8 encoded bits and return as byte."""
        byte = 0
        for i in range(8):
            bit = self.read_bit()
            byte |= bit << i
        return byte

    def write(self, str):
        """Embeds byte string into image."""
        for byte in str:
            self.write_byte(ord(byte))

    def read(self, length):
        """Reads the next length bytes and return as string."""
        str = ''
        for i in range(length):
            str += chr(self.read_byte())
        return str

### Sample position iterators ###

def row_major(image):
    """Generates row-major coordinates on the red channel."""
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            yield (x, y, RED)
    # TODO: throw exception here

def random_with_seed(image, seed):
    """Generates random coordinates given an initial seed."""
    random.seed(seed)
    while True:
        x = random.randint(0, image.size[0]-1)
        y = random.randint(0, image.size[1]-1)
        channel = random.randint(0, 2) # RED, GREEN, BLUE
        yield (x, y, channel)
    # FIXME: this will never terminate
