import itertools
import javatools
import os
import zipfile

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


def expand_classpath_entry(entry):
    if os.path.isdir(entry) or is_jar(entry):
        return [entry]
    elif os.path.basename(entry) == '*':
        entry = os.path.dirname(entry)
        contents = [os.path.join(entry, c) for c in os.listdir(entry)]
        return [c for c in contents if is_jar(c)]
    else:
        raise ValueError('Invalid classpath entry: {}'.format(entry))


def open_classpath_entry(entry):
    if os.path.isdir(entry):
        return ExplodedZipFile(entry)
    elif is_jar(entry):
        return zipfile.ZipFile(entry, 'r')
    else:
        raise ValueError('Invalid classpath entry: {}'.format(entry))


class ClassLoader(object):
    def __init__(self, paths):
        entries = [expand_classpath_entry(p) for p in paths]
        self.entries = list(itertools.chain.from_iterable(entries)) # flatten

        # {Package : {class name : LinkableClass}}
        self.packages = {}

    def load(self, name):
        package, class_name = parse_name(name)

        try:
            return self.packages[package][class_name]
        except KeyError:
            clazz = self.find(name)
            if clazz:
                if clazz.package != package or clazz.name != class_name:
                    msg = "Wanted class '{}', but '{}' was loaded"
                    raise ValueError(msg.format(name, clazz))

                classes = self.packages.setdefault(package, {})
                classes[class_name] = clazz

            return clazz

    def find(self, name):
        package, class_name = parse_name(name)
        path = package.get_member_path(class_name)

        for entry in self.entries:
            with open_classpath_entry(entry) as jar:
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

        for entry in self.entries:
            with open_classpath_entry(entry) as jar:
                try:
                    jar.getinfo(package.path)
                except KeyError:
                    pass
                else:
                    # TODO avoid changing state in find method
                    self.packages[package] = {}
                    return package

        return None


class ExplodedZipFile(ziputils.ExplodedZipFile):
    """A ZipFile-like object that wraps a directory.

    Changes the behavior of javatools.ziputils.ExplodedZipFile to be
    more consistent with zipfile.ZipFile by raising a KeyError if an
    entry does not exist. It also provides a closing context for use in
    ``with`` statements.
    """

    def open(self, name, mode='rb'):
        if not os.path.isfile(os.path.join(self.fn, name)):
            raise KeyError("There is no item named '{}' in the archive".format(name))
        return super(ExplodedZipFile, self).open(name, mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return exc_type is None
