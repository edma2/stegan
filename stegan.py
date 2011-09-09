# stegan.py
# Author: Eugene Ma
import sys, os, argparse, struct, random, getpass, gzip, StringIO, hashlib 
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

# Tells us where the next bit should be encoded. Arguments are x and y
# coordinates, current channel, and Image object. Returns a tuple of (x, y,
# channel)
def nextbit(x, y, ch, im):
        if ch < 2:
                return (x, y, ch + 1)
        else:
                return (x + 1, y, 0) if x + 1 < im.size[0] else (0, y + 1, 0)

# Encode data into reference image where each input bit is embedded in the LSB
# of RGB channels of a pixel. Encoding format: length (32-bit), data.
def encode(im, data):
        length = struct.pack('i', len(data))
        x, y, ch = 0, 0, 0
        pix = im.load()
        for i in range(len(data) + 4):
                b = ord(length[i] if i < 4 else data[i-4])
                for j in range(8):
                        p = list(pix[x, y])
                        p[ch] = (p[ch] &~ 1) | ((b & (1<<(7 - j))) >> (7 - j))
                        pix[x, y] = tuple(p)
                        (x, y, ch) = nextbit(x, y, ch, im)

# Decode data from image. Assume the image contains at least 4 bytes of data
# corresponding to the length, then set real length after length is decoded.
def decode(im):
        data = ""
        size, length = 4, 0
        x, y, ch, i = 0, 0, 0, 0
        pix = im.load()
        while i < size:
                byte = 0
                # Decode byte mapped to next 8 channels
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
# Parse command line arguments
opts = argparse.ArgumentParser(usage = "%(prog)s {enc, dec} <image file> [options]")
opts.add_argument("mode", choices = ["enc", "dec"], help = "encode image with\
                data or decode image")
opts.add_argument("image", help = "carrier image")
opts.add_argument("-i", metavar = "data", help = "The data to be encoded will\
                be read from this file. This option is ignored when decoding\
                images. Defaults to standard input.")
opts.add_argument("-o", metavar = "output", help = "The encoded image or\
                decoded data will be written to this file. Defaults to standard\
                output.")
options = opts.parse_args(sys.argv[1:])

im = Image.open(options.image).convert("RGB")
if options.mode == "enc":
        # Read and compress data
        fin = open(options.i) if options.i else sys.stdin
        data = compress(fin.read())
        if options.i: fin.close() 

        # Need enough pixels to encode each bit
        maxbits = im.size[0] * im.size[1] * 3
        if maxbits < (len(data) * 8):
                print "error: input file too large for given reference image"
                print "maximum input size: %d" % maxbits
                sys.exit()

        # Encoding format: original file length (4 bytes), IV, encrypted data
        length = struct.pack("i", len(data))
        iv = struct.pack("Q", random.getrandbits(64))

        encode(im, length + iv + encrypt(getpass.getpass(), iv, data))
        im.save(options.o if options.o else sys.stdout, "PNG")
elif options.mode == "dec":
        # Decode data from image
        data = decode(im)

        # Decrypt and decompress data
        length = struct.unpack("i", data[:4])[0]
        iv, data = data[4:12], data[12:]

        fout = open(options.o, "w") if options.o else sys.stdout
        fout.write(decompress(decrypt(getpass.getpass(), iv, data)[:length]))
        if options.o: fout.close()
