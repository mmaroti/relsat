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

from relsat.theory import *
import numpy


def run():
    equ = Symbol('equ', 2)
    mul = Symbol('mul', 3)
    inv = Symbol('inv', 2)
    one = Symbol('one', 1)

    thy = Theory(
        [equ, mul, inv, one],
        [
            Clause([
                Literal(6, False, mul, [0, 1, 3]),
                Literal(6, False, mul, [1, 2, 4]),
                Literal(6, False, mul, [3, 2, 5]),
                Literal(6, True, mul, [0, 4, 5]),
            ]),
            Clause([
                Literal(6, False, mul, [0, 1, 3]),
                Literal(6, False, mul, [1, 2, 4]),
                Literal(6, False, mul, [0, 4, 5]),
                Literal(6, True, mul, [3, 2, 5]),
            ]),
            Clause([
                Literal(2, False, one, [0]),
                Literal(2, True, mul, [0, 1, 1]),
            ]),
            Clause([
                Literal(3, False, inv, [0, 1]),
                Literal(3, False, mul, [1, 0, 2]),
                Literal(3, True, one, [2]),
            ]),
            Clause([
                Literal(4, False, mul, [0, 1, 2]),
                Literal(4, False, mul, [0, 1, 3]),
                Literal(4, True, equ, [2, 3]),
            ]),
            Clause([
                Literal(3, False, inv, [0, 1]),
                Literal(3, False, inv, [0, 2]),
                Literal(3, True, equ, [1, 2]),
            ]),
            Clause([
                Literal(2, False, one, [0]),
                Literal(2, False, one, [1]),
                Literal(2, True, equ, [0, 1]),
            ])
        ])

    thy.create_tables(2)
    equ.set_equality()
    one.set_value([0], 1)
    thy.print_tables()
    print()
    thy.propagate()
    thy.print_tables()
    thy.print_satisfied()


if __name__ == '__main__':
    run()
