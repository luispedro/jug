# Types in Jug

Any type that can be pickled can be used with jug tasks. However, it
might sometimes be wiser to break up your tasks in ways that minimise the
communication necessary. For example, consider the following image processing
code:

```
from glob import glob
from mahotas import imread
from jug import Task

def process(img):
    # complex image processing
    ...

files = glob('inputs/*.png')
imgs = [Task(imread, f) for f in files]
props = [Task(process, img) for img in imgs]
```

This will work just fine, but it will save too much intermediate data. Consider
rewriting this to:

```
from glob import glob
from jug import Task

def process(f):
    from mahotas import imread
    img = imread(f)
    # complex image processing
    ...

files = glob('inputs/*.png')
props = [Task(process, f) for f in files]
```

I have also moved the import of `mahotas.imread` to inside the `process`
function. This is another micro-optimisation: it makes `jug status` and
friends just that little bit faster (as they do not need to perform this import
to do their jobs).

## How results are stored

By default, results are pickled and compressed. With the default filesystem
backend, numpy arrays are instead saved in numpy's `.npy` format and
[polars](https://pola.rs/) DataFrames as parquet files, which is faster and
does not require pickling (numpy arrays with `dtype=object` are still
pickled).
