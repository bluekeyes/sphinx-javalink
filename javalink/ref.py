import contextlib
import os
import traceback
import urllib2

import docutils.nodes
import docutils.utils

from urllib import quote as urlquote, pathname2url
from urlparse import urlparse, urlunparse, urljoin

from docutils.parsers import rst
from sphinx.util.nodes import split_explicit_title

from .loader import ClassLoader
from .model import parse_name


CONFIG_VALUES = {
    'javalink_classpath': ([], 'env', 'javalink_classloader'),
    'javalink_docroots': ([], 'env', 'javalink_packages'),
    'javalink_default_version': (7, 'env', None),
    'javalink_add_package_names': (True, 'env', None),
    'javalink_qualify_nested_types': (True, 'env', None),
    'javalink_add_method_parameters': (True, 'env', None)
}


def abspath(root, path):
    return os.path.normpath(os.path.join(root, path))


class EnvAccessor(object):
    @property
    def env(self):
        pass

    @property
    def classloader(self):
        if not hasattr(self.env, 'javalink_classloader'):
            classpath = self.env.config.javalink_classpath
            loader = ClassLoader([abspath(self.env.srcdir, p) for p in classpath])
            self.env.javalink_classloader = loader

        return self.env.javalink_classloader

    @property
    def imports(self):
        if not hasattr(self.env, 'javalink_imports'):
            self.env.javalink_imports = {}

        return self.env.javalink_imports


class JavarefImportDirective(rst.Directive, EnvAccessor):
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    @property
    def env(self):
        return self.state.document.settings.env

    def run(self):
        docname = self.env.docname
        imports = self.imports.setdefault(docname, [('java.lang', '*')])

        for i in self.content:
            package, name = parse_name(i.strip())
            if (package.name, name) not in imports:
                # TODO make this work with Package objects
                self._validate_import(package.name, name)
                imports.append((package.name, name))

        return []

    # TODO handle conflicting imports
    def _validate_import(self, package, name):
        if name == '*':
            entity = self.classloader.find_package(package)
        else:
            entity = self.classloader.load('{}.{}'.format(package, name))

        if not entity:
            self.error("unresolved import '{}.{}'".format(package, name))


def purge_imports(app, env, docname):
    if hasattr(env, 'javalink_imports'):
        try:
            del env.javalink_imports[docname]
        except KeyError:
            pass


def merge_imports(env, docnames, other):
    if not hasattr(other, 'javalink_imports'):
        return
    if not hasattr(env, 'javalink_imports'):
        env.javalink_imports = {}

    docs_with_imports = (d for d in docnames if d in other.javalink_imports)
    for doc in docs_with_imports:
        imports = other.javalink_imports.get(doc, [])
        env.javalink_imports.setdefault(doc, []).extend(imports)


def cleanup(app, exception):
    if hasattr(app.env, 'javalink_classloader'):
        app.env.javalink_classloader.close()


