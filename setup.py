#!/usr/bin/env python

from distutils.core import setup

setup(name='django-gtileoverlay',
    version=__import__('gtileoverlay').__version__,
    description='Create GTileOverlay images in Django for the Google Maps API',
    author='Chris Priest',
    author_email='cp368202@ohiou.edu',
    url='http://github.com/nbv4/django-gtileoverlay',
    packages=['gtileoverlay'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ]
    requires=['django (>=1.0)']
)
