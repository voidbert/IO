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

from collections.abc import Iterable
from typing import Optional

CutVar = tuple[float, float]
""" A variable that represents a one-cut [l;k]. """

VarSum = dict[CutVar, float]
"""
    A sum of variables is a dictionary where variables are associated to their linear coefficients.
"""

Containers = dict[float, Optional[int]]
""" Every container length associated to its available number (None for no upper bound). """

Items = dict[float, int]
""" Every item length associated to the number of that item that needs to be packed. """

def calculate_residuals(containers: Containers, items: Items) -> set[float]:
    """ Calculates the set of residual lengths from the containers and items. """

    min_items = min(items)
    all_to_cut = list(containers)
    residuals = set()

    while len(all_to_cut) > 0:
        to_cut = all_to_cut[0]
        for item in items:
            if to_cut > item:
                cut = to_cut - item

                residuals.add(item)
                if cut >= min_items:
                    if cut not in residuals:
                        all_to_cut.append(cut)
                    residuals.add(cut)

        all_to_cut = all_to_cut[1:]

    return residuals

def merge_sums(sums: Iterable[VarSum]) -> VarSum:
    """ Sums many variable sums together. """

    final_sum: VarSum = {}
    for summation in sums:
        for variable, coefficient in summation.items():
            final_coefficient = final_sum.get(variable)
            final_sum[variable] = \
                coefficient if final_coefficient is None else final_coefficient + coefficient

    # Remove variables with coefficient zero and with redundant names (e.g.: y7_5 and y7_2)
    ret = {variable: coefficient for variable, coefficient in final_sum.items() if variable != 0}
    return {(l, k): coefficient for (l, k), coefficient in ret.items() if \
        not (k < l - k and (l, l - k) in ret)}

def output_variable(variable: CutVar, all_variables: set[str], items: Items) -> str:
    """
        Outputs LP code for a variable representing a cut. all_variables will be filled with all
        variables ever outputted, so they can later be declared to be integers later on.
    """

    l, k = variable
    ret = f'y{l}_{k}' if k in items else f'y{l}_{l - k}'
    all_variables.add(ret)
    return ret

def output_sum(summation: VarSum, all_variables: set[str], items: Items) -> str:
    """
        Outputs LP code with a sum of variables and their linear coefficients. all_variables will be
        filled with allvariables ever outputted, so they can later be declared to be integers.
    """

    ret = ''
    for variable, coefficient in sorted(summation.items(), key=lambda item: item[0], reverse=True):
        str_coefficient = '' if coefficient == 1 else f'{coefficient} '
        ret += f'{str_coefficient}{output_variable(variable, all_variables, items)} + '
    return ret[:-3]

def output_objective(containers: Containers, \
                     items: Items, \
                     residuals: set[float], \
                     all_variables: set[str]) -> str:
    """
        Outputs LP code with the objective function of the problem. all_variables will be filled
        with all variables ever outputted, so they can later be declared to be integers.
    """

    ret = '/* Standardize optimizations of max{0, ...} */'
    stock_residuals_union = set(containers.keys()).union(residuals)

    for l in containers:
        b_sum = {(k + l, k): -1 for k in items if k + l in stock_residuals_union}
        c_sum = {(l, k): 1 for k in items if k < l}

        ret += f'\nm{l} >= {output_sum(merge_sums([b_sum, c_sum]), all_variables, items)};'

    objective = " + ".join([f'{l} m{l}' for l in containers])
    return f'min: {objective};\n\n{ret}'

def output_balance_restrictions(containers: Containers, \
                                items: Items, \
                                residuals: set[float], \
                                all_variables: set[str]) -> str:
    """
        Outputs LP code with all balance restrictions for the problem. all_variables will be filled
        with all variables ever outputted, so they can later be declared to be integers.
    """

    ret = '/* Balance restrictions */'
    stock_residuals_union = set(containers.keys()).union(residuals)
    l_values = sorted(set(items.keys()).union(residuals).difference(set(containers.keys())))
    for l in l_values:
        a_set = {k for k in stock_residuals_union if k > l} if l in items else set()

        a_sum = {(k, l): 1 for k in a_set}
        b_sum = {(k + l, k): 1 for k in items if k + l in stock_residuals_union}
        c_sum = {(l, k): -1 for k in items if k < l}

        summation = merge_sums([a_sum, b_sum, c_sum])
        ret += f'\nl{l}: {output_sum(summation, all_variables, items)} >= {items.get(l, 0)};'

    return ret

def output_container_count_bounds(containers: Containers, \
                                  items: Items, \
                                  residuals: set[float], \
                                  all_variables: set[str]) -> str:
    """ Outputs LP code limiting the number of containers of each type to their upper bound. """

    ret = '/* Container upper bounds */'
    stock_residuals_union = set(containers.keys()).union(residuals)
    for l, upper_bound in containers.items():
        if upper_bound is not None:
            b_sum = {(k + l, k): -1 for k in items if k + l in stock_residuals_union}
            c_sum = {(l, k): 1 for k in items if k < l}
            summation = merge_sums([b_sum, c_sum])

            ret += f'\nc{l}: {output_sum(summation, all_variables, items)} <= {upper_bound};'

    return ret

def output_integer_restrictions(all_variables: set[str]) -> str:
    """ Outputs LP code telling that all variables ever outputted are integers. """
    return 'int ' + ', '.join(sorted(all_variables)) + ';'

def output_model(containers: Containers, items: Items) -> str:
    """ Outputs LP code modelling a give bin-packing problem. """

    ret = ''
    all_variables: set[str] = set()
    residuals = calculate_residuals(containers, items)

    ret += f'{output_objective(containers, items, residuals, all_variables)}\n\n'
    ret += f'{output_balance_restrictions(containers, items, residuals, all_variables)}\n\n'
    ret += f'{output_container_count_bounds(containers, items, residuals, all_variables)}\n\n'
    ret += f'{output_integer_restrictions(all_variables)}\n'
    return ret

if __name__ == '__main__':
    # Our problem's data
    print(output_model({11: None, 10: 5, 7: 5}, {2: 13, 4: 9, 5: 5}), end='')

    # Example from Dyckhoff's one-cut model:
    # print(output_model({5: None, 6: None, 9: None}, {2: 20, 3: 10, 4: 20}), end='')
