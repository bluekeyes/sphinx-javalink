import os

from sphinx.errors import ExtensionError

from . import ref

def setup(app):
    for name, (default, rebuild, _) in ref.CONFIG_VALUES.iteritems():
        app.add_config_value(name, default, rebuild)

    app.add_directive('javaimport', ref.JavarefImportDirective)
    app.add_role('javaref', ref.JavarefRole(app))

    # initialize_package_list must happen after validate_env
    app.connect('builder-inited', validate_env)
    app.connect('builder-inited', ref.initialize_package_list)

    app.connect('env-purge-doc', ref.purge_imports)


def validate_env(app):
    if not hasattr(app.env, 'javalink_config_cache'):
        app.env.javalink_config_cache = {}

    for conf_attr, (_, _, env_attr) in ref.CONFIG_VALUES.iteritems():
        if not env_attr:
            continue

        value = getattr(app.config, conf_attr)
        cached = app.env.javalink_config_cache.get(conf_attr, value)

        app.env.javalink_config_cache[conf_attr] = value
        if value != cached:
            app.verbose('[javalink] config.%s has changed, clearing related env', conf_attr)
            delattr(app.env, env_attr)


def find_rt_jar(javahome=None):
    if not javahome:
        if 'JAVA_HOME' in os.environ:
            javahome = os.environ['JAVA_HOME']
        else:
            javahome = _get_javahome_from_java(_find_java_binary())

    rtpath = os.path.join(javahome, 'jre', 'lib', 'rt.jar')
    if not os.path.isfile(rtpath):
        msg = 'Could not find rt.jar: {} is not a file'.format(rtpath)
        raise ExtensionError(msg)

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

    raise ExtensionError("Could not find 'java' binary in PATH")
