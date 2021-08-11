import operator
from collections import defaultdict
from . core import ConstVar, ConstOpt, Literal, Clause

class Outcome:
    ALL = 'all'
    SOME = 'some'
    NONE = 'none'

class Con:
    GENERALISATION = 'generalisation'
    SPECIALISATION = 'specialisation'
    REDUNDANCY = 'redundancy'
    BANISH = 'banish'

OUTCOME_TO_CONSTRAINTS = {
    (Outcome.ALL, Outcome.NONE)  : (Con.BANISH,),
    (Outcome.ALL, Outcome.SOME)  : (Con.GENERALISATION,),
    (Outcome.SOME, Outcome.NONE) : (Con.SPECIALISATION,),
    (Outcome.SOME, Outcome.SOME) : (Con.SPECIALISATION, Con.GENERALISATION),
    (Outcome.NONE, Outcome.NONE) : (Con.SPECIALISATION, Con.REDUNDANCY),
    (Outcome.NONE, Outcome.SOME) : (Con.SPECIALISATION, Con.REDUNDANCY, Con.GENERALISATION)
}

def alldiff(vars):
    return ConstOpt(None, vars, 'AllDifferent')

def lt(a, b):
    return ConstOpt(operator.lt, (a, b), '<')

def eq(a, b):
    return ConstOpt(operator.eq, (a, b), '==')

def gteq(a, b):
    return ConstOpt(operator.ge, (a, b), '>=')

def vo_clause(variable):
    return ConstVar(f'C{variable}', 'Clause')

def vo_variable(variable):
    return ConstVar(f'{variable}', 'Variable')

# restrict a clause id to have a specific body size
def body_size_literal(clause_var, body_size):
    return Literal('body_size', (clause_var, body_size))

