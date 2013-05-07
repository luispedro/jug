import urllib.request, urllib.error, urllib.parse
from jug import Task
from collections import defaultdict
from time import sleep
import re
from string import lower
from os.path import exists
import json
from os import mkdir

def getdata(title):
    sleep(8)
    # The reason for this cache is to avoid hitting Wikipedia too much in
    # case we are playing around with testing.
    # In a real example, we would *not* have a cache, of course.
    cache = 'text-data/' + title
    if exists(cache):
        return str(file(cache).read(), 'utf-8')

    title = urllib.parse.quote(title)
    url = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=' + title
    text = urllib.request.urlopen(url).read()
    data = json.loads(text)
    data = list(data['query']['pages'].values())[0]
    text = data['revisions'][0]['*']
    text = re.sub(r'(?x) \[ [^]] *? \]\]', '', text)
    text = re.sub('(?x) {{ [^}]*? }}', '', text)
    text = text.strip()

    try:
        mkdir('text-data')
    except:
        pass
    cache = file(cache, 'w')
    cache.write(text.encode('utf-8'))
    cache.close()
    return text

def isstopword(titlewords, w):
    if not re.match('^\w+$', w): return True
    if w in titlewords: return True
    return False

def countwords(title, document):
    '''
    Takes a file name and returns a wordcount.
    '''
    sleep(4)
    titlewords = list(map(lower, title.split()))
    counts = defaultdict(int)
    for w in document.split():
        w = lower(w)
        if not isstopword(titlewords, w):
            counts[w] += 1
    return dict(counts)

def addcounts(counts):
    '''
    Takes intermediate word counts and puts them together
    '''
    sleep(24)
    allcounts = defaultdict(int)
    for c in counts:
        for k,v in c.items():
            allcounts[k] += v
    return dict(allcounts)

def divergence(global_counts, nr_documents, counts):
    '''
    Takes the global word counts as well as a single count vector
    and returns a set of words *in this document* that are document
    specific.
    '''
    sleep(8)
    specific = []
    for w,n in counts.items():
        if n > global_counts[w]//100:
            specific.append(w)
    specific.sort(key=counts.get)
    specific.reverse()
    return specific

counts = []
for mp in file('MPs.txt'):
    mp = mp.strip()
    document = Task(getdata, mp)
    counts.append(Task(countwords, mp, document))
avgs = Task(addcounts, counts)
results = []
for c in counts:
    results.append(Task(divergence,avgs, len(counts), c))
