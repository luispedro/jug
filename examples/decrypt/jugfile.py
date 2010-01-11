from jug import TaskGenerator
from itertools import product, chain
from crypt import decode, letters, isgood, preprocess

ciphertext = file('secret.msg').read()
ciphertext = preprocess(ciphertext)

@TaskGenerator
def decrypt(prefix, suffix_size):
    res = []
    for p in product(letters, repeat=suffix_size):
        text = decode(ciphertext, np.concatenate([prefix, p]))
        if isgood(text):
            passwd = "".join(map(chr,np.concatenate([prefix, p])))
            res.append((passwd, text))
    return res

@TaskGenerator
def join(partials):
    return list(chain(*partials))

fullresults = join([decrypt([let], 4) for let in letters])

