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
import numpy


class Symbol:
    def __init__(self, name: str, arity: int):
        """
        A relational symbol with the given name and arity.
        """
        assert arity >= 0
        self.name = name
        self.arity = arity
        self.table = None

    def __str__(self):
        return self.name + "(" + \
            ",".join("x" + str(var) for var in range(self.arity)) + ")"

    def create_table(self, size: int):
        assert size >= 1
        shape = [size for _ in range(self.arity)]
        self.table = numpy.zeros(shape=shape, dtype=numpy.int8)

    def print_table(self):
        print(self.table.flatten())

    def get_value(self, coords: List[int]) -> int:
        assert len(coords) == self.arity
        return self.table[tuple(coords)]

    def set_value(self, coords: List[int], value: int):
        assert len(coords) == self.arity
        self.table[tuple(coords)] = value


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
        self.table = None

    def __str__(self):
        return ("+" if self.sign else "-") + str(self.symbol.name) + \
            "(" + ",".join("x" + str(var) for var in self.vars) + ")"

    def create_table(self):
        """
        Creates a view into the underlying symbol table with properly
        permuted axes, repeated axes diagonalized and unused axes set
        to the broadcasting dimension of 1.
        """
        table = self.symbol.table

        # remove repeated axes
        vars = []
        for var in self.vars:
            if var in vars:
                idx = vars.index(var)
                table = table.diagonal(axis1=idx, axis2=len(vars)).swapaxes(idx, -1)
            else:
                vars.append(var)
        assert len(vars) == len(table.shape)

        # add broadcasting axes
        shape = list(table.shape)
        shape.extend(1 for _ in range(self.univs - len(vars)))
        table = table.reshape(shape)

        # permute axes
        unused = len(vars)
        axes = []
        for var in range(self.univs):
            if var in vars:
                axes.append(vars.index(var))
            else:
                axes.append(unused)
                unused += 1
        assert unused == self.univs
        self.table = table.transpose(axes)

        # make sure that we have a view to the original data
        assert self.table.dtype == numpy.int8
        assert self.table.base is self.symbol.table

    def get_table(self):
        return self.table if self.sign else -self.table

    def get_value(self, coords: List[int]) -> int:
        assert len(coords) == self.univs
        coords = [coords[var] for var in self.vars]
        value = self.symbol.get_value(coords)
        return value if self.sign else -value

    def set_value(self, coords: List[int], value: int):
        assert len(coords) == self.univs
        coords = [coords[var] for var in self.vars]
        self.symbol.set_value(coords, value if self.sign else -value)


class Clause:
    def __init__(self, literals: List['Literal']):
        assert literals
        self.univs = literals[0].univs
        assert all(lit.univs == self.univs for lit in literals[1:])
        self.literals = literals

    def __str__(self):
        return ", ".join(str(lit) for lit in self.literals)

    def create_tables(self):
        for lit in self.literals:
            lit.create_table()

    def get_table(self):
        table = self.literals[0].get_table()
        for lit in self.literals[1:]:
            table = numpy.maximum(table, lit.get_table())

        assert table.dtype == numpy.int8
        return table


class Theory:
    """
    Relational signature and corresponding universal theory.
    """

    def __init__(self, symbols: List['Symbol'], clauses: List['Clause']):
        self.symbols = symbols
        self.clauses = clauses
        self.size = None

    def print(self):
        print("size: " + str(self.size))
        print("symbols: " + ", ".join(str(sym) for sym in self.symbols))
        print("clauses:")
        for cla in self.clauses:
            print(cla)

    def create_tables(self, size: int):
        assert size >= 1
        self.size = size
        for sym in self.symbols:
            sym.create_table(size)
        for cla in self.clauses:
            cla.create_tables()

    def print_tables(self):
        for sym in self.symbols:
            print(sym.name + ": " + str(sym.table.flatten()))
