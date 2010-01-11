import numpy as np
from itertools import product
from crypt import decode, letters, isgood

ciphertext = file('secret.msg').read()
ciphertext = np.array(map(ord,ciphertext), np.uint8)

for p in product(letters, repeat=5):
    text = decode(ciphertext, p)
    if isgood(text):
        passwd = "".join(map(chr,p))
        print '%s:%s' % (passwd, text)

