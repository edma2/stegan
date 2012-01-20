import Image, random

class Steganographer:
    """Provides an interface for reading and writing raw bytes into image
    pixels. @image is the image to be used as the container, a PIL Image
    object, using the RGB color model."""

    def __init__(self, image, iter):
        self.image = image
        self.pixels = image.load()
        self.iter = iter

    def write_bit(self, bit):
        """Embeds bit in image by settings the LSB of a channel on or off."""
        (x, y, ch) = self.iter.next()
        pixel = list(self.pixels[x, y])
        pixel[ch] = (pixel[ch] | 1) if bit else (pixel[ch] & ~1)
        self.pixels[x, y] = tuple(pixel)

    def read_bit(self):
        """Reads the next encoded bit."""
        (x, y, ch) = self.iter.next()
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

    def randomize(self, seed):
        available = list(self.iter)
        random.seed(seed)
        random.shuffle(available)
        self.iter = (pos for pos in available)
