import sys, os
import Image
import subprocess, tempfile

# Check usage and flags
if len(sys.argv) != 5:
        print "usage: stegan <mode> <reference image> <input file> <output file>"
        print "usage: available modes: encode, decode"
        sys.exit()
mode = sys.argv[1]
infile = sys.argv[3]
outfile = sys.argv[4]

# Open reference image
im = Image.open(sys.argv[2]).convert("RGB")
w, h = im.size
pix = im.load()

######### Encryption and Compression ##########
if mode == "encode":
        # Open file and get its length in binary
        f = open(infile)
        flen = os.path.getsize(infile)

        # Do sanity check
        if (w * h) < (flen * 8):
                print >> sys.stderr, "error: input file too large for reference image"
                sys.exit()
        print >> sys.stderr, "Mode: Encode"
        print >> sys.stderr, "Image size: %d x %d pixels" % (w, h)
        print >> sys.stderr, "Input size: %d bytes" % flen
        bits = 0
        bytesread = 0
        # Write encrypted data to temporary file
        encrypt_args = ("./filelock %s" % infile).split()
        encrypt_tmp_file = tempfile.NamedTemporaryFile()
        print >> sys.stderr, "Encrypting file..."
        p = subprocess.Popen(encrypt_args, stdout = encrypt_tmp_file) 
        p.wait()

        # Compress temporary file and pipe from child process
        print >> sys.stderr, "Compressing file..."
        compress_args = ("tar cz %s" % encrypt_tmp_file.name).split()
        p = subprocess.Popen(compress_args, stdout = subprocess.PIPE, stderr = subprocess.PIPE) 
        data = p.communicate()[0]
        print >> sys.stderr, "Compressed size: %d bytes" % len(data)

        # Close and delete temporary file
        encrypt_tmp_file.close()

        print >> sys.stderr, "Encoding length..."
        #datalen = len(data).zfill(32)
        datalen = (bin(os.path.getsize(infile))[2:]).zfill(32)


        # Encode length of data into image
        (x, y) = (0, 0)
        for bit in datalen:
                # Convert to mutable data structure
                pixel = list(pix[x, y])
                if pixel[0] == 0:
                        pixel[0] += int(bit)
                else:
                        pixel[0] -= int(bit)
                # Store back to tuple
                pix[x, y] = tuple(pixel)
                # Increment coordinates
                (x, y) = (x+1, y) if x+1 < w else (0, y+1)
                bits += 1

        print >> sys.stderr, "Encoding file..."
        while True:
                byte = f.read(1)
                if byte == '': break
                # Convert hex to binary
                byte = bin(ord(byte))[2:].zfill(8)
                for bit in byte:
                        pixel = list(pix[x, y])
                        if pixel[0] == 0:
                                pixel[0] += int(bit)
                        else:
                                pixel[0] -= int(bit)
                        # Store back to tuple
                        pix[x, y] = tuple(pixel)
                        # Increment coordinates
                        (x, y) = (x+1, y) if x+1 < w else (0, y+1)
                        bits += 1
                bytesread += 1
        print >> sys.stderr, "%d bytes read." % bytesread
        print >> sys.stderr, "%d bits encoded." % bits
        im.save(outfile, "PNG")

######### Decoding ##########
elif mode == "decode":
        # Open input image
        input_im = Image.open(infile).convert("RGB")
        input_pix = input_im.load()
        bits = 0
        # Extract file length
        input_len = []
        (x, y) = (0, 0)
        for i in range(32):
                if input_pix[x, y][0] != ref_value[x, y][0]:
                        input_len.append('1')
                else:
                        input_len.append('0')
                (x, y) = (x+1, y) if x+1 < w else (0, y+1)
                bits += 1
        # Get input length in decimal
        input_len = int("".join(input_len), 2)





















        print >> sys.stderr, "error: decode not implemented yet"
