import gzip, StringIO, hashlib, random, struct
import Crypto.Cipher.Blowfish as blowfish
import stegan

"""Returns byte string decompressed with GZip."""
def decompress(str):
    buf = StringIO.StringIO(str)
    gz = gzip.GzipFile(mode = 'r', fileobj = buf)
    output = gz.read()
    gz.close()
    buf.close()
    return output

"""Decrypts byte string with given key and initialization vector. Outputs
plaintext byte string."""
def decrypt(key, iv, ciphertext):
    cipher = blowfish.new(key, blowfish.MODE_OFB, iv)
    return cipher.decrypt(ciphertext)

"""Returns byte string decoded from image."""
def decode(im, password):
    w, h = im.size
    linear = ((x,y,c) for x in range(w) for y in range(h) for c in range(3))
    reader = stegan.Steganographer(im, linear)

    # Decode header
    header = reader.read(20)
    length = struct.unpack('i', header[:4])[0]
    iv = header[4:12]
    seed = header[12:]

    # Decode data
    reader.randomize(seed)
    data = reader.read(length)

    # Decrypt and decompress data
    key = hashlib.sha256(password).digest()[:7]
    return decompress(decrypt(key, iv, data))
