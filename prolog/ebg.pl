% -*- Prolog -*-
% Explanation-based generalization.

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

eg(G, GG, R) :-
        (basic(G) ->
            call(G),
            R = [G]
        ;
            (G :: Antecedents),
            copy_term((GG :: GAntecedents), (G :: Antecedents)),
            eg_all(Antecedents, GAntecedents, R)).

eg_all([], [], []).
eg_all([G|Gs], [GG|GGs], Rs) :-
        eg(G, GG, Rs1),
        eg_all(Gs, GGs, Rs2),
        append(Rs1, Rs2, Rs).

basic(G) :-
        predicate_property(G, built_in).

simplify([], []).
simplify([R|Rs], SRs) :-
        (trivial(R) ->
            simplify(Rs, SRs)
        ;
            simplify(Rs, SRs1),
            SRs = [R|SRs1]).

trivial(G) :-
        ground(G),
        pure(G).

pure(true).
pure(_ is _).
pure(_ \= _).

append([], L, L).
append([H|T], L, [H|Z]) :-
        append(T, L, Z).
