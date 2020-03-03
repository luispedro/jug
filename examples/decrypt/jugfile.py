from itertools import product, chain

import numpy as np

from jug import TaskGenerator
from crypt import decode, letters, isgood, preprocess


with open('secret.msg', 'rb') as f:
    ciphertext = f.read()
ciphertext = preprocess(ciphertext)


@TaskGenerator
def decrypt(prefix):
    res = []
    for suffix in product(letters, repeat=5 - len(prefix)):
        passwd = np.concatenate([prefix, suffix])
        text = decode(ciphertext, passwd)
        if isgood(text):
            passwd = "".join(map(chr, passwd))
            res.append((passwd, text))
    return res


@TaskGenerator
def join(partials):
    return list(chain(*partials))


results = []
for p in letters:
    results.append(decrypt([p]))

fullresults = join(results)
