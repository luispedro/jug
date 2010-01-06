import numpy as np

def decode(text, passwd):
    cipher = np.tile(passwd, len(text)/len(passwd))
    text = text ^ cipher
    return "".join(map(chr, text))
encode = decode

def isgood(text):
    return text.find('Luis Pedro Coelho') >= 0

letters = map(ord, 'abcdefghijklmnopqrstuvwxyz')


if __name__ == '__main__':
    import sys
    text = sys.argv[1]
    passwd = sys.argv[2]
    passwd = map(ord, passwd)
    text = np.array(map(ord,text), np.uint8)
    sys.stdout.write(encode(text, passwd))


