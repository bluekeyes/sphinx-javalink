import os
import urlparse

import docutils.nodes
import docutils.utils

from docutils.parsers import rst
from sphinx.util.nodes import split_explicit_title

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
                if clazz.has_member(what):
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

    # TODO: does this need to encode the URL?
    def to_url(self, where, what=None):
        root = self._find_url_root(where)
        if not root:
            raise LookupError("Missing root URL for reference '{}'".format(where))

        path = where.replace('.', '/').replace('$', '.')
        path += '.html'
        if what:
            # TODO this probably needs work
            path += '#{}'.format(what)

        return root + path

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
        _, title, reftext = split_explicit_title(text)

        url, warnings = self.find_url(reftext)
        if url:
            # if no scheme, assume a local path relative to the src root
            if not urlparse.urlparse(url).scheme:
                docdir = os.path.dirname(inliner.document.current_source)
                url = os.path.relpath(self.env.srcdir, docdir) + '/' + url

            ref = docutils.nodes.reference(title, title, internal=False, refuri=url)
        else:
            ref = docutils.nodes.inline(rawsource=title, text=title)

        return [ref], [inliner.reporter.warning(w, line=lineno) for w in warnings]
