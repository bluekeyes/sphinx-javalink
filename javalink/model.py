import re

_primitive_types = {
    'B': 'byte',
    'C': 'char',
    'D': 'double',
    'F': 'float',
    'I': 'int',
    'J': 'long',
    'S': 'short',
    'Z': 'boolean'
}


class Package:
    def __init__(self, parts):
        self.parts = tuple(parts)
        self.name = '.'.join(self.parts)
        self.path = '/'.join(self.parts) + '/'

    def get_member_path(self, member):
        return self.path + member + '.class'

    def __eq__(self, other):
        return self.parts == other.parts

    def __ne__(self, other):
        return self.parts != other.parts

    def __hash__(self):
        return hash(self.parts)

    def __str__(self):
        return self.name


def parse_name(name, separator='.'):
    parts = name.split(separator)
    return (Package(parts[:-1]), parts[-1])


class LinkableClass:
    def __init__(self, class_info):
        self.package, self.name = parse_name(class_info.get_this(), '/')
        self.full_name = '{}.{}'.format(self.package, self.name)

        self.fields = tuple(LinkableField(f) for f in class_info.fields)

        methods = []
        for m in filter(is_linkable_method, class_info.methods):
            methods.append(LinkableMethod(self.name, m))
        self.methods = tuple(methods)

    def get_member(self, member):
        field = next((f for f in self.fields if member == f.name), None)
        if field:
            return field

        match = re.match(r'^(.+?)(?:\((.*)\))?$', member)
        if match:
            name, args = match.group(1, 2)
            method = next((m for m in self.methods if name == m.name), None)
            if method:
                if args is None:
                    return method

                arglist = [a.strip() for a in args.split(',')]
                if method.has_args(arglist):
                    return method

        return None

    def __str__(self):
        return '{}.{}'.format(self.package.name, self.name)


class LinkableField:
    def __init__(self, field):
        self.name = field.get_name()

    def get_url_fragment(self):
        return self.name

    def __str__(self):
        return self.get_url_fragment()


class LinkableMethod:
    def __init__(self, class_name, method):
        name = method.get_name()
        if name == '<init>':
            self.name = class_name.split('$')[-1]
        else:
            self.name = name

        bin_args = method.pretty_arg_types()
        sig_args = parse_signature_args(method.get_signature())
        self.args = map(Argument, bin_args, sig_args)

    def has_args(self, args):
        if len(args) != len(self.args):
            return False;

        for arg, a in zip(args, self.args):
            if not a.endswith(arg):
                return False

        return True

    def get_url_fragment(self):
        return '{}({})'.format(self.name, ', '.join(map(str, self.args)))

    def __str__(self):
        return self.get_url_fragment()


class Argument:
    def __init__(self, arg, sig=None):
        self.parts = arg.split('.')
        if sig:
            self.sig_parts = sig.split('.')
        else:
            self.sig_parts = None

    def endswith(self, arg):
        arg_parts = arg.split('.')
        if len(arg_parts) > len(self.parts):
            return False

        endswith = self.parts[-len(arg_parts):] == arg_parts
        if not endswith and self.sig_parts:
            endswith = self.sig_parts[-len(arg_parts):] == arg_parts

        return endswith

    def __str__(self):
        if self.sig_parts:
            return '.'.join(self.sig_parts)
        else:
            return '.'.join(self.parts)


def is_linkable_method(method_info):
    return not (method_info.is_bridge() or
                method_info.is_synthetic() or
                method_info.get_name() == '<clinit>')


def parse_signature_args(sig):
    if sig is None:
        return []

    start = sig.find('(')
    if start < 0:
        return []

    args = []
    s = sig[start+1:sig.find(')', start)]
    while s:
        arg, s = _next_arg(s)
        args.append(arg)

    return args


# TODO there's an unimplemented stub in javatools to produce "pretty"
# signatures. When that is implemented, check if it can be used.
def _next_arg(s):
    c = s[0]
    if c in _primitive_types:
        return (_primitive_types[c], s[1:])
    elif c == 'T':
        i = s.find(';')
        return (s[1:i], s[i+1:])
    elif c == 'L':
        name, s = _next_arg_class(s[1:])
        return (name.replace('/', '.'), s)
    elif c == '[':
        t, s = _next_arg(s[1:])
        return ('{}[]'.format(t), s)
    else:
        raise ValueError('unknown arg type: {} in {}'.format(c, s))


def _next_arg_class(s):
    end = name_end = len(s)

    type_arg_count = 0
    for i in range(0, len(s)):
        c = s[i]
        if c == ';':
            name_end = min(i, name_end)
            if type_arg_count == 0:
                end = i + 1
                break
        elif c == '<':
            name_end = min(i, name_end)
            type_arg_count += 1
        elif c == '>':
            type_arg_count -= 1

    return (s[:name_end], s[end:])
