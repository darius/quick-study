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
#. def compiled_loop(pc, ch, get_ch, recorder):
#.   recorder.reset()
#.   while True:
#.     if not (ch and ch in 'x'): return 3, ch
#.     ch = get_ch()
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
    targets = {}            # (state, tnum) -> pc
    for pass_num in range(2): # (The first pass just fills in targets[])
        insns = []
        for state, cmd in enumerate(program):
            parse_cmd(insns, targets, state, cmd.split())
    return insns

def parse_cmd(insns, targets, state, tokens):
    "Add to insns and targets by parsing tokens (for the given state)."
    live = True             # True when the next insn may be reachable
    def append(fn, *args):
        if live: insns.append((fn, args))
    enum = enumerate(tokens)
    for tnum, t in enum:
        targets[(state, tnum)] = len(insns)
        if t == 'emit':
            tnum, literal = enum.next()
            append(do_emit, literal)
        elif t == 'goto':
            tnum, dest_state = enum.next()
            append(do_goto, targets.get((int(dest_state), 0)))
            live = False
        elif t == 'if':
            tnum, charset = enum.next()
            tnum, _ = enum.next()
            assert _ == '['
            target = targets.get((state, tokens.index(']', tnum)))
            append(do_if, charset, target)
        elif t == ']':
            live = True
        else:
            assert False, t
    append(do_halt)


# The interpreter. Calls the recorder for all the tracing JIT stuff.

def execute(insns, string):
    input = iter(string)
    def get_ch():
        return next(input, None)
    ch = get_ch()
    pc = 0
    recorder = Recorder(insns)
    while pc is not None:
        fn, args = insns[pc]
        pc, ch = fn(pc, ch, get_ch, recorder, *args)

def do_halt(pc, ch, get_ch, recorder):
    return None, ch

def do_emit(pc, ch, get_ch, recorder, literal):
    recorder.record(gen_emit, literal)
    print literal
    return pc + 1, ch

def gen_emit(literal):
    yield 'print %r' % literal

def do_goto(pc, ch, get_ch, recorder, target):
    if target < pc:
        recorder.backjump(target)
    return target, ch

def do_if(pc, ch, get_ch, recorder, charset, target):
    if ch and ch in charset:
        recorder.record(gen_if_true, (charset, target))
        return pc + 1, get_ch()
    else:
        recorder.record(gen_if_false, (charset, pc + 1))
        return target, ch

def gen_if_true(arg):
    yield 'if not (ch and ch in %r): return %r, ch' % arg
    yield 'ch = get_ch()'

def gen_if_false(arg):
    yield 'if ch and ch in %r: return %r, ch' % arg


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
    defn = '\n  '.join(compiling(trace))
    print defn
    exec defn
    return eval('compiled_loop'), ()

def compiling(trace):
    yield 'def compiled_loop(pc, ch, get_ch, recorder):'
    yield 'recorder.reset()'
    yield 'while True:'
    for fn, arg in trace:
        for line in fn(arg):
            yield '  ' + line
