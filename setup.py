from setuptools import setup, Extension
import numpy


setup(
    ext_modules=[
        Extension(
            "utils.gwdt.gwdt_impl",
            ["utils/gwdt/gwdt_impl.pyx"],
            language="c++",
            include_dirs=[numpy.get_include()]
        )
    ]
)

