# stegan.py - TODO: more channels
import sys, os, struct
import Image, subprocess

# Check usage and flags
if len(sys.argv) != 4:
        print "Usage: stegan <mode> <reference image> <input file>"
        print "Usage: available modes: encode, decode"
        sys.exit()
mode = sys.argv[1]

# Prepare reference image
refim = Image.open(sys.argv[2]).convert("RGB")
refpix = refim.load()
refw, refh = refim.size

if mode == "encode":
        # Sanity check
        if (refw * refh) < (os.path.getsize(sys.argv[3]) * 8):
                print "Error: input file too large for reference image"
                sys.exit()

        # Compress to .gz file (input => input.gz)
        print "Compressing data...",
        gzargs = ("gzip -f %s" % sys.argv[3]).split()
        gzname = "%s.gz" % sys.argv[3]
        p = subprocess.Popen(gzargs)
        p.wait()
        print "Done. (Compressed size: %d bytes)" % os.path.getsize(gzname)

        # Encrypt compressed data and add .enc suffix (input.gz => input.gz.enc)
        print "Encrypting data..."
        encargs = ("filelock %s" % gzname).split()
        encname = "%s.enc" % gzname
        encf = open(encname, "w")
        p = subprocess.Popen(encargs, stdout = encf) 
        p.wait()
        encf.close()
        print "Done. (Encrypted size: %d bytes)" % os.path.getsize(encname)

        # Assume little endian byte order when packing size
        packedsize = struct.pack('i', os.path.getsize(encname))

        # Encode encrypted data into image pixels (input.gz.enc => input.gz.enc.png)
        print "Encoding data...",
        f = open(encname, "r")
        (x, y) = (0, 0)
        for i in range(os.path.getsize(encname)+4):
                # Encode length in little-endian order
                byte = packedsize[i] if i < 4 else f.read(1)
                # Convert from base 16 to binary
                byte = (bin(ord(byte))[2:]).zfill(8)
                for bit in byte:
                        pixel = list(refpix[x, y])
                        if pixel[0] == 0:
                                pixel[0] += int(bit)
                        else:
                                pixel[0] -= int(bit)
                        refpix[x, y] = tuple(pixel)
                        (x, y) = (x+1, y) if x+1 < refw else (0, y+1)
        f.close()
        print "Done."

        # Clean up .gz and .enc files
        print "Cleaning up...",
        os.remove(gzname)
        os.remove(encname)
        print "Done"

        # Save output with .png extension
        print "Saving to %s.png." % encname
        refim.save("%s.png" % encname, "PNG")

elif mode == "decode":
        # Open input image
        inim = Image.open(sys.argv[3]).convert("RGB")
        inpix = inim.load()
        inw, inh = inim.size

        # Decode image (input.gz.enc.png => input.gz.enc)
        print "Decoding..."
        f = open("%s" % sys.argv[3][:-4], "w")
        (x, y) = (0, 0)
        i, size, length = 0, 4, 0
        # Update size dynamically 
        while i < size:
                # Decode byte and convert to an integer
                byte = 0
                for j in range(8):
                        if inpix[x, y][0] != refpix[x, y][0]: byte |= (1<<(7-j))
                        (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                # Decode length before data (little endian)
                if i < 4:
                        length |= (byte << (i*8))
                        if i == 3: 
                                size += length
                                print "Length: %d bytes" % length
                else:
                        f.write(chr(byte))
                i += 1

        # Close and flush write buffer
        f.close()
        print "Done. (%d bytes written)" % os.path.getsize("%s" % sys.argv[3][:-4])

        # Decrypted decoded file (input.gz.enc => input.gz)
        print "Decrypting data..."
        decrargs = ("filelock -d %s" % sys.argv[3][:-4]).split()
        decrf = open("%s" % sys.argv[3][:-8], "w")
        p = subprocess.Popen(decrargs, stdout = decrf) 
        p.wait()
        decrf.close()
        print "Done. (%d bytes decrypted)" % os.path.getsize("%s" % sys.argv[3][:-8])

        # Decompress (input.gz => input)
        print "Decompressing data...",
        gzargs = ("gzip -d %s" % sys.argv[3][:-8]).split()
        p = subprocess.Popen(gzargs)
        p.wait()
        print "Done. (%d bytes decompressed)" % os.path.getsize("%s" % sys.argv[3][:-11])

        # Clean up
        os.remove(sys.argv[3])
        os.remove(sys.argv[3][:-4])

else:
        print "Error: unknown mode"
        print "Usage: available modes: encode, decode"
