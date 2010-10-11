"""
Sequential finite-state transducer language.
Interpreter.
"""

loopy = ["'x [ 'X emit goto 0 ]"]

## run(["'X emit"], '')
#. X
#. 

## run(["'x [ 'hey emit ]"], 'x')
#. hey
#. 
## run(["'x [ 'hey emit ]"], 'y')
            
## run(loopy, 'xxx-')
#. X
#. X
#. X
#. 

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

def run(program, string):
    states = [cmd.split() for cmd in program]
    input = iter(string)
    def next():
        try:
            return input.next()
        except StopIteration:
            return None
    ch = next()
    state = 0
    pc, acc, tokens = 0, '', states[state]
    while pc < len(tokens):
        t = tokens[pc]
        pc += 1
        if t.startswith("'"):
            acc = t[1:]
        elif t == '[':
            if ch and ch in acc:
                ch = next()
            else:
                pc = tokens.index(']', pc) + 1
        elif t == ']':
            pass
        elif t == 'emit':
            print acc
        elif t == 'goto':
            state = int(tokens[pc])
            pc, acc, tokens = 0, '', states[state]
        else:
            assert False, t
