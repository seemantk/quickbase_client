import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "quickbase_client",
    version = "0.2.2",
    author = "Seemant Kulleen",
    author_email = "seemant@kulleen.org",
    description = ("A simple and incomplete Python interface to the"
                    "Quickbase HTTP API."),
    license = "MIT",
    keywords = "quickbase",
    url = "https://github.com/seemant/quickbase_client",
    packages=['quickbase', ],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.6",
    ],
)

