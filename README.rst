***************
sphinx-javalink
***************

A Sphinx_ extension for linking to ``javadoc``-generated API documentation.

.. _Sphinx: http://sphinx-doc.org/

.. contents::
   :local:
   :depth: 1
   :backlinks: none

Installation
============

``sphinx-javalink`` is availabe from PyPI_:

.. code-block:: console

    pip install sphinx-javalink

.. _PyPI: https://pypi.python.org/pypi/sphinx-javalink

Usage
=====

Use the ``javaref`` role to link to Java types, members, and packages:

.. code-block:: rst

    Alpacas are best stored in a :javaref:`java.util.HashMap`, while clients
    may find that goats perform best in a :javaref:`java.util.TreeMap`. In
    either case, use :javaref:`biz.cloudgoats.api.Wizard#convert(Object)` to
    produce legally binding contracts.

    For more details, see the :javaref:`biz.cloudgoats.api` package.

Reference targets use standard Javadoc ``@see`` and ``@link`` syntax_.
Reference titles are generated based on the configuration options described
below. To use an explicit title, place the Java reference in angle brackets
following the title:

.. code-block:: rst

    :javaref:`I like objects! <java.lang.Object>`

By default, references must be fully qualified. For convenience, use the
``javaimport`` directive to import commonly used types:

.. code-block:: rst

    .. javaimport::
       java.util.*
       biz.cloudgoats.api.Wizard

    Alpacas are best stored in a :javaref:`HashMap`, while clients may find
    that goats perform best in a :javaref:`TreeMap`. In either case, use
    :javaref:`Wizard#convert(Object)` to produce chocolate covered pebbles or
    peanuts, depending on environmental factors.

    For more details, see the :javaref:`biz.cloudgoats.api` package.

Each import appears on its own line and may be either a type or a package name
followed by a ``*``. As in Java, this imports all types in the package. All
types in the ``java.lang`` package are imported by default.

The ``javaimport`` directive must appear before the first ``javaref`` that uses
one of the imported types. A document can have multiple ``javaimport``
directives; the imports are cumulative.

.. _syntax: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/javadoc.html#see

Examples
========

A simple example_ ``conf.py`` is included in the repository. For real-world
examples, see these projects:

- Giraffe_

.. _example: examples/conf.py
.. _Giraffe: https://github.com/palantir/giraffe

Configuration
=============

``javalink_classpath``
^^^^^^^^^^^^^^^^^^^^^^

*Default:* ``[]``

A list of jar files and directories in which to search for classes.  Elements
can take one of three forms:

1. ``/path/to/library.jar`` - an absolute or relative path to a jar file
2. ``/path/to/classes/dir`` - an absolute or relative path a directory
   containing class files
3. ``/path/to/jar/dir/*`` - an absolute or relative path a directory containing
   jar files. Only jar files that are direct children of the directory are
   loaded.

All relative paths are relative to the source directory.

To link to classes in the standard library, ``rt.jar`` (shipped with the JRE)
must be on the class path. Use ``javalink.find_rt_jar()`` to find the location
of this jar on the local system. This function respects the ``JAVA_HOME``
environment variable and may optionally take the path to an alternative
directory as an argument.

``javalink_docroots``
^^^^^^^^^^^^^^^^^^^^^

*Default:* ``[]``

A list of Javadocs that can be the target of links. A valid |package-list|_
file must exist in the directory specified by the root path or URL.

List elements may be either:

1. A string
2. A dictionary with the following keys:

   - ``root`` (string, required)
   - ``base`` (string, optional)
   - ``version`` (integer, optional)

Providing a string is equivalent to providing a dictionary with only the
``root`` key.

``root`` is a path or URL used to fine the ``package-list`` file. ``base`` is
the base component of generated links; if it is not specified, the value of
``root`` is used. ``version`` is the version of the ``javadoc`` tool used to
generate the documentation; if it is not specified, the value of
``javalink_default_version`` is used.

Specifying a ``base`` that differs from ``root`` is useful when the
``package-list`` is available at a local path that is not available from the
built and published documentation. This also allows offline builds, by
downloading all remote ``package-list`` files ahead of time.

.. |package-list| replace:: ``package-list``
.. _package-list: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/javadoc.html#linkpackagelist

``javalink_default_version``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default:* ``7``

The version of the ``javadoc`` tool assumed if a version is not provided for a
docroot. The version determines the format of generated links, which was
changed in Java 8.

``javalink_add_method_parameters``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default:* ``True``

A boolean that determines if parameter lists and parentheses are appended to
generated method references. References with explicit titles are not modified.

``javalink_add_package_names``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default:* ``True``

A boolean that determines if fully-qualified package names are prepended to
generated references. References with explicit titles are not modified.

``javalink_qualify_nested_types``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Default:* ``True``

A boolean that determines if containing type names are prepended to generated
references to nested types. Only applies if ``javalink_add_package_names`` is
``False``. References with explicit titles are not modified.

Limitations and Known Issues
============================

- When linking to methods, only the types of arguments may be specified.
  Specifying argument names will produce incorrect results.
- All references are created as ``literal`` nodes.
- Finding references in large jars and in class paths with many entries is
  slow.

Requirements
============

- Python 2.7 (no support for Python 3)
- Sphinx
- `javatools <https://github.com/obriencj/python-javatools>`_

Contributing
============

Pull requests, bug reports, and feature requests are welcome.

License
=======

`MIT <http://opensource.org/licenses/MIT>`_, see the ``LICENSE`` file.

Changelog
=========

**0.10.1** (2015-09-02)

- Fix syntax error in ``env-merge-info`` hook (thanks to @dadouf)

**0.10.0** (2015-08-30)

- Support the ``env-merge-info`` hook
- Fix #5 - support Java 8 link formats; required a breaking change to the
  ``javalink_docroots`` syntax (thanks to @dadouf)

**0.9.2** (2015-03-08)

- Fix #3 - resolve paths relative to the source directory

**0.9.1** (2015-03-03)

- Fix #2 - correctly generate links to varargs methods
- Fix #1 - ``find_rt_jar()`` now works correctly on OS X

**0.9.0** (2015-01-25)

- Initial release
