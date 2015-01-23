# sphinx-javalink

A [Sphinx][sphinx] extension for linking to `javadoc`-generated API
documentation.

## Usage

Use the `javaref` role to link to Java types, members, and packages:

    Alpacas are best stored in a :javaref:`java.util.HashMap`, while clients
    may find that goats perform best in a :javaref:`java.util.TreeMap`. In
    either case, use :javaref:`biz.cloudgoats.api.Wizard#convert(Object)` to
    produce legally binding contracts.

    For more details, see the :javaref:`biz.cloudgoats.api` package.

Link targets use the same syntax as Javadoc's [`@see`][seetag] tag. Reference
titles are automatically generated based on the configuration options described
below. To use an explicit title, place the Java reference in angle brackets
following the title:

    :javaref:`I like objects! <java.lang.Object>`

By default, references must be fully qualified. For convenience, use the
`javaimport` directive to import commonly used types:

    .. javaimport::
       java.util.*
       biz.cloudgoats.api.Wizard

    Alpacas are best stored in a :javaref:`HashMap`, while clients may find
    that goats perform best in a :javaref:`TreeMap`. In either case, use
    :javaref:`Wizard#convert(Object)` to produce chocolate covered pebbles or
    peanuts, depending on environmental factors.

    For more details, see the :javaref:`biz.cloudgoats.api` package.

Each import appears on its own line and may be either a type or a package name
followed by a `*`. As in Java, this imports all types in the package.  All
types in the `java.lang` package are imported by default.

The `javaimport` directive must appear before the first `javaref` that uses one
of the imported types. A document can have multiple `javaimport` directives;
the imports are cumulative.

### Configuration

#### `javalink_classpath`

_Default:_ `[]`

A list of jar files and directories in which to search for classes. Elements
can take one of three forms:

1. `/path/to/library.jar` - an absolute or relative path to a jar file
2. `/path/to/classes/dir` - an absolute or relative path a directory containing
   class files
3. `/path/to/jar/dir/*` - an absolute or relative path a directory containing
   jar files. Only jar files that are direct children of the directory are
   loaded.

All relative paths are relative to the source directory. For more details, see
the [the Java documentation][classpath].

To link to classes in the standard library, `rt.jar` (shipped with the JRE)
must be on the class path. Use `javalink.find_rt_jar()` to find the location of
this jar on the local system. This function respects the `JAVA_HOME` environment
variable and may optionally take the path to an alternative directory as an
argument.

#### `javalink_docroots`

_Default:_ `[]`

A list of paths or URLs referencing existing Javadoc documentation that can be
the target of links. A valid [`package-list`][packagelist] file must exist in
the directory specified by the path or URL.

List elements may be either strings or tuples of strings. For tuples, the first
element is used to find the `package-list` file and the second is used as the
base for generated links. This is useful when the `package-list` is available
at a local path will not be available from the built and published
documentation. This also allows offline builds, by downloading all remote
`package-list` files ahead of time.

#### `javalink_add_method_parameters`

_Default:_ `True`

A boolean that determines if parameter lists and parentheses are appended to
generated method references. References with explicit titles are not modified.

#### `javalink_add_package_names`

_Default:_ `True`

A boolean that determines if fully-qualified package names are prepended to
generated references. References with explicit titles are not modified.

#### `javalink_qualify_nested_types`

_Default:_ `True`

A boolean that determines if containing type names are prepended to generated
references to nested types. Only applies if `javalink_add_package_names` is
`False`.  References with explicit titles are not modified.

## Limitations and Known Issues

* When linking to methods, only the types of arguments may be specified.
  Specifying argument names will produce incorrect results.
* All references are created as `literal` nodes

## Requirements

* Python 2.7 (no support for Python 3)
* Sphinx
* [javatools][javatools]

## Contributing

Pull requests, bug reports, and feature requests are welcome.

## License

[MIT][mit], see `LICENSE` file.

[sphinx]: http://sphinx-doc.org/
[seetag]: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/javadoc.html#see
[classpath]: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/classpath.html
[packagelist]: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/javadoc.html#linkpackagelist
[javatools]: https://github.com/obriencj/python-javatools
[mit]: http://opensource.org/licenses/MIT
