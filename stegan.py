# stegan.py
# Written by Eugene Ma
import sys, os, struct, random, subprocess
import Image

# Check usage and flags
if len(sys.argv) != 5:
        print >> sys.stderr, "Usage: %s <mode> <reference image> <input file> <output file>" % sys.argv[0]
        print >> sys.stderr, "Usage: available modes: encode, decode"
        sys.exit()
mode = sys.argv[1]

# Prepare reference image
refim = Image.open(sys.argv[2]).convert("RGB")
refpix = refim.load()
refw, refh = refim.size

if mode == "encode":
        if (refw * refh) < (os.path.getsize(sys.argv[3]) * 8):
                print >> sys.stderr, "Error: input file too large for reference image"
                sys.exit()

        # Invoke gzip
        print >> sys.stderr, "Encoding..."
        gzargs = ("gzip -cf %s" % sys.argv[3]).split()
        gz = subprocess.Popen(gzargs, stdout = subprocess.PIPE)
        gz.wait()

        # Read from gzip and point stdout to pipe
        flargs = ("filelock -e - -").split()
        fl = subprocess.Popen(flargs, stdin = gz.stdout, stdout = subprocess.PIPE) 
        data = fl.communicate()[0]

        # Assume little endian byte order when packing size
        packedsize = struct.pack('i', len(data))

        # Encode encrypted data into image pixels (input.gz.enc => output)
        (x, y) = (0, 0)
        random.seed()
        for i in range(len(data)+4):
                # Encode length in little-endian order
                byte = packedsize[i] if i < 4 else data[i-4]
                # Convert from base 16 to binary
                byte = (bin(ord(byte))[2:]).zfill(8)
                for bit in byte:
                        # Randomly pick a channel to alter
                        pixel = list(refpix[x, y])
                        channel = random.randint(0, 2)
                        if pixel[channel] == 0:
                                pixel[channel] += int(bit)
                        else:
                                pixel[channel] -= int(bit)
                        refpix[x, y] = tuple(pixel)
                        (x, y) = (x+1, y) if x+1 < refw else (0, y+1)

        # Save output
        print >> sys.stderr, "Done. Saving to %s." % sys.argv[4]
        refim.save("%s" % sys.argv[4], "PNG")

elif mode == "decode":
        inim = Image.open(sys.argv[3]).convert("RGB")
        inpix = inim.load()
        inw, inh = inim.size

        print >> sys.stderr, "Decoding..."
        flargs = ("filelock -d - %s.gz" % sys.argv[4]).split()
        fl = subprocess.Popen(flargs, stdin = subprocess.PIPE)

        (x, y) = (0, 0)
        i, size, length = 0, 4, 0
        while i < size:
                # Reconstruct a full byte
                byte = 0
                for j in range(8):
                        if inpix[x, y] != refpix[x, y]: byte |= (1<<(7-j))
                        (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                # Decode length before data (little endian)
                if i < 4:
                        length |= (byte << (i*8))
                        if i == 3: 
                                size += length
                else:
                        fl.stdin.write(chr(byte))
                i += 1
        fl.stdin.close()
        fl.wait()

        # Decompress and deliver
        gzargs = ("gzip -d %s.gz" % sys.argv[4]).split()
        gz = subprocess.Popen(gzargs)
        gz.wait()
        print >> sys.stderr, "Done. Saving to %s." % sys.argv[4]
else:
        print >> sys.stderr, "Error: unknown mode"
        print >> sys.stderr, "Usage: available modes are encode, decode"
