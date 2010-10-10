from itertools import chain

def codegen(tt):
    print 'while True:'
    for line in indent(tt.emit()):
        print line

def indent(lines):
    return ('    ' + line for line in lines)

class TraceTree:
    """Represents a set of traces all starting from the same
    header. Adds in traces incrementally. Generates code embodying
    them all."""
    def emit(self):
        abstract

class Promise(TraceTree):
    def __init__(self, pc):
        self.pc = pc
        self.tt = None
        self.emitting = False
    def emit(self):
        if self.emitting:
            return ('continue',)
        else:
            self.emitting = True
            try:
                return (self.tt or Exit(self.pc)).emit()
            finally:
                self.emitting = False
    def resolve(self, make_tt):
        if self.tt is None:
            self.tt = make_tt()
        return self.tt
    def __repr__(self):
        return 'Promise()' if self.tt is None else repr(self.tt)

class Exit(TraceTree):
    def __init__(self, opt_pc):
        self.opt_pc = opt_pc
    def emit(self):
        yield 'return %r' % self.opt_pc
    def __repr__(self):
        return 'Exit(%r)' % (self.opt_pc)

class Trunk(TraceTree):
    def __init__(self, insn, next):
        self.insn = insn
        self.next = next
    def emit(self):
        return chain(self.insn.emit(), self.next.emit())
    def __repr__(self):
        return 'Trunk(%r, %r)' % (self.insn, self.next)

class Branch(TraceTree):
    def __init__(self, insn, on_true, on_false):
        self.insn = insn
        self.on_true = on_true
        self.on_false = on_false
    def emit(self):
        return self.insn.emit(self.on_true.emit(), self.on_false.emit())
    def __repr__(self):
        return 'Branch(%r, %r, %r)' % (self.insn, self.on_true, self.on_false)
        

## tt = Trunk(eg[0], Branch(eg[1], Trunk(eg[2], Exit(3)), Trunk(eg[4], Exit(5))))
## codegen(tt)
#. while True:
#.     print 1
#.     if input.next() in 'ab':
#.         print 2
#.         return 3
#.     else:
#.         print 3
#.         return 5
#. 


def run(code, decisions, header):
    promise = header
    input = iter(decisions)
    while promise is not None:
        promise = code[promise.pc].run(promise.pc, input, promise, header)

class Insn:
    def run(self, pc, input, promise):
        abstract
    def emit(self, *lineses):
        abstract

class Halt(Insn):
    def run(self, pc, input, promise, header):
        promise.resolve(lambda: Exit(None))
        return None

class Print(Insn):
    def __init__(self, literal):
        self.literal = literal
    def run(self, pc, input, promise, header):
        print self.literal
        tt = promise.resolve(lambda: Trunk(self, Promise(pc + 1)))
        return tt.next
    def emit(self):
        yield 'print %r' % self.literal
    def __repr__(self):
        return 'Print(%r)' % (self.literal)

class Jump(Insn):
    def __init__(self, offset):
        self.offset = offset
    def run(self, pc, input, promise, header):
        pc += self.offset
        tt = promise.resolve(lambda: header if pc == header.pc else Promise(pc))
        return tt
    def emit(self):
        assert False
    def __repr__(self):
        return 'Jump(%r)' % self.offset

class If(Insn):
    def __init__(self, chars, offset):
        self.chars = chars
        self.offset = offset
    def run(self, pc, input, promise, header):
        tt = promise.resolve(lambda: Branch(self,
                                            Promise(pc + 1),
                                            Promise(pc + 1 + self.offset)))
        return tt.on_true if input.next() in self.chars else tt.on_false
    def emit(self, on_true_lines, on_false_lines):
        return chain(('if input.next() in %r:' % self.chars,),
                     indent(on_true_lines),
                     ('else:',),
                     indent(on_false_lines))
    def __repr__(self):
        return 'If(%r)' % self.offset

loopy = [If('x', 2), Print('X'), Jump(-2), Halt()]

## hl = Promise(0)
## run(loopy, 'xxyz', hl)
#. X
#. X
#. 
## codegen(hl)
#. while True:
#.     if input.next() in 'x':
#.         print 'X'
#.         continue
#.     else:
#.         return None
#. 


eg = [Print(1), If('ab', 2), Print(2), Halt(), Print(3), Halt()]

## header = Promise(0)
## run(eg, 'X', header)
#. 1
#. 3
#. 
## codegen(header)
#. while True:
#.     print 1
#.     if input.next() in 'ab':
#.         return 2
#.     else:
#.         print 3
#.         return None
#. 
## run(eg, 'a', header)
#. 1
#. 2
#. 
## codegen(header)
#. while True:
#.     print 1
#.     if input.next() in 'ab':
#.         print 2
#.         return None
#.     else:
#.         print 3
#.         return None
#. 

trivial = [Halt()]
## header = Promise(0)
## run(trivial, '', header)
## codegen(header)
#. while True:
#.     return None
#. 

linear = [Print(42), Halt()]
## header = Promise(0)
## run(linear, '', header)
#. 42
#. 
## codegen(header)
#. while True:
#.     print 42
#.     return None
#. 
