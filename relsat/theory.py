#!/usr/bin/env python3
# Copyright (C) 2021, Miklos Maroti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import List


class Symbol:
    def __init__(self, name: str, arity: int):
        """
        A relational symbol with the given name and arity.
        """
        assert arity >= 0
        self.name = name
        self.arity = arity

    def __str__(self):
        return self.name + "(" + \
            ",".join("x" + str(var) for var in range(self.arity)) + ")"


class Literal:
    def __init__(self, univs: int, sign: bool, symbol: 'Symbol', vars: List[int]):
        """
        A literal in a universally classified clause with univs many free variables.
        The list of vars specify the mapping of coordinates of the relation to the
        set of free variables. The sign is true if this is a positive literal.
        """
        assert univs >= 0 and len(vars) == symbol.arity
        assert all(0 <= var < univs for var in vars)
        self.univs = univs
        self.symbol = symbol
        self.sign = sign
        self.vars = vars

    def __str__(self):
        return ("+" if self.sign else "-") + str(self.symbol.name) + \
            "(" + ",".join("x" + str(var) for var in self.vars) + ")"


class Clause:
    def __init__(self, literals: List['Literal']):
        assert literals
        self.univs = literals[0].univs
        assert all(lit.univs == self.univs for lit in literals[1:])
        self.literals = literals

    def __str__(self):
        return ", ".join(str(lit) for lit in self.literals)


class Theory:
    """
    Relational signature and corresponding universal theory.
    """

    def __init__(self, symbols: List['Symbol'], clauses: List['Clause']):
        self.symbols = symbols
        self.clauses = clauses

    def print(self):
        print("symbols: " + ", ".join(str(sym) for sym in self.symbols))
        print("clauses:")
        for cla in self.clauses:
            print(cla)
