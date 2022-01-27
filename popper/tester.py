from problog.engine import DefaultEngine
from problog.program import PrologString
from problog.logic import Term
from problog import get_evaluatable
from problog.util import init_logger

import re
import os
import sys
import time
from contextlib import contextmanager
# from . constrain import Outcome
from . core import Clause, Literal
from datetime import datetime

class Tester():
    def __init__(self, settings):
        self.settings = settings
        self.engine = DefaultEngine()
        self.data = ":- use_module(library(assert)).\n"
        self.loaded = False
        self.examples = []
        self.eval_timeout = settings.eval_timeout
        self.already_checked_redundant_literals = set()
        init_logger(verbose=0)

    def load_basic(self, head):
        bk_pl_path = self.settings.bk_file
        exs_pl_path = self.settings.ex_file
        test_pl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.pl')
        
        for x in [bk_pl_path, exs_pl_path, test_pl_path]:
          with open(x, 'r') as y:
            self.data += y.read()
            self.data += '\n'
        
        args = ','.join(['_'] * head.arity)
        q1 = f"query({head.predicate}({args}))."
        db = self.engine.prepare(PrologString(self.data + q1))

        lf = self.engine.ground_all(db)
        result = get_evaluatable().create_from(lf).evaluate()

        for i in result.items():
          self.examples.append(i)

        self.loaded = True

    def check_redundant_literal(self, program):
        for clause in program:
            k = Clause.clause_hash(clause)
            if k in self.already_checked_redundant_literals:
                continue
            self.already_checked_redundant_literals.add(k)
            (head, body) = clause
            C = f"[{','.join(('not_'+ Literal.to_code(head),) + tuple(Literal.to_code(lit) for lit in body))}]"
            query = Term(f'redundant_literal({C})')
            db = self.engine.prepare(PrologString(self.data))
            res = self.engine.query(db, query)
            if res:
                yield clause

    def check_redundant_clause(self, program):
        # AC: if the overhead of this call becomes too high, such as when learning programs with lots of clauses, we can improve it by not comparing already compared clauses
        prog = []
        for (head, body) in program:
            C = f"[{','.join(('not_'+ Literal.to_code(head),) + tuple(Literal.to_code(lit) for lit in body))}]"
            prog.append(C)
        prog = f"[{','.join(prog)}]"
        query = Term(f'redundant_clause({prog})')
        db = self.engine.prepare(PrologString(self.data))
        return self.engine.query(db, query)

    def is_non_functional(self, program):
        with self.using(program):
            return list(self.prolog.query(f'non_functional.'))

    def test(self, rules):
      (head, body) = rules[0]

      if not self.loaded:
        self.load_basic(head)

      args = ','.join(['_'] * head.arity)
      h = f":- retractall({head.predicate}({args})).\n"

      for rule in rules:
        code = Clause.to_code(Clause.to_ordered(rule))
        h += f":- assertz(({code})).\n"

      new_data = self.data + h
      db = self.engine.prepare(PrologString(new_data))

      tp = 0
      tn = 0
      fp = 0
      fn = 0

      queries = []

      for e in self.examples:
        q = e[0]
        queries.append(q)

      lf2 = self.engine.ground_all(db, queries=queries)
      res = get_evaluatable().create_from(lf2).evaluate()

      for i in range(0, len(self.examples)):
        pi = self.examples[i][1]
        ni = 1 - pi
        phi = res.get(queries[i])
        nhi = 1 - phi

        tpi = min(pi, phi)
        tni = min(ni, nhi)
        fpi = max(0, ni - tni)
        fni = max(0, pi - tpi)

        tp += tpi
        tn += tni
        fp += fpi
        fn += fni

      return tp, fn, tn, fp

    def is_totally_incomplete(self, rule):
      if not Clause.is_separable(rule):
        return False

      tp, fn, tn, fp = self.test([rule])

      return tp < self.settings.eps

    def is_inconsistent(self, rule):
      if not Clause.is_separable(rule):
        return False
    
      tp, fn, tn, fp = self.test([rule])
    
      return fp > 1 - self.settings.eps
