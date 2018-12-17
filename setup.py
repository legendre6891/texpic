from distutils.core import setup
from Cython.Build import cythonize

directives = {'boundscheck': False, 'wraparound': False}
setup(name='split_pnm_stream', ext_modules=cythonize('split_pnm_stream.pyx', compiler_directives = directives, annotate=True))
