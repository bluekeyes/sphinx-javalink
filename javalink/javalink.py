from docutils.parsers import rst

from loader import ClassLoader

def setup(app):
    app.add_config_value('javalink_classpath', [], '')
    app.add_config_value('javalink_package_roots', {
        'java': 'http://docs.oracle.com/javase/7/docs/api/',
        'javax': 'http://docs.oracle.com/javase/7/docs/api/'
    }, '')

    app.add_directive('javaimport', JavadocImportDirective)
    app.add_role('javaref', create_javaref_role(app))


class JavadocImportDirective(rst.Directive):
    required_arguments = 0
    optional_arguments = 0
    has_content = True

    def run(self):
        env = self.state.document.settings.env

        if not hasattr(env, 'javalink_imports'):
            env.javalink_imports = {}

        if not self.docname in env.javalink_imports:
            env.javalink_imports[self.docname] = []

        if not hasattr(env, 'javalink_classloader'):
            classpath = env.config.javalink_classpath
            env.javalink_classloader = ClassLoader(classpath)

        imports = []
        for i in self.contents:
            package, name = i.rsplit('.', 1)
            self._validate_import(package, name)
            imports.append((package, name))

        env.javalink_imports[self.docname].extend(imports)

        return []

    def _validate_import(self, package, name):
        cl = self.state.document.settings.env.javalink_classloader

        entity = None
        if name == '*':
            entity = cl.find_package(package)
        else:
            entity = cl.load('{}.{}'.format(package, name))

        if not entity:
            self.error("unresolved import '{}.{}'".format(package, name))


def create_javaref_role(app):
    def javaref_role(name, rawtext, text, lineno, inliner,
                     options={}, content=[]):
        pass

    return javaref_role
