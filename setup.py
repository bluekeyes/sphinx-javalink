from setuptools import setup

long_description="""
sphinx-javalink
===============

A Sphinx_ extension for linking to ``javadoc``-generated API documentation.

Usage
-----

See the `GitHub project`_ for documentation.

.. _Sphinx: http://sphinx-doc.org/
.. _GitHub project: https://github.com/bluekeyes/sphinx-javalink
"""

setup(
    name='sphinx-javalink',
    version='0.11.0',

    description='Link to Javadoc APIs from Sphinx documentation',
    long_description=long_description,

    url='https://github.com/bluekeyes/sphinx-javalink',

    author='Billy Keyes',
    author_email='bluekeyes@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Framework :: Sphinx :: Extension',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Java',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    keywords='javadoc java sphinx documentation',

    packages=['javalink'],

    install_requires=['sphinx >=1.2', 'javatools >=1.3']
)
