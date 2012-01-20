import sys, Image, getpass
sys.path.append('src')
import stegan

im = Image.open('test/tux.png').convert('RGB')
writer = stegan.Writer(im, 'password')
writer.encode('hello, world')
im.save("test/test.png")

im = Image.open('test/test.png').convert('RGB')
reader = stegan.Reader(im, 'password')
print reader.decode()
