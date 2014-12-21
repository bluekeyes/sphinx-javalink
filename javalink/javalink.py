from docutils.parsers import rst

from loader import ClassLoader

def setup(app):
    app.add_config_value('javalink_urls', [], '')

    app.add_directive('javaimport', JavadocImportDirective)
    app.add_role('javaref', create_javaref_role(app))


class JavadocImportDirective(rst.Directive):
    pass


def create_javaref_role(app):
    def javaref_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        pass

    return javaref_role
