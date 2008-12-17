from task import Task, TaskGenerator

@TaskGenerator
def compfeats(url):
    print 'Feats called: ', url
    return url+'feats'

@TaskGenerator
def nfold(param, feats):
    print 'nfold called: ', param, feats
    return param, feats

imgs = ['images/img1.png','images/img2.png']
feats = [compfeats(img) for img in imgs]
tenfold = [nfold(param=p,feats=feats) for p in range(10)]

