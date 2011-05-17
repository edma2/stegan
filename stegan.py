# stegan.py - TODO: more channels
import sys, os
import Image
import subprocess, tempfile

# Check usage and flags
if len(sys.argv) != 5:
        print "usage: stegan <mode> <reference image> <input file> <output file>"
        print "usage: available modes: encode, decode"
        sys.exit()
mode = sys.argv[1]

# Prepare reference image
refim = Image.open(sys.argv[2]).convert("RGB")
refpix = refim.load()
refw, refh = refim.size

if mode == "encode":
        # Open file and get its length in binary
        f = open(sys.argv[3])
        flen = os.path.getsize(sys.argv[3])

        # Do sanity check
        if (refw * refh) < (flen * 8):
                print >> sys.stderr, "error: input file too large for reference image"
                sys.exit()

        print >> sys.stderr, "Mode: Encode"
        print >> sys.stderr, "Reference Image size: %d x %d pixels" % (refw, refh)
        print >> sys.stderr, "Input file size: %d bytes" % flen

        # Keep verbose records
        bitsencoded = 0
        bytesread = 0

        # Encrypt
        encrypt_args = ("filelock %s" % sys.argv[3]).split()
        encrypt_tmp_file = tempfile.NamedTemporaryFile()
        print >> sys.stderr, "Encrypting file..."
        p = subprocess.Popen(encrypt_args, stdout = encrypt_tmp_file) 
        p.wait()
        print >> sys.stderr, "Done."

        # Compress
        print >> sys.stderr, "Compressing file...",
        compress_args = ("gzip -c %s" % encrypt_tmp_file.name).split()
        p = subprocess.Popen(compress_args, stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
        # Obtain output data
        data = p.communicate()[0]
        print >> sys.stderr, "Done. (Compressed size: %d bytes)" % len(data)

        # Close and delete temporary file
        encrypt_tmp_file.close()

        print >> sys.stderr, "Encoding length...",
        datalen = bin(len(data))[2:].zfill(32)
        #datalen = (bin(os.path.getsize(sys.argv[3]))[2:]).zfill(32)

        # Encode length of data into image
        (x, y) = (0, 0)
        for bit in datalen:
                # Convert to mutable data structure
                pixel = list(refpix[x, y])
                if pixel[0] == 0:
                        pixel[0] += int(bit)
                else:
                        pixel[0] -= int(bit)
                refpix[x, y] = tuple(pixel)
                # Increment coordinates
                (x, y) = (x+1, y) if x+1 < refw else (0, y+1)
                bitsencoded += 1
        print >> sys.stderr, "Done."

        print >> sys.stderr, "Encoding file...",
        for byte in data:
                # Convert hex digit to 8 binary digits
                byte = (bin(ord(byte))[2:]).zfill(8)
                for bit in byte:
                        pixel = list(refpix[x, y])
                        if pixel[0] == 0:
                                pixel[0] += int(bit)
                        else:
                                pixel[0] -= int(bit)
                        # Store back to tuple
                        refpix[x, y] = tuple(pixel)
                        # Increment coordinates
                        (x, y) = (x+1, y) if x+1 < refw else (0, y+1)
                        bitsencoded += 1
                bytesread += 1
        print >> sys.stderr, "Done."
        print >> sys.stderr, "%d bytes read." % bytesread
        print >> sys.stderr, "%d bits encoded." % bitsencoded

        # All done
        refim.save(sys.argv[4], "PNG")

elif mode == "decode":
        # Open input image
        inim = Image.open(sys.argv[3]).convert("RGB")
        inpix = inim.load()
        inw, inh = inim.size

        # Open temorary output file that will be decrypted
        tmpf = tempfile.NamedTemporaryFile()

        # Create output file
        print >> sys.stderr, "Mode: Decode"
        print >> sys.stderr, "Reference image size: %d x %d pixels" % (inw, inh)
        print >> sys.stderr, "Input image size: %d x %d pixels" % (refw, refh)

        bitsdecoded = 0
        byteswritten = 0

        print >> sys.stderr, "Decoding length",
        # Extract file length
        inlen = []
        (x, y) = (0, 0)
        for i in range(32):
                if inpix[x, y][0] != refpix[x, y][0]:
                        inlen.append('1')
                else:
                        inlen.append('0')
                (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                bitsdecoded += 1
        # Convert input length to decimal
        inlen = int("".join(inlen), 2)

        print >> sys.stderr, "Done. (%d bytes)" % inlen

        print >> sys.stderr, "Decoding input image...",
        for i in range(inlen):
                # Retreive a byte at a time
                byte = []
                for j in range(8):
                        if inpix[x, y][0] != refpix[x, y][0]:
                                byte.append('1')
                        else:
                                byte.append('0')
                        # Advance pixel by pixel
                        (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                        bitsdecoded += 1
                # Convert bit pattern to int
                byte = int("".join(byte), 2)
                print byte
                tmpf.write(chr(byte))
                byteswritten += 1

        print >> sys.stderr, "Done."
        print >> sys.stderr, "%d bits decoded." % bitsdecoded
        print >> sys.stderr, "%d bytes written." % byteswritten

        # Decompress
        print >> sys.stderr, "Decompressing data...",
        compress_args = ("gzip -c -d %s" % tmpf.name).split()
        compress_tmp_file = tempfile.NamedTemporaryFile()
        p = subprocess.Popen(compress_args, stdout = compress_tmp_file, stderr = subprocess.PIPE) 
        p.wait()
        size = os.path.getsize(compress_tmp_file.name)
        print >> sys.stderr, "Done. (Decompressed size: %d bytes)" % size

        # Decrypt
        outfile = open(sys.argv[4], "w")
        decrypt_args = ("filelock -d %s" % compress_tmp_file.name).split()
        print >> sys.stderr, "Decrypting data...",
        p = subprocess.Popen(decrypt_args, stdout = outfile) 
        p.wait()
        size = os.path.getsize(sys.argv[4])
        print >> sys.stderr, "Done. (Decrypted size: %d bytes)" % size

        # Close and delete temporary file
        tmpf.close()
        compress_tmp_file.close()
        outfile.close()
else:
        print >> sys.stderr, "error: unknown mode"
        print >> "usage: available modes: encode, decode"