class JavarefRole(EnvAccessor):
    def __init__(self, app):
        self.app = app

    @property
    def env(self):
        return self.app.env

    def find_ref(self, reftext):
        reftext = reftext.strip()

        # TODO add additional validation (see SeeTagImpl.java)
        where, _, what = reftext.partition('#')
        clazz = self._find_class(where)
        if clazz:
            where = clazz.full_name
            if what:
                member = clazz.get_member(what)
                if not member:
                    raise JavarefError('unknown member: {}'.format(reftext))

                what = member.get_url_fragment()

            return where, what

        if not what:
            package = self.classloader.find_package(where)
            if package:
                return package.name + '.package-summary', None

        raise JavarefError('reference not found: {}'.format(reftext))

    def to_url(self, where, what):
        root = self._find_url_root(where)
        if not root:
            raise JavarefError('root URL not found: {}'.format(where))

        path = where.replace('.', '/').replace('$', '.')
        path += '.html'

        if what:
            java_version = self._find_java_version(where)
            path += self.to_anchor(java_version, what)

        return urljoin(root, path)

    def to_anchor(self, java_version, what):
        if java_version > 7:
            # javadoc in 8+ uses '-' as separator
            what = what.replace('(', '-').replace(')', '-').replace(', ', '-')

        return '#{}'.format(urlquote(what, ';/?:@&=+$,()-'))

    def to_title(self, where, what):
        package, name = parse_name(where)
        if name == 'package-summary':
            return package.name

        add_package_names = self.app.config.javalink_add_package_names
        qualify_nested_types = self.app.config.javalink_qualify_nested_types
        add_method_parameters = self.app.config.javalink_add_method_parameters

        title = []
        if add_package_names:
            title.append(package.name)

        if add_package_names or qualify_nested_types:
            title.append(name.replace('$', '.'))
        else:
            title.append(name.rpartition('$')[-1])

        if what:
            if add_method_parameters:
                title.append(what)
            else:
                title.append(what.partition('(')[0])

        return '.'.join(title)

    def _find_class(self, where):
        import_name = where.partition('.')[0]
        imports = self.imports.get(self.env.docname, [])

        candidates = [where]
        for package, name in imports:
            if name == import_name or name == '*':
                candidates.append('{}.{}'.format(package, where))

        for name in candidates:
            clazz = self.classloader.load(name)
            if clazz:
                return clazz

            # try all possible class nestings
            sep = name.rfind('.')
            while sep >= 0:
                name = name[:sep] + '$' + name[sep+1:]
                clazz = self.classloader.load(name)
                if clazz:
                    return clazz

                sep = name.rfind('.', 0, sep)

        return None

    def _find_url_root(self, where):
        package, _ = parse_name(where)
        return self.env.javalink_packages.get(package.name, None)

    def _find_java_version(self, where):
        package, _ = parse_name(where)
        return self.env.javalink_packages_versions.get(package.name, self.app.config.javalink_default_version)

    def __call__(self, name, rawtext, text, lineno, inliner,
                 options={}, content=[]):

        text = docutils.utils.unescape(text)
        has_title, title, reftext = split_explicit_title(text)

        warnings = []
        try:
            where, what = self.find_ref(reftext)
            url = self.to_url(where, what)
            if not has_title:
                title = self.to_title(where, what)
        except JavarefError as e:
            url = None
            warnings.append(e.reason)

        if url:
            # if no scheme, assume a local path relative to the src root
            if not urlparse(url).scheme:
                docdir = os.path.dirname(inliner.document.current_source)
                if docdir != self.env.srcdir:
                    url = os.path.relpath(self.env.srcdir, docdir) + '/' + url

            ref = docutils.nodes.reference('', '', internal=False, refuri=url)
            ref.append(docutils.nodes.literal(rawsource=title, text=title))
        else:
            ref = docutils.nodes.literal(rawsource=title, text=title)

        return [ref], [inliner.reporter.warning(w, line=lineno) for w in warnings]


class JavarefError(Exception):
    """Raised when a reference to a Java element cannot be resolved.

    Attributes:
        reason: reason why the reference is unresolved
    """

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)


def initialize_package_list(app):
    env = app.env
    if hasattr(env, 'javalink_packages') and hasattr(env, 'javalink_packages_versions'):
        return

    app.verbose('[javalink] initializing package list...')
    env.javalink_packages = {}
    env.javalink_packages_versions = {}

    for docroot_dict in [normalize_docroot(app, r) for r in app.config.javalink_docroots]:
        try:
            with contextlib.closing(urllib2.urlopen(docroot_dict['root'])) as package_list:
                for package in package_list:
                    package = package.strip()
                    if package not in env.javalink_packages:
                        env.javalink_packages[package] = docroot_dict['base']
                        env.javalink_packages_versions[package] = docroot_dict['version']
                    else:
                        app.warn("[javalink] duplicate package '{}' in {}".format(package, url))

        except urllib2.URLError:
            app.warn('[javalink] could not get {}; some links may not resolve'.format(url))
            app.verbose('[javalink] %s', traceback.format_exc())


def normalize_docroot(app, root):
    """Creates a package-list URL and a link base from a docroot element.

    Args:
        app: the global app object
        root: the docroot element [string or dictionary]
    """

    srcdir = app.env.srcdir
    default_version = app.config.javalink_default_version

    if isinstance(root, basestring):
        (url, base) = _parse_docroot_str(srcdir, root)

        return {'root':url, 'base':base, 'version':default_version}
    else:
        if 'base' in root:
            root['base'] = _parse_docroot_str(srcdir, root['base'])[1]
        else:
            root['base'] = _parse_docroot_str(srcdir, root['root'])[1]

        root['root'] = _parse_docroot_str(srcdir, root['root'])[0]

        if 'version' not in root:
            root['version'] = default_version

        return root


def _parse_docroot_str(srcdir, root):
    scheme, netloc, path = urlparse(root)[0:3]
    if not scheme:
        # assume local path; add trailing '/'s if missing
        root = os.path.join(root, '')
        absroot = os.path.join(abspath(srcdir, root), '')

        url = urljoin('file:///', pathname2url(absroot))
        base = pathname2url(root)
    else:
        path = path.rstrip('/') + '/'

        url = urlunparse((scheme, netloc, path, '', '', ''))
        base = url

    return (urljoin(url, 'package-list'), base)
