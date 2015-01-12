import os
import urllib

import docutils.nodes
import docutils.utils

from docutils.parsers import rst
from sphinx.util.nodes import split_explicit_title
from urlparse import urlparse, urljoin

from loader import ClassLoader

def setup(app):
    app.add_config_value('javalink_classpath', [], '')
    app.add_config_value('javalink_package_roots', {
        'java': 'http://docs.oracle.com/javase/7/docs/api/',
        'javax': 'http://docs.oracle.com/javase/7/docs/api/'
    }, '')

    app.add_directive('javaimport', JavadocImportDirective)
    app.add_role('javaref', JavaRefRole(app))

    app.connect('env-purge-doc', purge_imports)


class JavalinkEnvAccessor:
    @property
    def env(self):
        pass

    @property
    def classloader(self):
        if not hasattr(self.env, 'javalink_classloader'):
            classpath = self.env.config.javalink_classpath
            self.env.javalink_classloader = ClassLoader(classpath)

        return self.env.javalink_classloader

    @property
    def imports(self):
        if not hasattr(self.env, 'javalink_imports'):
            self.env.javalink_imports = {}

        return self.env.javalink_imports


class JavadocImportDirective(rst.Directive, JavalinkEnvAccessor):
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    @property
    def env(self):
        return self.state.document.settings.env

    def run(self):
        docname = self.env.docname

        if not docname in self.imports:
            self.imports[docname] = []

        imports = []
        for i in self.content:
            package, name = i.strip().rsplit('.', 1)
            self._validate_import(package, name)
            imports.append((package, name))

        self.imports[docname].extend(imports)
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
        env.javalink_imports.pop(docname, None)


class JavaRefRole(JavalinkEnvAccessor):
    def __init__(self, app):
        self.app = app

    @property
    def env(self):
        return self.app.env

    def find_url(self, reftext):
        reftext = reftext.strip()
        warnings = []

        # TODO add additional validation (see SeeTagImpl.java)
        where, _, what = reftext.partition('#')

        clazz = self._find_class(where)
        if clazz:
            where = clazz.full_name
            if what:
                # TODO handle member ambiguity
                member = clazz.get_member(what)
                if member:
                    what = member.get_url_fragment()
                    return self.to_url(where, what), warnings
                else:
                    warnings.append('unknown member: {}'.format(reftext))
                    return None, warnings
            else:
                return self.to_url(where), warnings

        if not what:
            package = self.classloader.find_package(where)
            if package:
                where = package.name + '.package-summary'
                return self.to_url(where), warnings

        warnings.append('reference not found: {}'.format(reftext))
        return None, warnings

    def to_url(self, where, what=None):
        root = self._find_url_root(where)
        if not root:
            raise LookupError("Missing root URL for reference '{}'".format(where))

        path = where.replace('.', '/').replace('$', '.')
        path += '.html'
        if what:
            # TODO is this the correct way to escape the URL?
            path += '#{}'.format(urllib.quote(what, ';/?:@&=+$,()'))

        return urljoin(root, path)

    def _find_class(self, where):
        import_name = where.split('.')[0]
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
        roots = self.app.config.javalink_package_roots.items()
        roots = sorted(roots, key=lambda x: len(x[0]), reverse=True)

        for root, url in roots:
            if where.startswith(root):
                if url.endswith('/'):
                    return url
                else:
                    return url + '/'

        return None

    def __call__(self, name, rawtext, text, lineno, inliner,
                 options={}, content=[]):

        text = docutils.utils.unescape(text)
        has_title, title, reftext = split_explicit_title(text)
        if not has_title:
            title = title.replace('#', '.')

        url, warnings = self.find_url(reftext)
        if url:
            # if no scheme, assume a local path relative to the src root
            if not urlparse(url).scheme:
                docdir = os.path.dirname(inliner.document.current_source)
                url = os.path.relpath(self.env.srcdir, docdir) + '/' + url

            ref = docutils.nodes.reference('', '', internal=False, refuri=url)
            ref.append(docutils.nodes.literal(rawsource=title, text=title))
        else:
            ref = docutils.nodes.literal(rawsource=title, text=title)

        return [ref], [inliner.reporter.warning(w, line=lineno) for w in warnings]


def find_rt_jar(javahome=None):
    if not javahome:
        if 'JAVA_HOME' in os.environ:
            javahome = os.environ['JAVA_HOME']
        else:
            javahome = _get_javahome_from_java(_find_java_binary())

    rtpath = os.path.join(javahome, 'jre', 'lib', 'rt.jar')
    if not os.path.isfile(rtpath):
        # TODO include javahome in this message?
        # TODO use a better exception class
        raise Exception('{} does not exist'.format(rtpath))

    return rtpath


def _get_javahome_from_java(java):
    while os.path.islink(java):
        link = java
        java = os.readlink(link)
        if not os.path.isabs(java):
            java = os.path.join(os.path.dirname(link), java)

    javahome = os.path.join(os.path.dirname(java), '..', '..')
    return os.path.normpath(javahome)


def _find_java_binary():
    path = os.environ.get('PATH', os.defpath)

    exts = os.environ.get('PATHEXT', '')
    java_names = ['java' + ext for ext in exts.split(os.pathsep)]

    for p in path.split(os.pathsep):
        p = p.strip('"')
        for name in java_names:
            java = os.path.join(p, name)
            if os.path.isfile(java) and os.access(java, os.X_OK):
                return java

    # TODO include possible solutions in this message?
    # TODO use a better exception class
    raise Exception('Could not find java executable')
