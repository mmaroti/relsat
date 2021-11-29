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
    """
    This represents a relational symbol with a given arity and optionally a
    value table storing the tuples in this relation. The value is positive if
    the given tuple is in the relation, it is negative if it is not, and it
    is zero if it is still unknown whether it is inside the relation or not.
    """

    def __init__(self, name: str, arity: int):
        """
        Creates the relational symbol with the given name and arity.
        """
        assert arity >= 0
        self.name = name
        self.arity = arity
        self.table = None

    def __str__(self):
        return self.name + "(" + \
            ",".join("x" + str(var) for var in range(self.arity)) + ")"

    def get_size(self):
        """
        Returns the size of the underlying universe (the relation must be at
        least unary).
        """
        assert self.arity > 0 and self.table is not None
        return self.table.shape[0]

    def create_table(self, size: int):
        """
        Creates an empty value table with full of zeros (undefined value).
        """
        assert size >= 1
        shape = [size for _ in range(self.arity)]
        self.table = numpy.zeros(shape=shape, dtype=numpy.int8)

    def set_constant(self, value: int):
        """
        Set all values of the table to the given one.
        """
        self.table.fill(value)

    def set_equality(self):
        """
        Sets the value in the table to the equality relation of arity 2.
        """
        assert self.arity == 2
        self.table.fill(-1)
        numpy.fill_diagonal(self.table, 1)

    def update_masked(self, mask: numpy.ndarray, value: int) -> bool:
        """
        Sets the values specified by the boolean mask array to the specified
        value. Also verifies that the sign of assigned values do not change.
        The mask must broadcast with the value table. Returns whether 
        something has been updated.
        """
        assert mask.ndim == self.arity and mask.dtype == bool

        # tests if we are not overwriting anything that is already set
        if value > 0:
            assert not numpy.logical_and(self.table < 0, mask).any()
        elif value < 0:
            assert not numpy.logical_and(self.table > 0, mask).any()

        changed = numpy.logical_and(self.table == 0, mask).any()
        self.table[mask] = value
        return changed

    def print_table(self):
        print(self.table.flatten())

    def get_value(self, coords: List[int]) -> int:
        """
        Returns the value at the specific location of the table.
        """
        assert len(coords) == self.arity
        return self.table[tuple(coords)]

    def set_value(self, coords: List[int], value: int):
        """
        Sets the value at the specific location of the table.
        """
        assert len(coords) == self.arity
        assert self.table[tuple(coords)] in [0, value]
        self.table[tuple(coords)] = value


