from jug.task import Task, TaskGenerator
from time import sleep

@TaskGenerator
def compfeats(url):
    print('Feats called: {}'.format(url))
    sleep(2)
    return url+'feats'

@TaskGenerator
def nfold(param, feats):
    print('nfold called: {} {}'.format(param, feats))
    sleep(3)
    return param, feats

imgs = ['images/img1.png','images/img2.png']
feats = [compfeats(img) for img in imgs]
tenfold = [nfold(param=p,feats=feats) for p in range(10)]

