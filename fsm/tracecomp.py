"""
Sequential finite-state transducer language.
Interpreter with single-trace JIT to Python.
"""

loopy = ["'x [ 'X emit goto 0 ]"]

## run(["'X emit"], '')
#. X
#. 

## run(["'x [ 'hey emit ]"], 'x')
#. hey
#. 
## run(["'x [ 'hey emit ]"], 'y')
            
## traces = running(loopy, 'xxx-')
#. X
#. X
#. def foo(ch, get_ch):
#.   while True:
#.     if not (ch and ch in 'x'): return ch, 'x', (0, 7)
#.     ch = get_ch()
#.     print 'X'
#. X
#. 0 <function foo at 0x7f556f46f938>
#. 
### compile(traces[0])

def compile(trace):
    defn = '\n  '.join(['def foo(ch, get_ch):'] + list(compiling(trace)))
    print defn
    exec defn
    return eval('foo')

def compiling(trace):
    yield 'while True:'
    acc = ''
    for op, arg in trace:
        if op == "'":
            acc = arg
        elif op == 'emit':
            yield '  print %r' % acc
        elif op == '[true':
            yield '  if not (ch and ch in %r): return ch, %r, %r' % (acc, acc, arg)
            yield '  ch = get_ch()'
        elif op == '[false':
            yield '  if ch and ch in %r: return ch, %r, %r' % (acc, acc, arg)
        else:
            assert False, op

branchy = ["'a [ goto 2 ] 'b [ goto 1 ] 'neither emit goto 2",
           "'one emit",
           "'two emit"]

## run(branchy, 'a')
#. two
#. 
## run(branchy, 'b')
#. one
#. 
## run(branchy, 'c')
#. neither
#. two
#. 
## run(branchy, '')
#. neither
#. two
#. 

trace_limit = 50

def run(program, string):
    running(program, string)

def running(program, string):
    states = [cmd.split() for cmd in program]

    input = iter(string)
    def get_ch():
        return next(input, None)
    ch = get_ch()

    traces = {}                 # state_number -> compiled-function
    current_trace = []          # [state_number, insn, insn, ...]
    def append(op, arg=()):
        if current_trace:
            if len(current_trace) < trace_limit:
                current_trace.append((op, arg))
            else:
                del current_trace[:]

    state = 0
    pc, acc, tokens = 0, '', states[state]
    while pc < len(tokens):
        t = tokens[pc]
        pc += 1

        if t.startswith("'"):
            acc = t[1:]
            append("'", acc)
        elif t == '[':
            skip = tokens.index(']', pc) + 1
            if ch and ch in acc:
                append('[true', (state, skip))
                ch = get_ch()
            else:
                append('[false', (state, pc))
                pc = skip
        elif t == ']':
            pass
        elif t == 'emit':
            append(t)
            print acc
        elif t == 'goto':
            target = int(tokens[pc])
            if target <= state: # Backward jump?
                if not current_trace:
                    if target not in traces:
                        current_trace = [target]
                elif target == current_trace[0]: # Closed the loop?
                    traces[target] = compile(current_trace[1:])
                    del current_trace[:]
            if True and target in traces:
                ch, acc, (state, pc) = traces[target](ch, get_ch)
                tokens = states[state]
            else:
                state = target
                pc, acc, tokens = 0, '', states[state]
        else:
            assert False, t

    for header, trace in traces.items():
        print header, trace
    return traces
