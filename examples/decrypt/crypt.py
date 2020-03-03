import numpy as np


def decode(text, passwd):
    cipher = np.tile(passwd, len(text) // len(passwd))
    text = text ^ cipher
    return "".join(map(chr, text))
encode = decode


def preprocess(ciphertext):
    return np.array(list(ciphertext), np.uint8)


def isgood(text):
    return text.find('Luis Pedro Coelho') >= 0


letters = list(map(ord, 'abcdefghijklmnopqrstuvwxyz'))


if __name__ == '__main__':
    import sys
    text = sys.argv[1]
    passwd = sys.argv[2]
    passwd = list(map(ord, passwd))
    text = np.array(list(map(ord, text)), np.uint8)
    sys.stdout.write(encode(text, passwd))
