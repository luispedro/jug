============
Types in Jug
============

Any type that can be ``pickle()d`` can be used with jug tasks. However, it
might sometimes be wiser to break up your tasks in ways that minimise the
communication necessary. For example, consider the following image processing
code::

    from glob import glob
    from mahotas import imread

    def process(img):
        # complex image processing

    files = glob('inputs/*.png')
    imgs = [Task(imread, f) for f in files]
    props = [Task(process, img) for img in imgs]

This will work just fine, but it will save too much intermediate data. Consider
rewriting this to::

    from glob import glob

    def process(f):
        from mahotas import imread
        img = imread(f)
        # complex image processing

    files = glob('inputs/*.png')
    props = [Task(process, f) for f in files]

I have also moved the import of ``mahotas.imread`` to inside the ``process``
function. This is another micro-optimisation: it makes ``jug status`` and
friends just that little bit faster (as they do not need to perform this import
to do their jobs).

