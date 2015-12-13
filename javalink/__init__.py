import os
import subprocess
import sys

from sphinx.errors import ExtensionError

from . import ref

def setup(app):
    """Register the extension with Sphinx.

    Args:
        app: The Sphinx application.
    """

    for name, (default, rebuild, _) in ref.CONFIG_VALUES.iteritems():
        app.add_config_value(name, default, rebuild)

    app.add_directive('javaimport', ref.JavarefImportDirective)
    app.add_role('javaref', ref.JavarefRole(app))

    # initialize_package_list must happen after validate_env
    app.connect('builder-inited', validate_env)
    app.connect('builder-inited', ref.initialize_package_list)

    app.connect('env-purge-doc', ref.purge_imports)
    app.connect('env-merge-info', ref.merge_imports)

    app.connect('build-finished', ref.cleanup)


def validate_env(app):
    """Purge expired values from the environment.

    When certain configuration values change, related values in the
    environment must be cleared. While Sphinx can rebuild documents on
    configuration changes, it does not notify extensions when this
    happens. Instead, cache relevant values in the environment in order
    to detect when they change.

    Args:
        app: The Sphinx application.
    """

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
    """Find the path to the Java standard library jar.

    The jar is expected to exist at the path 'jre/lib/rt.jar' inside a
    standard Java installation directory. The directory is found using
    the following procedure:

    1. If the javehome argument is provided, use the value as the
       directory.
    2. If the JAVA_HOME environment variable is set, use the value as
       the directory.
    3. Find the location of the ``java`` binary in the current PATH and
       compute the installation directory from this location.

    Args:
        javahome: A path to a Java installation directory (optional).
    """

    if not javahome:
        if 'JAVA_HOME' in os.environ:
            javahome = os.environ['JAVA_HOME']
        elif sys.platform == 'darwin':
            # The default java binary on OS X is not part of a standard Oracle
            # install, so building paths relative to it does not work like it
            # does on other platforms.
            javahome = _find_osx_javahome()
        else:
            javahome = _get_javahome_from_java(_find_java_binary())

    rtpath = os.path.join(javahome, 'jre', 'lib', 'rt.jar')
    if not os.path.isfile(rtpath):
        msg = 'Could not find rt.jar: {} is not a file'.format(rtpath)
        raise ExtensionError(msg)

    return rtpath


def _find_osx_javahome():
    return subprocess.check_output(['/usr/libexec/java_home']).strip()


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
