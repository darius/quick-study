% -*- Prolog -*-
% Prolog meta-interpreter. There are better ones, but this is mine.

:- op(1200, xfx, '::').

interpret(G) :- 
        (basic(G) ->
            call(G)
        ;
            (G :: Antecedents),
            interpret_each(Antecedents)).

interpret_each([]).
interpret_each([G|Gs]) :-
        interpret(G), interpret_each(Gs).

basic(G) :-
        predicate_property(G, built_in).
