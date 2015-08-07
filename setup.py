# -*- coding: utf-8 -*-
# Copyright (C) 2008-2013, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.


from sys import exit, version_info
try:
    import setuptools
except:
    from sys import stdout
    stdout.write('''
setuptools not found. Please install it.

On linux, the package is often called python-setuptools\n''')
    exit(1)

exec(compile(open('jug/jug_version.py').read(), 'jug/jug_version.py', 'exec'))
long_description = open('README.rst').read()

classifiers = [
'Development Status :: 4 - Beta',
'Environment :: Console',
'License :: OSI Approved :: MIT License',
'Operating System :: POSIX',
'Operating System :: OS Independent',
'Programming Language :: Python',
'Topic :: Scientific/Engineering',
'Topic :: Software Development',
'Topic :: System :: Distributed Computing',
'Intended Audience :: Science/Research',
]

install_requires = ['six', 'redis']
if version_info < (2, 7):
    install_requires.append('ordereddict')

setuptools.setup(name = 'Jug',
      version = __version__,
      description = 'A Task Based Parallelization Framework',
      long_description = long_description,
      author = 'Luis Pedro Coelho',
      author_email = 'luis@luispedro.org',
      license = 'MIT',
      platforms = ['Any'],
      classifiers = classifiers,
      url = 'http://luispedro.org/software/jug',
      packages = setuptools.find_packages(),
      scripts = ['bin/jug', 'bin/jug-execute'],
      test_suite = 'nose.collector',
      install_requires=install_requires,
      )


