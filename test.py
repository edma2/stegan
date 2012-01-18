import sys, Image, getpass
sys.path.append('src')
import encode, decode

image = Image.open('test/tux.png').convert('RGB')
encode.encode(image, 'password', 'hello, world!')
image.save("test/test.png")
image = Image.open('test/test.png').convert('RGB')
print decode.decode(image, 'password')
