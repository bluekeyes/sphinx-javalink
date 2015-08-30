import javalink

extensions = ['javalink']

project = u'My Project'
copyright = u'2015, My Company'

version = 1.2
release = 1.2.0

master_doc = 'index'
source_suffix = '.rst'

javalink_classpath = [
  javalink.find_rt_jar(),
  '/path/to/your/java/classes',
  '/path/to/your/libs/guava.jar'
]

javalink_docroots = [
  'http://docs.oracle.com/javase/7/docs/api/',
  'http://docs.guava-libraries.googlecode.com/git/javadoc/',

  # If your Javadocs are already online
  'http://mysite.com/mylibrary/api/',

  # If your Javadocs are local and you want to include them with Sphinx,
  # you have to manually copy the javadocs to the Sphinx build directory
  {'root': '/path/to/your/local/javadocs', 'base': 'path/relative/to/sphinx/index')
]

# In your .rst file, to link to a class named com.example.Foo, use:
# :javaref:`com.example.Foo`

# You can also use imports to save characters:
# .. javaimport::
#    com.example.Foo
#
# :javaref:`Foo`
