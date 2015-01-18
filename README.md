# sphinx-javalink

A [Sphinx][sphinx] extension for linking to `javadoc`-generated API
documentation.

## Usage

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

#### `add_function_parentheses`

_Default:_ `True`

A boolean that determines if argument lists and parentheses are appended to
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

## Limitations

While this extension should work for most use cases, it has several
limitations. Many of these could be fixed with more effort and may be removed
in the future.

* When linking to methods, only the types of arguments may be specified.
  Specifying argument names will produce incorrect results.

[sphinx]: http://sphinx-doc.org/
[classpath]: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/classpath.html
[packagelist]: http://docs.oracle.com/javase/7/docs/technotes/tools/windows/javadoc.html#linkpackagelist
