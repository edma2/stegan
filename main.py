import stegan, sys, Image, getpass

pw = getpass.getpass()

if sys.argv[1] == 'encode':
    image = Image.open(sys.argv[2])
    inp = open(sys.argv[3])
    data = inp.read()
    stegan.encode(image, pw, data)
    image.save(sys.argv[4])
elif sys.argv[1] == 'decode':
    image = Image.open(sys.argv[2])
    data = stegan.decode(image, pw)
    out = open(sys.argv[3], 'w')
    out.write(data)
