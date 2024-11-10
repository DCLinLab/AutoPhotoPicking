from setuptools import setup, Extension
import numpy


setup(
    ext_modules=[
        Extension(
            "segmentation.gwdt.gwdt_impl",
            ["segmentation/gwdt/gwdt_impl.pyx"],
            language="c++",
            include_dirs=[numpy.get_include()]
        )
    ]
)

