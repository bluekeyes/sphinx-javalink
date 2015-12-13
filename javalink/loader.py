import javatools
import os
import zipfile

from itertools import chain as flatten
from javatools import ziputils

from .model import LinkableClass, Package, parse_name

def extract_class(jar, name):
    """Extracts a LinkableClass from a jar.

    Args:
        jar: An open ZipFile instance.
        name: A string containing the binary name of a class.

    Raises:
        KeyError: The class does not exist in the jar.
    """

    with jar.open(name) as entry:
        return LinkableClass(javatools.unpack_class(entry))


def is_jar(path):
    return path.endswith('.jar') and zipfile.is_zipfile(path)


def expand_path(path):
    if os.path.isdir(path) or is_jar(path):
        return [path]
    elif os.path.basename(path) == '*':
        path = os.path.dirname(path)
        contents = [os.path.join(path, c) for c in os.listdir(path)]
        return [c for c in contents if is_jar(c)]
    else:
        raise ValueError('Invalid classpath entry: {}'.format(path))


def open_resource(path):
    if os.path.isdir(path):
        return ExplodedZipFile(path)
    elif is_jar(path):
        return zipfile.ZipFile(path, 'r')
    else:
        raise ValueError('Invalid classpath entry: {}'.format(path))


class ClassLoader(object):
    def __init__(self, paths):
        expanded_paths = [expand_path(p) for p in paths]
        self.paths = list(flatten.from_iterable(expanded_paths))

        self.resources = [open_resource(p) for p in self.paths]

        # {Package : {class name : LinkableClass}}
        self.packages = {}

    def load(self, name):
        package, class_name = parse_name(name)

        try:
            return self.packages[package][class_name]
        except KeyError:
            clazz = self.find(name)
            if clazz and (clazz.package != package or clazz.name != class_name):
                msg = "Wanted class '{}', but '{}' was loaded"
                raise ValueError(msg.format(name, clazz))

            classes = self.packages.setdefault(package, {})
            classes[class_name] = clazz
            return clazz

    def find(self, name):
        package, class_name = parse_name(name)
        path = package.get_member_path(class_name)

        for jar in self.resources:
            try:
                return extract_class(jar, path)
            except KeyError:
                pass

        return None

    # TODO take either a Package or a string name
    def find_package(self, name):
        package = Package(name.split('.'))

        if package in self.packages:
            return package

        for jar in self.resources:
            try:
                jar.getinfo(package.path)
            except KeyError:
                pass
            else:
                # TODO avoid changing state in find method
                self.packages[package] = {}
                return package

        return None

    def close(self):
        for resource in self.resources:
            resource.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return exc_type is None

    def __getstate__(self):
        obj = self.__dict__.copy()
        del obj['resources']
        return obj

    def __setstate__(self, obj):
        resources = [open_resource(p) for p in obj['paths']]
        self.__dict__.update(obj)
        self.resources = resources


class ExplodedZipFile(ziputils.ExplodedZipFile):
    """A ZipFile-like object that wraps a directory.

    Changes the behavior of javatools.ziputils.ExplodedZipFile to be
    more consistent with zipfile.ZipFile by raising a KeyError if an
    entry does not exist. It also provides a closing context for use in
    ``with`` statements.
    """

    def open(self, name, mode='rb'):
        try:
            return super(ExplodedZipFile, self).open(name, mode)
        except IOError:
            raise KeyError("There is no item named '{}' in the archive".format(name))

    def getinfo(self, name):
        info = super(ExplodedZipFile, self).getinfo(name)
        if not info:
            raise KeyError("There is no item named '{}' in the archive".format(name))
        return info

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return exc_type is None
