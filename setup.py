from setuptools import setup, Extension
import numpy


setup(
    ext_modules=[
        Extension(
            "img_proc.gwdt.gwdt_impl",
            ["img_proc/gwdt/gwdt_impl.pyx"],
            language="c++",
            include_dirs=[numpy.get_include()]
        )
    ]
)