class Constrain:
    def __init__(self, experiment):
        self.seen_clause_handle = {}
        self.added_clauses = set()

    @staticmethod
    def decide_outcome(tp, fn, tn, fp):
        # complete
        if fn == 0:
            positive_outcome = Outcome.ALL
        # totally incomplete
        elif tp == 0 and fn > 0: # AC: we must use TP==0 rather than FN=|E+| because of minimal testing
            positive_outcome = Outcome.NONE
        # incomplete
        else:
            positive_outcome = Outcome.SOME

        # consistent
        if fp == 0:
            negative_outcome = Outcome.NONE
        # totally inconsistent
        # AC: this line may not work with minimal testing
        # elif FP == self.num_neg:
            # negative_outcome = Outcome.ALL
        # inconsistent
        else:
            negative_outcome = Outcome.SOME

        return (positive_outcome, negative_outcome)

    def build_constraints(self, program, before, min_clause, outcome):
        (positive_outcome, negative_outcome) = outcome
        # RM: If you don't use these two lines you need another three entries in the OUTCOME_TO_CONSTRAINTS table (one for every positive outcome combined with negative outcome ALL).
        if negative_outcome == Outcome.ALL:
             negative_outcome = Outcome.SOME
        for constraint_type in OUTCOME_TO_CONSTRAINTS[(positive_outcome, negative_outcome)]:
            if constraint_type == Con.GENERALISATION:
                yield from self.generalisation_constraint(program, before, min_clause)
            elif constraint_type == Con.SPECIALISATION:
                yield from self.specialisation_constraint(program, before, min_clause)
            elif constraint_type == Con.REDUNDANCY:
                yield from self.redundancy_constraint(program, before, min_clause)
            elif constraint_type == Con.BANISH:
                yield from self.banish_constraint(program, before, min_clause)

    def make_literal_handle(self, literal):
        return f'{literal.predicate}{"".join(literal.arguments)}'

    def make_clause_handle(self, clause):
        if clause in self.seen_clause_handle:
            return self.seen_clause_handle[clause]
        (head, body) = clause
        body_literals = sorted(body, key = operator.attrgetter('predicate'))
        clause_handle = ''.join(self.make_literal_handle(literal) for literal in [head] + body_literals)
        self.seen_clause_handle[clause] = clause_handle
        return clause_handle

    def make_clause_inclusion_rule(self, clause, min_num, clause_handle):
        if clause_handle in self.added_clauses:
            return
            yield

        (head, body) = clause

        self.added_clauses.add(clause_handle)
        clause_number = vo_clause('l')

        literals = []
        literals.append(Literal('head_literal', (clause_number, head.predicate, head.arity, tuple(vo_variable(v) for v in head.arguments))))

        for body_literal in body:
            literals.append(Literal('body_literal', (clause_number, body_literal.predicate, body_literal.arity, tuple(vo_variable(v) for v in body_literal.arguments))))

        literals.append(gteq(clause_number, min_num))

        # ensure that each var_var is ground to a unique value
        literals.append(alldiff(tuple(vo_variable(v) for v in Clause.all_vars(clause))))

        for idx, var in enumerate(head.arguments):
            literals.append(eq(vo_variable(var), idx))

        yield (Literal('included_clause', (clause_handle, clause_number)), tuple(literals))

    def banish_constraint(self, program, before, min_clause):
        literals = []
        for clause_number, clause in enumerate(program):
            (head, body) = clause
            clause_handle = self.make_clause_handle(clause)
            yield from self.make_clause_inclusion_rule(clause, min_clause[clause_number], clause_handle)

            literals.append(Literal('included_clause', (clause_handle, vo_clause(clause_number))))
            literals.append(body_size_literal(vo_clause(clause_number), len(body)))

        for clause_number1, clause_numbers in before.items():
            for clause_number2 in clause_numbers:
                literals.append(lt(vo_clause(clause_number1), vo_clause(clause_number2)))

        for clause_number, clause in enumerate(program):
            literals.append(gteq(vo_clause(clause_number), min_clause[clause]))


        num_clauses = len(program)
        # ensure that each clause_var is ground to a unique value
        literals.append(alldiff(tuple(vo_clause(c) for c in range(num_clauses))))
        literals.append(Literal('clause', (num_clauses, ), positive = False))

        yield (None, tuple(literals))

    def generalisation_constraint(self, program, before, min_clause):
        literals = []
        for clause_number, clause in enumerate(program):
            (_head, body) = clause
            clause_handle = self.make_clause_handle(clause)
            yield from self.make_clause_inclusion_rule(clause,  min_clause[clause], clause_handle)

            literals.append(Literal('included_clause', (clause_handle, vo_clause(clause_number))))
            literals.append(body_size_literal(vo_clause(clause_number), len(body)))

        for clause_number1, clause_numbers in before.items():
            for clause_number2 in clause_numbers:
                literals.append(lt(vo_clause(clause_number1), vo_clause(clause_number2)))

        for clause_number, clause in enumerate(program):
            literals.append(gteq(vo_clause(clause_number), min_clause[clause]))

        # ensure that each clause_var is ground to a unique value
        literals.append(alldiff(tuple(vo_clause(c) for c in range(len(program)))))

        yield (None, tuple(literals))

    def specialisation_constraint(self, program, before, min_clause):
        literals = []

        for clause_number, clause in enumerate(program):
            clause_handle = self.make_clause_handle(clause)
            yield from self.make_clause_inclusion_rule(clause, min_clause[clause], clause_handle)
            clause_variable = vo_clause(clause_number)
            literals.append(Literal('included_clause', (clause_handle, clause_variable)))

        for clause_number1, clause_numbers in before.items():
            for clause_number2 in clause_numbers:
                literals.append(lt(vo_clause(clause_number1), vo_clause(clause_number2)))

        num_clauses = len(program)
        # ensure that each clause_var is ground to a unique value
        literals.append(alldiff(tuple(vo_clause(c) for c in range(num_clauses))))

        literals.append(Literal('clause', (num_clauses, ), positive = False))

        yield (None, tuple(literals))

    # AC: THIS CONSTRAINT DUPLICATES THE GENERALISATION CONSTRAINT AND NEEDS REFACTORING
    def redundant_literal_constraint(self, clause, before, min_clause):
        (_head, body) = clause
        clause_handle = self.make_clause_handle(clause)
        yield from self.make_clause_inclusion_rule(clause, min_clause[clause], clause_handle)
        literals = []
        clause_variable = vo_clause(0)
        literals.append(Literal('included_clause', (clause_handle, clause_variable)))
        literals.append(body_size_literal(clause_variable, len(body)))
        yield (None, tuple(literals))

    # Jk: AC, I cleaned this up a bit, but this reorg is for you. Godspeed!
    # AC: @JK, I made another pass through it. It was tough. I will try again once we have the whole codebase tidied.
    def redundancy_constraint(self, program, before, min_clause):
        lits_num_clauses = defaultdict(int)
        lits_num_recursive_clauses = defaultdict(int)
        for clause in program:
            (head, _) = clause
            lits_num_clauses[head.predicate] += 1
            if Clause.is_recursive(clause):
                lits_num_recursive_clauses[head.predicate] += 1

        recursively_called = set()
        while True:
            something_added = False
            for clause in program:
                (head, body) = clause
                is_rec = Clause.is_recursive(clause)
                for body_literal in body:
                    if body_literal.predicate not in lits_num_clauses:
                        continue
                    if (body_literal.predicate != head.predicate and is_rec) or (head.predicate in recursively_called):
                        something_added |= not body_literal.predicate in recursively_called
                        recursively_called.add(body_literal.predicate)
            if not something_added:
                break

        for lit in lits_num_clauses.keys() - recursively_called:
            literals = []

            for clause_number, clause in enumerate(program):
                clause_handle = self.make_clause_handle(clause)
                yield from self.make_clause_inclusion_rule(clause, min_clause[clause], clause_handle)
                clause_variable = vo_clause(clause_number)
                literals.append(Literal('included_clause', (clause_handle, clause_variable)))

            for clause_number1, clause_numbers in before.items():
                for clause_number2 in clause_numbers:
                    literals.append(lt(vo_clause(clause_number1), vo_clause(clause_number2)))

            # ensure that each clause_var is ground to a unique value
            literals.append(alldiff(tuple(vo_clause(c) for c in range(len(program)))))

            for other_lit, num_clauses in lits_num_clauses.items():
                if other_lit == lit:
                    continue
                literals.append(Literal('num_clauses', (other_lit, num_clauses)))
            num_recursive = lits_num_recursive_clauses[lit]

            literals.append(Literal('num_recursive', (lit, num_recursive)))

            yield (None, tuple(literals))

    @staticmethod
    def print_constraint(con):
        (head, body) = con
        constraint_literals = []
        for constobj in body:
            if isinstance(constobj, Literal):
                constraint_literals.append(str(constobj))
            elif isinstance(constobj, ConstOpt):
                if constobj.operation == 'AllDifferent':
                    # print(f'ALLDIFF:{constobj.arguments}')
                    # AC: TODO!!!
                    continue
                arga, argb = constobj.arguments
                if isinstance(arga, ConstVar):
                    arga = arga.name
                else:
                    arga = str(arga)
                if isinstance(argb, ConstVar):
                    argb = argb.name
                else:
                    argb = str(argb)
                constraint_literals.append(f'{arga}{constobj.operation}{argb}')

        x = f':- {", ".join(constraint_literals)}.'
        if head:
            x = f'{head} {x}'
        print(x)

