import stegan, Image, getpass

pw = getpass.getpass()

#image = Image.open('tux.png')
#inp = open('README')
#data = inp.read()
#stegan.encode(image, pw, data)
#image.save('out.png')

image = Image.open('out.png')
print stegan.decode(image, pw)
