tracing = False

def push(stack, x):
    stack.append(x)

def top(stack):
    return stack[-1]

def pop(stack):
    return stack.pop()

def nativize(pc, code):
    prefix = []
    lines = []
    temps = [0]
    ds = []

    def gentemp():
        t = 't%d' % temps[0]
        temps[0] += 1
        return t

    def pop():
        if ds:
            return ds.pop()
        t = gentemp()
        prefix.insert(0, '%s = pop(ds)' % t)
        return t

    def push(t):
        ds.append(t)

    def binop(make_expr):
        z, y = pop(), pop()
        t0 = gentemp()
        lines.append('%s = (%s)' % (t0, make_expr(y, z)))
        push(t0)

    def genpush(margin):
        for t in ds:
            lines.append(margin + 'push(ds, %s)' % t)

    while True:
        insn = code[pc]
        pc += 1
        if insn == prim['halt']:
            return None
        elif insn == prim['(:)']:
            return None
        elif insn == prim[';']:
            break
        elif insn == prim['(if)']:
            z = pop()
            # Let's simulate branch-always-taken in this trace tree,
            # for now:
            # XXX return *after* pushing
            lines.append('if %s != 0:' % z)
            genpush('    ')
            lines.append('    return %d' % (pc + 1))
            pc = code[pc]
        elif insn == prim['(literal)']:
            t0 = gentemp()
            lines.append('%s = %d' % (t0, code[pc]))
            push(t0)
            pc += 1
        elif insn == prim['dup']:
            z = pop()
            push(z)
            push(z)
        elif insn == prim['drop']:
            z = pop()
        elif insn == prim['swap']:
            z, y = pop(), pop()
            push(z)
            push(y)
        elif insn == prim['over']:
            z, y = pop(), pop()
            push(y)
            push(z)
            push(y)
        elif insn == prim['rot']:
            z, y, x = pop(), pop(), pop()
            push(y)
            push(z)
            push(x)
        elif insn == prim['+']:
            binop(lambda y, z: '(%s + %s) & wmask' % (y, z))
        elif insn == prim['-']:
            binop(lambda y, z: '(%s - %s) & wmask' % (y, z))
        elif insn == prim['and']:
            binop(lambda y, z: '%s & %s' % (y, z))
        elif insn == prim['or']:
            binop(lambda y, z: '%s | %s' % (y, z))
        elif insn == prim['xor']:
            binop(lambda y, z: '%s ^ %s' % (y, z))
        elif insn == prim['<<']:
            binop(lambda y, z: '(%s << %s) & wmask' % (y, z))
        elif insn == prim['>>']:
            binop(lambda y, z: '(%s >> %s) & wmask' % (y, z))
        elif insn == prim['=']:
            binop(lambda y, z: 'wmask if %s == %s else 0' % (y, z))
        else:
            assert False

    genpush('')
    lines.append('return %d' % pc)
    return prefix + lines

fn_counter = 0

def gen_fn(lines):
    global fn_counter
    name = 'fn%d' % fn_counter
    fn_counter += 1
    code = '\n    '.join(['def %s(ds, rs, data):' % name] + lines)
#    print code
    exec code
    return eval(name)

functiontype = type(gen_fn)


def run(pc, ds, rs, code, data, words):
    # pc = program counter (index into code)
    # ds = data stack
    # rs = return stack
    # code = read-only (but adjustable in size)
    # data = read/write
    # words = dictionary
    tallies = {}
    natives = {}
    while True:
        insn = code[pc]
        trace = '%3d %-10s' % (pc, unprim[insn])
        pc += 1
        if insn == prim['halt']:
            return
        elif insn == prim['(:)']:
            newpc = code[pc]
            native = natives.get(newpc)
            if native:
                if isinstance(native, functiontype):
                    pc = native(ds, rs, data)
                    continue
            else:
                tallies[newpc] = tallies.get(newpc, 0) + 1
                if 4 < tallies[newpc]:
                    native_lines = nativize(newpc, code)
                    if native_lines:
                        fn = gen_fn(native_lines)
                        natives[newpc] = fn
