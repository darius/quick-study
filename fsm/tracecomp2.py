"""
Sequential finite-state transducer language.
Interpreter with single-trace JIT to Python.
This time the tracing code is more clearly separated.
"""

loopy = ["if x [ emit X goto 0 ]"]
branchy = ["if a [ goto 2 ] if b [ goto 1 ] emit neither goto 2",
           "emit one",
           "emit two"]

## for pc, insn in enumerate(parse(loopy)): print pc, insn
#. 0 If(charset='x',target=3)
#. 1 Emit(literal='X')
#. 2 Goto(target=0)
#. 3 Halt()
#. 
## for pc, insn in enumerate(parse(branchy)): print pc, insn
#. 0 If(charset='a',target=2)
#. 1 Goto(target=8)
#. 2 If(charset='b',target=4)
#. 3 Goto(target=6)
#. 4 Emit(literal='neither')
#. 5 Goto(target=8)
#. 6 Emit(literal='one')
#. 7 Halt()
#. 8 Emit(literal='two')
#. 9 Halt()
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
            def append(insn):
                if live: insns.append(insn)
            while tnum < len(tokens):
                targets[(cmd, tnum)] = len(insns)
                t = tokens[tnum]
                tnum += 1
                if t == 'if':
                    charset = tokens[tnum]
                    assert tokens[tnum+1] == '['
                    tnum += 2
                    target = targets.get((cmd, tokens.index(']', tnum)))
                    append(If(charset, target))
                elif t == ']':
                    live = True
                elif t == 'emit':
                    append(Emit(tokens[tnum]))
                    tnum += 1
                elif t == 'goto':
                    state = int(tokens[tnum])
                    tnum += 1
                    append(Goto(targets.get((program[state], 0))))
                    live = False
                else:
                    assert False, t
            append(Halt())
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
        pc, ch = program[pc].step(pc, ch, next, recorder)

class Insn(object):
    def __repr__(self):
        args = ','.join('%s=%r' % x for x in self.__dict__.items())
        return '%s(%s)' % (self.__class__.__name__, args)

class If(Insn):
    def __init__(self, charset, target):
        self.charset = charset
        self.target = target
    def step(self, pc, ch, next, recorder):
        if ch and ch in self.charset:
            recorder.op('[true', (self.charset, self.target))
            return pc + 1, next()
        else:
            recorder.op('[false', (self.charset, pc + 1))
            return self.target, ch

class Emit(Insn):
    def __init__(self, literal):
        self.literal = literal
    def step(self, pc, ch, next, recorder):
        recorder.op('emit', self.literal)
        print self.literal
        return pc + 1, ch

class Goto(Insn):
    def __init__(self, target):
        self.target = target
    def step(self, pc, ch, next, recorder):
        if self.target < pc:
            recorder.backjump(self.target)
        fn = recorder.find_code(self.target)
        return fn(ch, next) if fn else (self.target, ch)

class Halt(Insn):
    def step(self, pc, ch, next, recorder):
        return None, ch


# Trace recording, compiling, and lookup.

trace_limit = 50

class Recorder(object):
    def __init__(self):
        self.code = {}     # pc -> compiled-function
        self._reset()
    def _reset(self, pc=None):
        self.head = pc     # The pc starting the current trace, if any
        self.trace = []    # A growing list of instructions
    def find_code(self, pc):
        return self.code.get(pc)
    def op(self, tag, arg):
        if self.head is not None:
            if len(self.trace) < trace_limit:
                self.trace.append((tag, arg))
            else:
                self._reset()
    def backjump(self, pc):
        if self.head is None:
            if pc not in self.code:
                self._reset(pc)
        elif self.head == pc:   # Closed the loop?
            self.code[pc] = compile(self.trace)
            self._reset()

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
