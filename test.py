import sys, Image, getpass
sys.path.append('src')
import stegan

image = Image.open('test/tux.png').convert('RGB')
stegan.encode(image, 'password', 'hello, world!')
image.save("test/test.png")
image = Image.open('test/test.png').convert('RGB')
print stegan.decode(image, 'password')
