import itertools

from crypt import decode, letters, isgood, preprocess


with open('secret.msg') as f:
    ciphertext = f.read()
ciphertext = preprocess(ciphertext)

for p in itertools.product(letters, repeat=5):
    text = decode(ciphertext, p)
    if isgood(text):
        passwd = "".join(map(chr, p))
        print('%s:%s' % (passwd, text))
