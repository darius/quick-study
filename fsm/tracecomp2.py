"""
Sequential finite-state transducer language.
Interpreter with single-trace JIT to Python.
This time the tracing code is more clearly separated.
"""

loopy = ["if x [ emit X goto 0 ]"]
branchy = ["if a [ goto 2 ] if b [ goto 1 ] emit neither goto 2",
           "emit one",
           "emit two"]

def show(parsed):
    for pc, (fn, args) in enumerate(parsed):
        print '%3d %-8s %s' % (pc, fn.__name__, ', '.join(map(repr, args)))

## show(parse(loopy))
#.   0 do_if    'x', 3
#.   1 do_emit  'X'
#.   2 do_goto  0
#.   3 do_halt  
#. 
## show(parse(branchy))
#.   0 do_if    'a', 2
#.   1 do_goto  8
#.   2 do_if    'b', 4
#.   3 do_goto  6
#.   4 do_emit  'neither'
#.   5 do_goto  8
#.   6 do_emit  'one'
#.   7 do_halt  
#.   8 do_emit  'two'
#.   9 do_halt  
#. 

## run(["emit X"], '')
#. X
#. 
## run(["if x [ emit hey ]"], 'x')
#. hey
#. 
## run(["if x [ emit hey ]"], 'y')
            
## run(loopy, 'xxx-')
#. X
#. X
#. def foo(ch, next):
#.   while True:
#.     if not (ch and ch in 'x'): return 3, ch
#.     ch = next()
#.     print 'X'
#. X
#. 

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

def run(program, string):
    return execute(parse(program), string)

def parse(program):
    targets = {}            # (cmd, tnum) -> pc
    for pass_num in range(2): # (The first pass just fills in targets[])
        insns = []          # Result of the parse
        for cmd in program:
            tokens = cmd.split()
            tnum = 0        # Index into tokens[]
            live = True     # True when the next insn may be reachable
            def append(insn, *args):
                if live: insns.append((insn, args))
            while tnum < len(tokens):
                targets[(cmd, tnum)] = len(insns)
                t = tokens[tnum]
                tnum += 1
                if t == 'if':
                    charset = tokens[tnum]
                    assert tokens[tnum+1] == '['
                    tnum += 2
                    target = targets.get((cmd, tokens.index(']', tnum)))
                    append(do_if, charset, target)
                elif t == ']':
                    live = True
                elif t == 'emit':
                    append(do_emit, tokens[tnum])
                    tnum += 1
                elif t == 'goto':
                    state = int(tokens[tnum])
                    tnum += 1
                    append(do_goto, targets.get((program[state], 0)))
                    live = False
                else:
                    assert False, t
            append(do_halt)
    return insns


# The interpreter. Calls the recorder for all the tracing JIT stuff.

def execute(program, string):
    input = iter(string)
    def next():
        try:
            return input.next()
        except StopIteration:
            return None
    ch = next()
    pc = 0
    recorder = Recorder()
    while pc is not None:
        fn, args = program[pc]
        pc, ch = fn(pc, ch, next, recorder, *args)

def do_if(pc, ch, next, recorder, charset, target):
    if ch and ch in charset:
        recorder.op('[true', (charset, target))
        return pc + 1, next()
    else:
        recorder.op('[false', (charset, pc + 1))
        return target, ch

def do_emit(pc, ch, next, recorder, literal):
    recorder.op('emit', literal)
    print literal
    return pc + 1, ch

def do_goto(pc, ch, next, recorder, target):
    if target < pc:
        recorder.backjump(target)
        fn = recorder.find_code(target)
        if fn:
            recorder.reset()
            return fn(ch, next)
    return target, ch

def do_halt(pc, ch, next, recorder):
    return None, ch


# Trace recording, compiling, and lookup.

trace_limit = 50

class Recorder(object):
    def __init__(self):
        self.code = {}     # pc -> compiled-function
        self.reset()
    def reset(self, pc=None):
        self.head = pc     # The pc starting the current trace, if any
        self.trace = []    # A growing list of instructions
    def find_code(self, pc):
        return self.code.get(pc)
    def op(self, tag, arg):
        if self.head is not None:
            if len(self.trace) < trace_limit:
                self.trace.append((tag, arg))
            else:
                self.reset()
    def backjump(self, pc):
        if self.head is None:
            if pc not in self.code:
                self.reset(pc)
        elif self.head == pc:   # Closed the loop?
            self.code[pc] = compile(self.trace)
            self.reset()

def compile(trace):
    defn = '\n  '.join(['def foo(ch, next):']
                       + list(compiling(trace)))
    print defn
    exec defn
    return eval('foo')

def compiling(trace):
    yield 'while True:'
    for op, arg in trace:
        if op == 'emit':
            yield '  print %r' % arg
        elif op == '[true':
            yield '  if not (ch and ch in %r): return %r, ch' % arg
            yield '  ch = next()'
        elif op == '[false':
            yield '  if ch and ch in %r: return %r, ch' % arg
        else:
            assert False, op
