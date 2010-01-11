from jug import TaskGenerator
import numpy as np
from itertools import product, chain
from crypt import decode, letters, isgood

ciphertext = file('secret.msg').read()
ciphertext = np.array(map(ord,ciphertext), np.uint8)

@TaskGenerator
def decrypt(prefix, suffix_size):
    res = []
    for p in product(letters, repeat=suffix_size):
        text = decode(ciphertext, np.concatenate([prefix, p]))
        if isgood(text):
            passwd = "".join(map(chr,p))
            res.append((passwd, text))
    return res

@TaskGenerator
def join(partials):
    return list(chain(*partials))

fullresults = join([decrypt([let], 4) for let in letters])

