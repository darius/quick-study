% -*- Prolog -*-
% Toy partial evaluator.

% G for goal
% R for residual
% SRs for simplified residuals

peval(G, SRs) :-
        pe(G, Rs),
        simplify(Rs, SRs).

pe(G, R) :-
        (basic(G) ->
            call(G),
            R = [G]
        ;
            (G :: Antecedents),
            pe_all(Antecedents, R)).

pe_all([], []).
pe_all([G|Gs], Rs) :-
        pe(G, Rs1),
        pe_all(Gs, Rs2),
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
