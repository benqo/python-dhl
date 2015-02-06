from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
long_description = """\
This is a python package for using the DHL webservice.
It allows developers to easily connect to DHL services and make requests.
The package creates SOAP requests using the suds-jurko package (https://pypi.python.org/pypi/suds-jurko/0.6)
to create shipments, to schedule a pickup and possibly to delete a created shipment.
It also provides the ability to save the shipping labels.
"""

setup(
    name='python-dhl',

    version='1.0.0.dev7',

    description='Python package for DHL webservice',
    long_description=long_description,

    url='https://github.com/benqo/python-dhl',

    author='Benjamin Polovic',
    author_email='benkoman@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        # 'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.6',
        #'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.2',
        #'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    packages=['dhl', 'dhl/resources'],

    install_requires=['suds-jurko'],
)
