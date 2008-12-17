def compfeats(url):
    print 'Feats called: ', url
    return url

def nfold(imgs, feats):
    print 'nfold called: ', imgs, feats

imgs = ['images/img1.png','images/img2.png']
feats = [Compute('featurecomputation',compfeats,url=img) for img in imgs]
tenfold = Compute('10 fold',nfold,imgs=imgs,feats=feats)

