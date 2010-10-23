"""
Sequential finite-state transducer language.
Interpreter with single-trace JIT to Python.
This time the tracing code is more clearly separated.
"""

loopy = ["if x [ emit X goto 0 ]"]
branchy = ["if a [ goto 2 ] if b [ goto 1 ] emit neither goto 2",
           "emit one",
           "emit two"]

def show(insns):
    for pc, (fn, args) in enumerate(insns):
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
            
## run(loopy, 'xxxx-')
#. X
#. X
#. def foo(pc, ch, next, recorder):
#.   recorder.reset()
#.   while True:
#.     if not (ch and ch in 'x'): return 3, ch
#.     ch = next()
#.     print 'X'
#. X
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
            def append(fn, *args):
                if live: insns.append((fn, args))
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

def execute(insns, string):
    input = iter(string)
    def next():
        try:
            return input.next()
        except StopIteration:
            return None
    ch = next()
    pc = 0
    recorder = Recorder(insns)
    while pc is not None:
        fn, args = insns[pc]
        pc, ch = fn(pc, ch, next, recorder, *args)

def do_if(pc, ch, next, recorder, charset, target):
    if ch and ch in charset:
        recorder.record(gen_if_true, (charset, target))
        return pc + 1, next()
    else:
        recorder.record(gen_if_false, (charset, pc + 1))
        return target, ch

def gen_if_true(arg):
    yield '  if not (ch and ch in %r): return %r, ch' % arg
    yield '  ch = next()'

def gen_if_false(arg):
    yield '  if ch and ch in %r: return %r, ch' % arg

def do_emit(pc, ch, next, recorder, literal):
    recorder.record(gen_emit, literal)
    print literal
    return pc + 1, ch

def gen_emit(literal):
    yield '  print %r' % literal

def do_goto(pc, ch, next, recorder, target):
    if target < pc:
        recorder.backjump(target)
    return target, ch

def do_halt(pc, ch, next, recorder):
    return None, ch


# Trace recording and compiling.

trace_limit = 50                # We give up on traces that get this long

class Recorder(object):
    def __init__(self, insns):
        self.insns = insns
        self.heads = set()      # pc's starting compiled chunks
        self.reset()
    def reset(self, pc=None):
        self.head = pc     # The pc starting the current trace, if any
        self.trace = []    # A growing list of instructions
    def record(self, gen_fn, arg):
        if self.head is not None:
            if len(self.trace) < trace_limit:
                self.trace.append((gen_fn, arg))
            else:
                self.reset()
    def backjump(self, pc):
        if self.head is None:
            if pc not in self.heads:
                self.reset(pc)  # Start recording a loop
        elif self.head == pc:   # Closed the loop?
            self.insns[pc] = compile(self.trace)
            self.heads.add(pc)
            self.reset()

def compile(trace):
    defn = '\n  '.join(['def foo(pc, ch, next, recorder):']
                       + list(compiling(trace)))
    print defn
    exec defn
    return eval('foo'), ()

def compiling(trace):
    yield 'recorder.reset()'
    yield 'while True:'
    for fn, arg in trace:
        for line in fn(arg):
            yield line
