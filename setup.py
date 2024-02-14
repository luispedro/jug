# -*- coding: utf-8 -*-
# Copyright (C) 2008-2024, Luis Pedro Coelho <luis@luispedro.org>
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


from sys import exit
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

install_requires = open('requirements.txt').read()
tests_require = open('test-requirements.txt').read()

classifiers = [
'Development Status :: 5 - Production/Stable',
'Environment :: Console',
'License :: OSI Approved :: MIT License',
'Operating System :: POSIX',
'Operating System :: OS Independent',
'Programming Language :: Python',
'Programming Language :: Python :: 3',
'Programming Language :: Python :: 3.5',
'Programming Language :: Python :: 3.6',
'Programming Language :: Python :: 3.7',
'Programming Language :: Python :: 3.8',
'Programming Language :: Python :: 3.9',
'Programming Language :: Python :: 3.10',
'Programming Language :: Python :: 3.11',
'Programming Language :: Python :: 3.12',
'Topic :: Scientific/Engineering',
'Topic :: Software Development',
'Topic :: System :: Distributed Computing',
'Intended Audience :: Science/Research',
]

setuptools.setup(name = 'Jug',
      version = __version__, # noqa: F821
      description = 'A Task Based Parallelization Framework',
      long_description = long_description,
      author = 'Luis Pedro Coelho',
      author_email = 'luis@luispedro.org',
      license = 'MIT',
      platforms = ['Any'],
      classifiers = classifiers,
      url = 'https://jug.readthedocs.io',
      packages = setuptools.find_packages(),
      entry_points={
          'console_scripts': [
              'jug = jug.jug:main',
          ],
      },
      scripts = ['bin/jug-execute'],
      install_requires = install_requires,
      tests_require = tests_require,
      )


