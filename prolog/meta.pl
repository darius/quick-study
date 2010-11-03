% -*- Prolog -*-
% Prolog meta-interpreter. There are better ones, but this is mine.
% Just good enough to run terp.pl if you enter
%    source.
% at the prompt before loading terp.pl (so that clause(G, Antecedent)
% can find the program's clauses).

meta(true).
meta((G1, G2)) :- meta(G1), meta(G2).
meta(G) :- basic(G), call(G).
meta(G) :- \+ (basic(G); G = (_,_)), clause(G, Antecedent), meta(Antecedent).

basic(_ is _).
basic(_ =\= _).
basic(write(_)).
basic(nl).
