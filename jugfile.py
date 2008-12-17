from task import Task
def compfeats(url):
    print 'Feats called: ', url
    return url+'feats'

def nfold(param, feats):
    print 'nfold called: ', param, feats
    return param, feats

imgs = ['images/img1.png','images/img2.png']
feats = [Task(compfeats,url=img) for img in imgs]
tenfold = [Task(nfold,param=p,feats=feats) for p in range(10)]

