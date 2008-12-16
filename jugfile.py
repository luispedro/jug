def feats(url):
    print 'Feats called: ', url
    return url

def nfold(imgs, feats):
    print 'nfold called: ', imgs, feats

imgs = [Data(img) for img in ['images/img1.png','images/img2.png']]
feats = [Compute('featurecomputation',feats,img) for img in imgs]
tenfold = Compute('10 fold',nfold,imgs,feats)

