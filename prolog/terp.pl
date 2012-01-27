% -*- Prolog -*-
% Toy interpreter for a Forth-like virtual machine.
% The code is to be meta-intepreted: instead of
%    foo :- bar, baz.
% we write
%    foo :: [bar, baz].

:- op(1200, xfx, '::').

% S is the initial stack. Any output is by side effects.
run(S)           :: [run(0, S)].
run(PC, S)       :: [insn(PC, Insn), run(PC, S, Insn)].
run(PC, S, halt) :: [].
run(PC, S, Insn) :: [step(Insn, PC, S, PC1, S1), run(PC1, S1)].

step(jump(Target), PC, S, Target, S)    :: [].
step(branch(Target), PC, [0|S], Target, S) :: [].
step(branch(Target), PC, [Z|S], PC1, S) :: [Z \= 0, PC1 is PC+1].
step(Insn, PC, S, PC1, S1)              :: [operate(Insn, S, S1), PC1 is PC+1].

operate(push(Lit), S, [Lit|S])      :: [].
operate(over, [Z,Y|S], [Y,Z,Y|S])   :: [].
operate(rot,  [Z,Y,X|S], [X,Z,Y|S]) :: [].
operate(add,  [Z,Y|S], [R|S])       :: [R is Y+Z].
operate(sub,  [Z,Y|S], [R|S])       :: [R is Y-Z].
operate(mul,  [Z,Y|S], [R|S])       :: [R is Y*Z].
operate(eq,   [Z,Z|S], [1|S])       :: [].
operate(eq,   [Z,Y|S], [0|S])       :: [Y \= Z].
operate(write, [H|S], S)            :: [write(H), nl].

% The VM-code program: compute n factorial.
                           % Stack picture
insn( 0, push(1))   :: []. % n 1
insn( 1, over)      :: []. % n p n        (top of loop)
insn( 2, push(0))   :: []. % n p n 0
insn( 3, eq)        :: [].
insn( 4, branch(7)) :: [].
insn( 5, write)     :: [].
insn( 6, halt)      :: [].
insn( 7, over)      :: []. % n p n        (target of branch)
insn( 8, push(1))   :: [].
insn( 9, sub)       :: []. % n p n-1
insn(10, rot)       :: [].
insn(11, rot)       :: []. % n-1 n p
insn(12, mul)       :: []. % n-1 n*p
insn(13, jump(1))   :: [].
