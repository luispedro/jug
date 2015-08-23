===========================
Image Segmentation Tutorial
===========================

This was originally material for a presentation and `blog post
<https://metarabbit.wordpress.com/2013/05/20/segmenting-images-in-parallel-with-python-jug/>`__.
You can get the `slides online <http://luisepdro.org/talks/2013/jug-meetup>`__.

Let us imagine you are trying to compare two image segmentation algorithms
based on human-segmented images. This is a completely real-world example as it
`was one of the projects where I first used jug
<https://github.com/luispedro/Coelho2009_ISBI_NuclearSegmentation>`__ [#]_.

It depends on `mahotas <http://mahotas.readthedocs.org/>`__ for image
processing.

We are going to build this up piece by piece.

First a few imports::

    import mahotas as mh
    from jug import TaskGenerator
    from glob import glob

Here, we test two thresholding-based segmentation method, called ``method1`` and
``method2``. They both (i) read the image, (ii) blur it with a Gaussian, and
(iii) threshold it [#]_::

    @TaskGenerator
    def method1(image):
        # Read the image
        image = mh.imread(image)[:, :, 0]
        image  = mh.gaussian_filter(image, 2)
        binimage = (image > image.mean())
        labeled, _ = mh.label(binimage)
        return labeled

    @TaskGenerator
    def method2(image):
        image = mh.imread(image)[:, :, 0]
        image  = mh.gaussian_filter(image, 4)
        image = mh.stretch(image)
        binimage = (image > mh.otsu(image))
        labeled, _ = mh.label(binimage)
        return labeled


We need a way to compare these. We will use the `Adjusted Rand Index
<http://en.wikipedia.org/wiki/Rand_index>`__ [#]_::

    @TaskGenerator
    def compare(labeled, ref):
        from milk.measures.cluster_agreement import rand_arand_jaccard
        ref = mh.imread(ref)
        return rand_arand_jaccard(labeled.ravel(), ref.ravel())[1]

Running over all the images **looks exactly like Python**::

    results = []
    for im in glob('images/*.jpg'):
        m1 = method1(im)
        m2 = method2(im)
        ref = im.replace('images', 'references').replace('jpg', 'png')
        v1 = compare(m1, ref)
        v2 = compare(m2, ref)
        results.append( (v1,v2) )

But how do we get the results out?

A simple solution is to write a function which writes to an output file::

    @TaskGenerator
    def print_results(results):
        import numpy as np
        r1, r2 = np.mean(results, 0)
        with open('output.txt', 'w') as out:
            out.write('Result method1: {}\nResult method2: {}\n'.format(r1,
                                                                        r2))
    print_results(results)

§

**Except for the ``TaskGenerator`` this would be a pure Python file!**

With ``TaskGenerator``, we get jugginess!

We can call::

    jug execute &
    jug execute &
    jug execute &
    jug execute &

to get 4 processes going at once.

§

Note also the line::

    print_results(results)

``results`` is a list of ``Task`` objects. This is *how you define a
dependency*. Jug picks up that to call ``print_results``, it needs all the
``results`` values and behaves accordingly.

Easy as Py.

§

The full script above including data is available `from github
<https://github.com/luispedro/jug-presentations/tree/master/jug-segmentation-tutorial>`__

.. [#] The code in that repository still uses a pretty old version of jug, this
   was 2009, after all. ``TaskGenerator`` had not been invented yet.

.. [#] This is for demonstration purposes; the paper had better methods, of
   course.

.. [#] Again, you can do better than Adjusted Rand, as we show in the paper;
   but **this is a demo**. This way, we can just call a function in `milk
   <http://luispedro.org/software/milk>`__

