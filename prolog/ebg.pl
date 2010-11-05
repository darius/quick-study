% -*- Prolog -*-
% Explanation-based generalization.
% Enter
%    source.
% at the prompt before loading terp.pl (so that clause(G, Antecedent)
% can find the program's clauses).

% G for goal
% GG for generalized goal
% R for residual
% SR for simplified residual

% A problem:
%   ?- ebg(run([0]), run([N]), R).
% 1
% N = 0,
% R = [write(1),nl]
%
% where we actually want something like
% R = [N=0,write(1),nl]

ebg(G, GG, SR) :-
        eg(G, GG, R),
        simplify(R, SR).

eg((G1, G2), (GG1, GG2), (R1, R2)) :-
        !,
        eg(G1, GG1, R1),
        eg(G2, GG2, R2).
eg(G, GG, basic(GG)) :-
        basic(G), !,
        call(G).
eg(G, GG, R) :-
        clause(GG, GAntecedent),
        % I don't really understand this line:
        copy_term((GG :- GAntecedent), (G :- Antecedent)),
        eg(Antecedent, GAntecedent, R).

basic(G) :-
        predicate_property(G, built_in).

simplify((R1, R2), SR) :-
        simplify(R1, SR1),
        simplify(R2, SR2),
        append(SR1, SR2, SR).
simplify(basic(G), []) :- trivial(G).
simplify(basic(G), [G]) :- \+ trivial(G).

trivial(G) :-
        ground(G),
        pure(G).

pure(true).
pure(_ is _).
pure(_ \= _).

append([], L, L).
append([H|T], L, [H|Z]) :-
        append(T, L, Z).
