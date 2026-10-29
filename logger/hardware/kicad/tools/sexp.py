"""Minimal KiCad s-expression reader/writer."""

def toks(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in '()':
            out.append(c); i += 1
        elif c == '"':
            j = i + 1; b = []
            while True:
                if s[j] == '\\':
                    b.append(s[j:j+2]); j += 2; continue
                if s[j] == '"':
                    break
                b.append(s[j]); j += 1
            out.append('"' + ''.join(b)); i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()"':
                j += 1
            out.append(s[i:j]); i = j
    return out


def parse(t, i=0):
    assert t[i] == '(', t[i]
    node = []; i += 1
    while t[i] != ')':
        if t[i] == '(':
            sub, i = parse(t, i); node.append(sub)
        else:
            node.append(t[i]); i += 1
    return node, i + 1


def read(path):
    return parse(toks(open(path, encoding='utf-8').read()))[0]


def dump(node, indent=0):
    if not isinstance(node, list):
        return node if not node.startswith('"') else '"' + node[1:] + '"'
    pad = '\t' * indent
    head = dump(node[0])
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return pad + '(' + ' '.join(dump(x) for x in node) + ')'
    parts = [pad + '(' + head]
    rest = node[1:]
    lead = []
    while rest and not isinstance(rest[0], list):
        lead.append(dump(rest.pop(0)))
    if lead:
        parts[0] += ' ' + ' '.join(lead)
    for x in rest:
        parts.append(dump(x, indent + 1))
    parts.append(pad + ')')
    return '\n'.join(parts)


def get(node, key):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def getall(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def q(s):
    return ('"' + s.replace('\\', '\\\\').replace('"', '\\"')
            .replace('\n', '\\n'))
