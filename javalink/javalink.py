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


class JavadocImportDirective(rst.Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    def run(self):
        env = self.state.document.settings.env

        if not hasattr(env, 'javalink_imports'):
            env.javalink_imports = {}

        if not env.docname in env.javalink_imports:
            env.javalink_imports[env.docname] = []

        if not hasattr(env, 'javalink_classloader'):
            classpath = env.config.javalink_classpath
            env.javalink_classloader = ClassLoader(classpath)

        # TODO handle conflicting imports
        imports = []
        for i in self.content:
            package, name = i.strip().rsplit('.', 1)
            self._validate_import(package, name)
            imports.append((package, name))

        env.javalink_imports[env.docname].extend(imports)

        return []

    def _validate_import(self, package, name):
        cl = self.state.document.settings.env.javalink_classloader
        assert cl, 'no classloader'

        entity = None
        if name == '*':
            entity = cl.find_package(package)
        else:
            entity = cl.load('{}.{}'.format(package, name))

        if not entity:
            self.error("unresolved import '{}.{}'".format(package, name))


class JavaRefRole:
    def __init__(self, app):
        self.app = app

    def find_url(self, reftext):
        reftext = reftext.strip()

        # TODO add additional validation (see SeeTagImpl.java)
        where, _, what = reftext.partition('#')

        clazz = self._find_class(where)
        if clazz:
            where = clazz.full_name
            if what:
                # TODO handle member ambiguity
                if clazz.has_member(what):
                    return self.to_url(where, what)
                else:
                    return None
            else:
                return self.to_url(where)

        if not what:
            package = self.app.env.javalink_classloader.find_package(where)
            if package:
                where = package.name + '.package-summary'
                return self.to_url(where)

        return None

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
        imports = self.app.env.javalink_imports.get(self.app.env.docname, [])

        candidates = []
        for package, name in imports:
            if name == import_name or name == '*':
                candidates.append('{}.{}'.format(package, where))

        classloader = self.app.env.javalink_classloader
        for name in candidates:
            clazz = classloader.load(name)
            if clazz:
                return clazz

            # try all possible class nestings
            sep = name.rfind('.')
            while sep >= 0:
                name = name[:sep] + '$' + name[sep+1:]
                clazz = classloader.load(name)
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

        url = self.find_url(reftext)
        if url:
            # TODO make this better
            if not urlparse.urlparse(url).scheme:
                path_to_root = os.path.relpath(self.app.env.srcdir, os.path.dirname(inliner.document.current_source))
                url = path_to_root + '/' + url

            ref = docutils.nodes.reference(title, title, internal=False, refuri=url)
            return [ref], []
        else:
            ref = docutils.nodes.inline(rawsource=title, text=title)
            msg = 'reference not found: {}'.format(reftext)
            return [ref], [inliner.reporter.warning(msg, line=lineno)]

        pass
