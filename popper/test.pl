%% ========== FUNCTIONAL CHECKS ==========
non_functional:-
    pos(Atom),
    non_functional(Atom),!.

%% ========== REDUNDANCY CHECKS ==========

%subsumes(C,D) :- \+ \+ (copy_term(D,D2), numbervars(D2,0,_), subset(C,D2)).

subset([], _D).
subset([A|B], D):-
    member(A, D),
    subset(B,D).

redundant_literal(C1):-
    select(_,C1,C2),
    subsumes_term(C1,C2),!.

redundant_clause(P1):-
    select(C1,P1,P2),
    member(C2,P2),
    subsumes_term(C1,C2),!.
