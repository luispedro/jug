from collections import defaultdict
import json
from os import mkdir
from os.path import exists
import re
from time import sleep

import requests

from jug import Task


def get_data(title):
    sleep(8)
    # The reason for this cache is to avoid hitting Wikipedia too much in
    # case we are playing around with testing.
    # In a real example, we would *not* have a cache, of course.
    cache = 'text-data/' + title
    if exists(cache):
        with open(cache, 'rb') as f:
            return f.read().decode('utf-8')

    params = {'action': 'query',
              'prop': 'revisions',
              'rvprop': 'content',
              'format': 'json',
              'titles': title}
    r = requests.get('http://en.wikipedia.org/w/api.php', params=params)
    data = json.loads(r.text)
    data = list(data['query']['pages'].values())[0]
    text = data['revisions'][0]['*']
    text = re.sub(r'(?x) \[ [^]] *? \]\]', '', text)
    text = re.sub('(?x) {{ [^}]*? }}', '', text)
    text = text.strip()

    try:
        mkdir('text-data')
    except:
        pass
    with open(cache, 'wb') as f:
        f.write(text.encode('utf-8'))
    return text


def isstopword(titlewords, w):
    if not re.match(r'^\w+$', w):
        return True
    if w in titlewords:
        return True
    return False


def count_words(title, document):
    '''
    Takes a file name and returns a wordcount.
    '''
    sleep(4)
    titlewords = [w.lower() for w in title.split()]
    counts = defaultdict(int)
    for w in document.split():
        w = w.lower()
        if not isstopword(titlewords, w):
            counts[w] += 1
    return dict(counts)


def add_counts(counts):
    '''
    Takes intermediate word counts and puts them together
    '''
    sleep(24)
    allcounts = defaultdict(int)
    for c in counts:
        for k, v in c.items():
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
    for w, n in counts.items():
        if n > global_counts[w] // 100:
            specific.append(w)
    specific.sort(key=counts.get)
    specific.reverse()
    return specific


counts = []
with open('MPs.txt', 'rb') as f:
    for mp in f:
        mp = mp.decode('utf-8').strip()
        document = Task(get_data, mp)
        counts.append(Task(count_words, mp, document))
avgs = Task(add_counts, counts)
results = []
for c in counts:
    results.append(Task(divergence, avgs, len(counts), c))
