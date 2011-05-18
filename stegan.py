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
        f = open(sys.argv[3])
        flen = os.path.getsize(sys.argv[3])
        compress_tmp_file = tempfile.NamedTemporaryFile()

        # Sanity check
        if (refw * refh) < (flen * 8):
                print >> sys.stderr, "error: input file too large for reference image"
                sys.exit()

        # Compress
        print >> sys.stderr, "Compressing data...",
        compress_args = ("gzip -c %s" % sys.argv[3]).split()
        p = subprocess.Popen(compress_args, stdout = compress_tmp_file, stderr = subprocess.PIPE) 
        p.wait()
        size = os.path.getsize(compress_tmp_file.name)
        print >> sys.stderr, "Done. (Compressed size: %d bytes)" % size

        # Encrypt
        encrypt_args = ("filelock %s" % compress_tmp_file.name).split()
        print >> sys.stderr, "Encrypting data..."
        p = subprocess.Popen(encrypt_args, stdout = subprocess.PIPE) 
        data = p.communicate()[0]
        size = len(data)
        print >> sys.stderr, "Done. (Encrypted size: %d bytes)" % size

        # Encode length of data into image
        binsize = bin(size)[2:].zfill(32)
        bitsencoded = 0
        print >> sys.stderr, "Encoding length...",
        (x, y) = (0, 0)
        for bit in binsize:
                pixel = list(refpix[x, y])
                if pixel[0] == 0:
                        pixel[0] += int(bit)
                else:
                        pixel[0] -= int(bit)
                refpix[x, y] = tuple(pixel)
                (x, y) = (x+1, y) if x+1 < refw else (0, y+1)
                bitsencoded += 1
        print >> sys.stderr, "Done. (Length: %d bytes)" % size

        # Encode file
        print >> sys.stderr, "Encoding file...",
        bytesread = 0
        for byte in data:
                byte = (bin(ord(byte))[2:]).zfill(8)
                for bit in byte:
                        pixel = list(refpix[x, y])
                        if pixel[0] == 0:
                                pixel[0] += int(bit)
                        else:
                                pixel[0] -= int(bit)
                        refpix[x, y] = tuple(pixel)
                        (x, y) = (x+1, y) if x+1 < refw else (0, y+1)
                        bitsencoded += 1
                bytesread += 1
        compress_tmp_file.close()
        refim.save(sys.argv[4], "PNG")
        print >> sys.stderr, "Done. (%d bytes read, %d bits encoded)" % (bytesread, bitsencoded)
elif mode == "decode":
        # Open input image
        inim = Image.open(sys.argv[3]).convert("RGB")
        inpix = inim.load()
        inw, inh = inim.size

        bitsdecoded = 0
        byteswritten = 0

        decode_tmp_file = tempfile.NamedTemporaryFile()
        decrypt_tmp_file = tempfile.NamedTemporaryFile()
        decompress_output_file = open(sys.argv[4], "w")

        # Decode length
        print >> sys.stderr, "Decoding length...",
        size = []
        (x, y) = (0, 0)
        for i in range(32):
                if inpix[x, y][0] != refpix[x, y][0]:
                        size.append('1')
                else:
                        size.append('0')
                (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                bitsdecoded += 1
        size = int("".join(size), 2)
        print >> sys.stderr, "Done. (Length: %d bytes)" % size

        # Decode image
        print >> sys.stderr, "Decoding input image...",
        for i in range(size):
                byte = []
                for j in range(8):
                        if inpix[x, y][0] != refpix[x, y][0]:
                                byte.append('1')
                        else:
                                byte.append('0')
                        (x, y) = (x+1, y) if x+1 < inw else (0, y+1)
                        bitsdecoded += 1
                byte = int("".join(byte), 2)
                decode_tmp_file.write(chr(byte))
                byteswritten += 1
        print >> sys.stderr, "Done. (%d bits decoded, %d bytes written)" % (bitsdecoded, byteswritten)

        # Decrypt
        print >> sys.stderr, "Decrypting file..."
        decrypt_args = ("filelock -d %s" % decode_tmp_file.name).split()
        p = subprocess.Popen(decrypt_args, stdout = decrypt_tmp_file) 
        p.wait()
        size = os.path.getsize(decrypt_tmp_file.name)
        print >> sys.stderr, "Done. (%d bytes decrypted)" % size

        print >> sys.stderr, "Decompressing file...",
        decompress_args = ("gzip -c -d %s" % decrypt_tmp_file.name).split()
        p = subprocess.Popen(decompress_args, stdout = decompress_output_file)
        p.wait()
        print >> sys.stderr, "Done. (%d bytes decompressed)" % os.path.getsize(sys.argv[4])

        # Close and delete temporary files
        decode_tmp_file.close()
        decrypt_tmp_file.close()
        decompress_output_file.close()
else:
        print >> sys.stderr, "error: unknown mode"
        print >> "usage: available modes: encode, decode"
