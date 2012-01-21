Author: Eugene Ma (edma2)

------------------------------------------------
Dependencies: 
------------------------------------------------
* PyCrypto (https://www.dlitz.net/software/pycrypto/)
* PIL (http://www.pythonware.com/products/pil/)

------------------------------------------------
Description:
------------------------------------------------
stegan is a steganographic tool for Python, encoding arbitrary streams
of bytes into PNG image files.

------------------------------------------------
Usage:
------------------------------------------------
```python
>>> import Image, stegan
>>> im = Image.open('tux.png').convert('RGB')
>>> writer = stegan.Writer(im, 'password')
>>> writer.encode('hello, world!')
>>> im.save('encoded.png')
>>> im = Image.open('encoded.png').convert('RGB')
>>> reader = stegan.Reader(im, 'password')
>>> print reader.decode()
hello, world!
```