#                        print 'compiled yay'
                        pc = fn(ds, rs, data)
                        continue
            if code[pc+1] != prim[';']: # Is this a nontail call?
                push(rs, pc+1)
            pc = newpc
        elif insn == prim[';']:
            pc = pop(rs)
        elif insn == prim['(if)']:
            if pop(ds) == 0:
                pc = code[pc]
            else:
                pc += 1
        elif insn == prim['(literal)']:
            push(ds, code[pc])
            pc += 1
        elif insn == prim['dup']:
            push(ds, top(ds))
        elif insn == prim['drop']:
            pop(ds)
        elif insn == prim['swap']:
            z, y = pop(ds), pop(ds)
            push(ds, z)
            push(ds, y)
        elif insn == prim['over']:
            push(ds, ds[-2])
        elif insn == prim['rot']:
            z, y, x = pop(ds), pop(ds), pop(ds)
            push(ds, y)
            push(ds, z)
            push(ds, x)
        elif insn == prim['+']:
            z, y = pop(ds), pop(ds)
            push(ds, (y + z) & wmask)
        elif insn == prim['-']:
            z, y = pop(ds), pop(ds)
            push(ds, (y - z) & wmask)
        elif insn == prim['and']:
            z, y = pop(ds), pop(ds)
            push(ds, y & z)
        elif insn == prim['or']:
            z, y = pop(ds), pop(ds)
            push(ds, y | z)
        elif insn == prim['xor']:
            z, y = pop(ds), pop(ds)
            push(ds, y ^ z)
        elif insn == prim['<<']:
            z, y = pop(ds), pop(ds)
            push(ds, (y << z) & wmask)
        elif insn == prim['>>']:
            z, y = pop(ds), pop(ds)
            push(ds, (y >> z) & wmask)
        elif insn == prim['=']:
            z, y = pop(ds), pop(ds)
            push(ds, (-1 & wmask) if z == y else 0)
        else:
            assert False
        trace = '%s %-36s %20s' % (trace,
                                   ' '.join(map(format, ds)),
                                   ' '.join(map(str, rs)))
        if tracing: print trace

wmask = (1 << 32) - 1

def format(n):
    if (n & (1 << 31)) != 0:
        return '%d' % (n - (1<<32))
    return '%d' % n

primitive_names = """
halt (:) ; (if) (literal)
dup drop swap over rot
+ - um* um/mod and or xor << >> >>>
= < u< @ ! code@ code!
fancy
""".split()
prim = dict(zip(primitive_names, range(len(primitive_names))))
unprim = dict(zip(range(len(primitive_names)), primitive_names))

def compile(string, code, data, primwords, words):
    forwards = []
    tokens = iter(string.split())
    for token in tokens:
        if token in primwords:
            code.append(primwords[token])
        elif token in words:
            code.append(prim['(:)'])
            code.append(words[token])
        elif token == ':':
            token = tokens.next()
            words[token] = len(code)
        elif token == 'if':
            code.append(prim['(if)'])
            push(forwards, len(code))
            code.append(0)
        elif token == 'then':
            addr = pop(forwards)
            code[addr] = len(code)
        else:
            number = int(token)
            code.append(prim['(literal)'])
            code.append(number & wmask)
    assert forwards == []

primwords = dict(prim)
words = {}
ds = []
rs = []
code = []
data = []

def comp(string):
    compile(string, code, data, primwords, words)

comp("""
: gcd   over 0 = if  drop ;  then  swap over - gcd ;
: main   8 12 gcd halt
: 2*   dup + ;
: main   5 2* halt
: rfib   dup 0 = if  drop 1 ;  then
         dup 1 = if  drop 1 ;  then
         dup 1 - rfib  swap 2 - rfib  + ;

: 1-  1 - ;

: fibloop   dup 0 = if  drop swap drop ;  then
            1- rot rot  over + swap  rot fibloop ;
: fib   1 1 rot fibloop ;

: main   5 fib halt
""")

run(words['main'], ds, rs, code, data, words)
## ds
#. [5L]

"""
: 2dup   over over ;
: 2*   dup + ;
: nip   swap drop ;
: main   5 2* halt
"""

## print nativize(words['2*'], code)
#. ['t0 = pop(ds)', 't1 = ((t0 + t0) & wmask)', 'push(ds, t1)', 'return 24']
