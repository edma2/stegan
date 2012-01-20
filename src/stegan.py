import random, struct, hashlib, gzip, StringIO
import Image, Crypto.Cipher.Blowfish as blowfish

class Steganographer(object):
    """Provides an interface for reading and writing raw bytes into image
    pixels."""

    def __init__(self, im, iter):
        self.im = im
        self.pixels = self.im.load()
        w, h = self.im.size
        self.iter = iter

    def write_bit(self, bit):
        (x, y, ch) = self.iter.next()
        pixel = list(self.pixels[x, y])
        pixel[ch] = (pixel[ch] | 1) if bit else (pixel[ch] & ~1)
        self.pixels[x, y] = tuple(pixel)

    def read_bit(self):
        (x, y, ch) = self.iter.next()
        pixel = self.pixels[x, y]
        bit = pixel[ch] & 1
        return bit

    def write_byte(self, byte):
        for i in range(8):
            self.write_bit((byte & (1<<i)) >> i)

    def read_byte(self):
        byte = 0
        for i in range(8):
            bit = self.read_bit()
            byte |= bit << i
        return byte

    def write(self, str):
        for byte in str:
            self.write_byte(ord(byte))

    def read(self, length):
        str = ''
        for i in range(length):
            str += chr(self.read_byte())
        return str

    def randomize(self, seed):
        available = list(self.iter)
        random.seed(seed)
        random.shuffle(available)
        self.iter = (pos for pos in available)

class Writer(Steganographer):
    """Writes a single string of bytes to image, including a header used for
    decoding"""

    def __init__(self, im, passphrase):
        self.key = hashlib.sha256(passphrase).digest()[:7]
        self.iv = struct.pack("Q", random.getrandbits(64))
        w, h = im.size
        linear = ((x,y,c) for x in range(w) for y in range(h) for c in range(3))
        super(Writer, self).__init__(im, linear)

    def compress(self, str):
        """Returns the string in compressed form"""
        buf = StringIO.StringIO()
        # Write compressed string to string buffer
        gz = gzip.GzipFile(mode = 'w', fileobj = buf)
        gz.write(str)
        gz.close()
        # Get string from buffer
        return buf.getvalue()

    def encrypt(self, plaintext):
        """Encrypts plaintext and returns ciphertext."""
        def bf_padding(data):
            """Returns padding necessary for Blowfish algorithm."""
            if len(data) == 8:
                return ''
            else:
                return '\x00' * (8 - len(data) % 8)
        cipher = blowfish.new(self.key, blowfish.MODE_OFB, self.iv)
        ciphertext = cipher.encrypt(plaintext + bf_padding(plaintext))
        return ciphertext

    def encode(self, str):
        plaintext = self.compress(str)
        ciphertext = self.encrypt(plaintext)
        # Write header
        self.write(struct.pack('i', len(ciphertext)) + self.iv)
        # Scramble iterator and write payload
        self.randomize(self.iv)
        self.write(ciphertext)

class Reader(Steganographer):

    def __init__(self, im, passphrase):
        self.key = hashlib.sha256(passphrase).digest()[:7]
        w, h = im.size
        linear = ((x,y,c) for x in range(w) for y in range(h) for c in range(3))
        super(Reader, self).__init__(im, linear)

    def decompress(self, str):
        """Returns the (GZip compressed) string in decompressed form"""
        buf = StringIO.StringIO(str)
        # Read compressed data into gzip object, decompress
        gz = gzip.GzipFile(mode = 'r', fileobj = buf)
        # Get string
        output = gz.read()
        # Cleanup
        gz.close()
        buf.close()
        return output

    def decrypt(self, ciphertext):
        """Decrypts ciphertext, returning plaintext"""
        cipher = blowfish.new(self.key, blowfish.MODE_OFB, self.iv)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext

    def decode(self):
        length = self.read(4)
        length = struct.unpack('i', length)[0]
        self.iv = self.read(8)
        self.randomize(self.iv)
        ciphertext = self.read(length)
        return self.decompress(self.decrypt(ciphertext))
