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

# Encrypt data with given key and initialization vector
# Input data will be padded for you to ensure 8-byte alignment
def encrypt(key, iv, data):
        padding = "\x00" * (8 - len(data) % 8) if len(data) != 8 else ""
        key = hashlib.sha256(key).digest()[:7]
        data = bf.new(key, bf.MODE_CBC, iv).encrypt(data + padding)
        return data

# Decrypt data with given key and initialization vector
def decrypt(key, iv, data):
        key = hashlib.sha256(key).digest()[:7]
        return bf.new(key, bf.MODE_CBC, iv).decrypt(data)

# Encode data into reference image
def encode(ref, data):
        pix = ref.load()
        w, h = ref.size
        x, y = (0, 0)

        # Store number of bytes to encode in first 4 bytes 
        length = struct.pack('i', len(data))
        for i in range(len(data) + 4):
                byte = ord(length[i] if i < 4 else data[i-4])
                for j in range(8):
                        # Unpack pixel from tuple to list
                        p = list(pix[x, y])
                        ch = random.randint(0, 2)
                        # Subtle pixel alteration if bit is set 
                        if byte & (1 << (7 - j)): p[ch] -= 1 if p[ch] else -1
                        pix[x, y] = tuple(p)
                        (x, y) = (x + 1, y) if x + 1 < w else (0, y + 1)

# Decode data from image and reference image and return data string
def decode(ref, im):
        pix, rpix = im.load(), ref.load()
        w, h = im.size
        x, y = (0, 0)
        size, length, i = 4, 0, 0
        data = ""

        while i < size:
                # Reconstruct full byte
                byte = 0
                for j in range(8):
                        if pix[x, y] != rpix[x, y]: byte |= (1 << (7 - j))
                        (x, y) = (x + 1, y) if x + 1 < w else (0, y + 1)
                # Decode length before data (little-endian)
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
        random.seed()

        # Read and compress file contents
        f = open(sys.argv[3])
        data = compress(f.read())
        f.close()

        # Need enough pixels to encode each bit
        ref = Image.open(sys.argv[2]).convert("RGB")
        w, h = ref.size
        if (w * h) < (os.path.getsize(sys.argv[3]) * 8):
                print "Error: input file too large for given reference image"
                sys.exit()

        pw = getpass.getpass()
        iv = struct.pack("Q", random.getrandbits(64))
        length = struct.pack("i", len(data))

        # Encoding format: original file length (4 bytes), IV, encrypted data
        encode(ref, length + iv + encrypt(pw, iv, data))

        ref.save("%s" % sys.argv[4], "PNG")
elif mode == "decode":
        ref, im = [Image.open(sys.argv[i]).convert("RGB") for i in [2, 3]]
        f = open(sys.argv[4], "w")

        data = decode(ref, im)
        pw = getpass.getpass()
        length = struct.unpack("i", data[:4])[0]
        iv, data = data[4:12], data[12:]

        f.write(decompress(decrypt(pw, iv, data)[:length]))
        f.close()
else:
        print "Error: unknown mode - available modes are encode, decode"
