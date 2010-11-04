% -*- Prolog -*-
% Toy partial evaluator.
% Enter
%    source.
% at the prompt before loading terp.pl (so that clause(G, Antecedent)
% can find the program's clauses).

% G for goal
% R for residual
% SR for simplified residual

peval(G, SR) :-
        pe(G, R),
        simplify(R, SR).

pe((G1, G2), (R1, R2)) :-
        !,
        pe(G1, R1),
        pe(G2, R2).
pe(G, basic(G)) :-
        basic(G), !,
        call(G).
pe(G, R) :-
        clause(G, Antecedent),
        pe(Antecedent, R).

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