class Literal:
    def __init__(self, arity: int, sign: bool, symbol: 'Symbol', vars: List[int]):
        """
        A literal in a universally classified clause with arity many free variables.
        The list of vars specify the mapping of coordinates of the relation to the
        set of free variables. The sign is true if this is a positive literal.
        """
        assert arity >= 0 and len(vars) == symbol.arity
        assert all(0 <= var < arity for var in vars)
        self.arity = arity
        self.symbol = symbol
        self.sign = sign
        self.vars = vars
        self.table = None

    def __str__(self):
        return ("+" if self.sign else "-") + str(self.symbol.name) + \
            "(" + ",".join("x" + str(var) for var in self.vars) + ")"

    def get_size(self):
        """
        Returns the size of the underlying universe (the symbol must be at
        least unary).
        """
        return self.symbol.get_size()

    def create_table(self):
        """
        Creates a view into the underlying symbol table with properly
        permuted axes, repeated axes diagonalized and unused axes set
        to new broadcasting dimensions of size 1.
        """
        table = self.symbol.table.view()
        assert table is not None

        # remove repeated axes
        vars = []
        for var in self.vars:
            if var in vars:
                idx = vars.index(var)
                table = table.diagonal(
                    axis1=idx, axis2=len(vars)).swapaxes(idx, -1)
            else:
                vars.append(var)
        assert len(vars) == len(table.shape)

        # add dummy axes
        shape = list(table.shape)
        shape.extend(1 for _ in range(self.arity - len(vars)))
        table.shape = shape

        # permute axes
        unused = len(vars)
        axes = []
        for var in range(self.arity):
            if var in vars:
                axes.append(vars.index(var))
            else:
                axes.append(unused)
                unused += 1
        assert unused == self.arity
        self.table = table.transpose(axes)

        # make sure that we have a view to the original data
        assert self.table.dtype == numpy.int8
        assert self.table.base is self.symbol.table

    def update_masked(self, mask: numpy.ndarray, value: int) -> bool:
        """
        Sets the values specified by the boolean mask array to the specified
        value. Also verifies that the sign of assigned values do not change.
        The dummy variables are removed from the mask by taking disjunctions.
        Returns whether something has been updated.
        """
        assert mask.ndim == self.arity and mask.dtype == bool
        assert value in [-1, 0, 1]

        # speed optimization
        if not mask.any():
            return False

        # fix the sign of value
        if not self.sign:
            value = -value

        # remove dummy axes
        axes = []
        for var in self.vars:
            if var not in axes:
                axes.append(var)
        keep = len(axes)
        for var in range(self.arity):
            if var not in axes:
                axes.append(var)
        mask = mask.view().transpose(axes)
        if keep < self.arity:
            mask.shape = list(mask.shape[:keep]) + [-1]
            mask = mask.any(axis=-1, keepdims=False)

        # zero arity case (no size info)
        if keep == 0:
            return self.symbol.update_masked(mask, value)

        # calculate equality constraints and reshape
        size = self.get_size()
        eye1 = numpy.eye(size, dtype=bool)
        equs = numpy.ones([size for _ in range(self.symbol.arity)], dtype=bool)

        shape = []
        for idx, var in enumerate(self.vars):
            pos = self.vars.index(var)
            if pos < idx:
                shape.append(1)
                eye2 = eye1.view()
                eye2.shape = [size if i == pos or i == idx else 1
                              for i in range(self.symbol.arity)]
                equs = numpy.logical_and(equs, eye2)
            else:
                pos = axes.index(var)
                shape.append(mask.shape[pos])

        mask.shape = shape
        mask = numpy.logical_and(mask, equs)
        return self.symbol.update_masked(mask, value)

    def set_constant(self, value: int):
        assert value in [-1, 0, 1]
        mask = numpy.ones([1 for _ in range(self.arity)], dtype=bool)
        self.update_masked(mask, value)

    def get_value_mask(self, value: int) -> numpy.ndarray:
        """
        Returns a bool table where the value table equals the given value.
        """
        assert value in [-1, 0, 1]
        return self.table == (value if self.sign else -value)

    def get_table(self):
        return self.table if self.sign else -self.table

    def get_value(self, coords: List[int]) -> int:
        assert len(coords) == self.arity
        coords = [coords[var] for var in self.vars]
        value = self.symbol.get_value(coords)
        return value if self.sign else -value

    def set_value(self, coords: List[int], value: int):
        assert len(coords) == self.arity
        coords = [coords[var] for var in self.vars]
        self.symbol.set_value(coords, value if self.sign else -value)


class Clause:
    def __init__(self, literals: List['Literal']):
        assert literals
        self.arity = literals[0].arity
        assert all(lit.arity == self.arity for lit in literals[1:])
        self.literals = literals

    def __str__(self):
        return ", ".join(str(lit) for lit in self.literals)

    def create_tables(self):
        for lit in self.literals:
            lit.create_table()

        # do propagation here
        if len(self.literals) == 1:
            self.literals[0].set_constant(1)

    def get_table(self):
        """
        Returns the disjunction of all literals.
        """
        table = self.literals[0].get_table()
        for lit in self.literals[1:]:
            table = numpy.maximum(table, lit.get_table())

        assert table.dtype == numpy.int8
        return table

    def satisfied(self) -> int:
        """
        Returns a positive integer if this clause is satisfied for all
        combination of the universally quantified variables, negative one if
        it is not satisfied for at least one combination, and zero if
        undefined for some combination and satisfied for others.
        """
        return numpy.amin(self.get_table())

    def propagate(self) -> bool:
        """
        Propagates forced values for this clause. Returns whether
        anything has been updated.
        """
        # this is already done
        if len(self.literals) <= 1:
            return False

        updated = False
        for target in range(len(self.literals)):
            value1 = None
            value2 = None
            for idx, lit in enumerate(self.literals):
                if idx == target:
                    value2 = lit.get_table()
                elif value1 is None:
                    value1 = lit.get_table()
                else:
                    value1 = numpy.maximum(value1, lit.get_table())
            assert value1.dtype == numpy.int8
            forced = numpy.logical_and(value1 < 0, value2 == 0)

            if self.literals[target].update_masked(forced, 1):
                updated = True

        return updated


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

    def print_satisfied(self):
        print("satisfied:")
        for cla in self.clauses:
            if cla.satisfied() > 0:
                print("  " + str(cla))
        print("unknown:")
        for cla in self.clauses:
            if cla.satisfied() == 0:
                print("  " + str(cla))
        print("failed:")
        for cla in self.clauses:
            if cla.satisfied() < 0:
                print("  " + str(cla))

    def propagate(self):
        updated = False
        counter = 0
        idx = 0
        while counter < len(self.clauses):
            cla = self.clauses[idx]
            if cla.propagate():
                updated = True
                counter = 1
            else:
                counter += 1
            idx += 1
            if idx >= len(self.clauses):
                idx = 0
        return updated
print