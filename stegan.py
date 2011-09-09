# stegan.py
# Author: Eugene Ma
import sys, os, struct, random, getpass, gzip, StringIO, hashlib
import Image
from Crypto.Cipher import Blowfish as bf

# Compress data with gzip and return output as string
def compress(data):
        buf = StringIO.StringIO()
        gz = gzip.GzipFile(mode = "w", fileobj = buf)
        gz.write(data)
        gz.close()
        output = buf.getvalue()
        buf.close()
        return output

# Decompress data with gzip and return output as string
def decompress(data):
        buf = StringIO.StringIO(data)
        gz = gzip.GzipFile(mode = "r", fileobj = buf)
        output = gz.read()
        gz.close()
        buf.close()
        return output

# Encrypt data with given key and initialization vector.
# The output string may be of different length since due to padding.
def encrypt(key, iv, data):
        padding = "\x00" * (8 - len(data) % 8) if len(data) != 8 else ""
        key = hashlib.sha256(key).digest()[:7]
        return bf.new(key, bf.MODE_CBC, iv).encrypt(data + padding)

# Decrypt data with given key and initialization vector
def decrypt(key, iv, data):
        key = hashlib.sha256(key).digest()[:7]
        return bf.new(key, bf.MODE_CBC, iv).decrypt(data)

# Tells us where the next bit is expected
# Arguments: x and y coordinates, current channel, image 
# Returns a tuple of (x, y, channel)
def nextbit(x, y, ch, im):
        if ch < 2:
                return (x, y, ch + 1)
        else:
                return (x + 1, y, 0) if x + 1 < im.size[0] else (0, y + 1, 0)

# Encode data into reference image where each input bit is embedded in the LSB
# of RGB channels of a pixel. Encoding format: length (32-bit), data.
def encode(ref, data):
        length = struct.pack('i', len(data))
        x, y, ch = 0, 0, 0
        pix = ref.load()
        for i in range(len(data) + 4):
                b = ord(length[i] if i < 4 else data[i-4])
                for j in range(8):
                        p = list(pix[x, y])
                        p[ch] = (p[ch] &~ 1) | ((b & (1<<(7 - j))) >> (7 - j))
                        pix[x, y] = tuple(p)
                        (x, y, ch) = nextbit(x, y, ch, ref)

# Decode data from image. Assume the image contains at least 4 bytes of data
# corresponding to the length, then set real length after length is decoded.
def decode(im):
        data = ""
        size, length = 4, 0
        x, y, ch, i = 0, 0, 0, 0
        pix = im.load()
        while i < size:
                byte = 0
                # Decode byte mapped to next 8 bits
                for j in range(8):
                        byte |= ((pix[x, y][ch] & 1) << (7 - j))
                        (x, y, ch) = nextbit(x, y, ch, im)
                # First 4 bytes are length bytes, otherwise data byte
                if i < 4: 
                        length |= (byte << (i * 8))
                        if i == 3: size += length
                else:
                        data += chr(byte)
                i += 1
        return data

##############################################################################
# Check usage and flags
if len(sys.argv) != 5:
        print "Usage: %s <mode> <ref> <input> <output>" % sys.argv[0]
        print "Usage: available modes: encode, decode"
        sys.exit()

mode = sys.argv[1]
if mode == "encode":
        # Read and compress file contents
        f = open(sys.argv[3])
        data = compress(f.read())
        f.close()

        # Need enough pixels to encode each bit
        ref = Image.open(sys.argv[2]).convert("RGB")
        w, h = ref.size
        if (w * h * 3) < (len(data) * 8):
                print "Error: input file too large for given reference image"
                sys.exit()

        pw = getpass.getpass()
        iv = struct.pack("Q", random.getrandbits(64))
        length = struct.pack("i", len(data))

        # Encoding format: original file length (4 bytes), IV, encrypted data
        encode(ref, length + iv + encrypt(pw, iv, data))

        ref.save("%s" % sys.argv[4], "PNG")
elif mode == "decode":
        im = Image.open(sys.argv[3]).convert("RGB")
        pw = getpass.getpass()

        data = decode(im)
        length = struct.unpack("i", data[:4])[0]
        iv, data = data[4:12], data[12:]

        f = open(sys.argv[4], "w")
        f.write(decompress(decrypt(pw, iv, data)[:length]))
        f.close()
else:
        print "Error: unknown mode - available modes are encode, decode"
