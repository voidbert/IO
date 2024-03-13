#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <https://www.gnu.org/licenses/>.

from typing import Optional

Variable = tuple[float, Optional[int]]
"""
    A variable representing either a container (second item in tuple is None) or a given cutting
    pattern (container length and cutting pattern index).
"""

VarSum = dict[Variable, float]
""" A sum of variables, correlated to their coefficients. """

CuttingPattern = list[float]
"""
    One of many cutting patterns for a given length and set of items. Cutting patterns that leave
    more waste than the smallest item are considered invalid.
"""

ContainersPatterns = dict[float, list[CuttingPattern]]
""" Association between container lengths and their cutting patterns. """

CuttingPatternsCoefficients = dict[tuple[float, int], int]
"""
    Association between cutting patterns (container length and index) and how many of a given
    item produces.
"""

Containers = dict[float, Optional[int]]
""" Every container length associated to its available number (None for no upper bound). """

Items = dict[float, int]
""" Every item length associated to the number of that item that needs to be packed. """

def calculate_cutting_patterns(items: Items, length: float) -> list[CuttingPattern]:
    """ Generates all cutting patterns for a set of items and a length. """

    def calculate_cutting_patterns_rec(items: list[float], length: float) -> list[CuttingPattern]:
        patterns = []
        for i, item in enumerate(items):
            if item <= length:
                next_items = items[i:]
                patterns_remaining = calculate_cutting_patterns_rec(next_items, length - item)
                patterns_total = [[item] + p for p in patterns_remaining]
                patterns += patterns_total

        if len(patterns) == 0:
            patterns = [[]]
        return patterns

    items_list = sorted(list(items.keys()), reverse=True)
    patterns = calculate_cutting_patterns_rec(items_list, length)
    return [p for p in patterns if len(p) != 0]

def cutting_pattern_coefficients(item: float, \
                                 patterns: ContainersPatterns) -> CuttingPatternsCoefficients:
    """ Generates the coefficients for how much each cutting pattern produces of a given item. """

    ret = {}
    for length, container_patterns in patterns.items():
        for i, cut in enumerate(container_patterns):
            coefficient = cut.count(item)
            ret[(length, i)] = coefficient

    return ret

def output_variable(var: Variable) -> str:
    """ Outputs LP code with the name of a variable. """

    container, pattern = var
    return f'c{container}' if pattern is None else f'c{container}_{pattern + 1}'

def output_sum(summation: VarSum) -> str:
    """ Outputs LP code for a sum of variables. """

    variables = [f'{coefficient} {output_variable(variable)}' \
        for variable, coefficient in sorted(summation.items())]
    return ' + '.join(variables)

def output_objective(all_patterns: ContainersPatterns) -> str:
    """ Outputs LP code with the objective function of the model. """

    summation = {}
    for length, container_patterns in all_patterns.items():
        for i in range(len(container_patterns)):
            summation[(length, i)] = length

    return f'/* Minimize total container length */\nmin: {output_sum(summation)};'

def output_patterns_comment(all_patterns: ContainersPatterns) -> str:
    """ Outputs an LP comment describing all cutting patterns. """

    ret = '/*'
    for length, container_patterns in sorted(all_patterns.items()):
        ret += f'\n  Cutting patterns for containers of length {length}:\n'
        for i, pattern in enumerate(container_patterns):
            pattern_str = ' + '.join([str(length) for length in pattern])
            ret += f'    {i + 1}: {pattern_str}\n'

    return f'{ret}*/'

def output_item_requirements(items: Items, all_patterns: ContainersPatterns) -> str:
    """ Outputs LP code specifying how many items of each type need to be packed. """

    ret = '/* Minimum production of each item type */'
    for item, demand in items.items():
        summation = {}
        coefficients = cutting_pattern_coefficients(item, all_patterns)
        for variable, coefficient in coefficients.items():
            if coefficient != 0:
                summation[variable] = coefficient

        ret += f'\ni{item}: {output_sum(summation)} >= {demand};'

    return ret

def output_container_count_bounds(containers: Containers, all_patterns: ContainersPatterns) -> str:
    """ Outputs LP code with the restrictions for the maximum number of containers of each type. """

    ret = '/* Container upper bounds */'
    for container, container_patterns in sorted(all_patterns.items()):
        if containers[container] is not None:
            variables = {(container, i): 1 for i in range(len(container_patterns))}
            ret += f'\nc{container}: {output_sum(variables)} <= {containers[container]};'

    return ret

def output_integer_restrictions(all_patterns: ContainersPatterns) -> str:
    """ Outputs LP code informing all variables in the model are integers. """

    variables = []
    for container, container_patterns in sorted(all_patterns.items()):
        variables += [output_variable((container, i)) for i in range(len(container_patterns))]

    return f'int {", ".join(variables)};'

def output_model(containers: Containers, items: Items) -> str:
    """ Outputs LP code modelling a give bin-packing problem. """

    all_patterns = {length: calculate_cutting_patterns(items, length) for length in containers}

    ret = ''
    ret += f'{output_objective(all_patterns)}\n\n'
    ret += f'{output_patterns_comment(all_patterns)}\n\n'
    ret += f'{output_item_requirements(items, all_patterns)}\n\n'
    ret += f'{output_container_count_bounds(containers, all_patterns)}\n\n'
    ret += f'{output_integer_restrictions(all_patterns)}\n'

    return ret

if __name__ == '__main__':
    # Our problem's data
    print(output_model({11: None, 10: 5, 7: 5}, {2: 13, 4: 9, 5: 5}), end='')
