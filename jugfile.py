def compfeats(url):
    print 'Feats called: ', url
    return url+'feats'

def nfold(param, feats):
    print 'nfold called: ', param, feats
    return param, feats

imgs = ['images/img1.png','images/img2.png']
feats = [Compute('featurecomputation',compfeats,url=img) for img in imgs]
tenfold = Compute('10 fold',nfold,param=ParamSearch([0,1,2,3,4,5]),feats=feats)

