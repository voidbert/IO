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

from sys import stderr

Graph = tuple[dict[int, int], dict[tuple[int, int], tuple[int, int]]]
""" A graph (vertices (number -> flow), edges (origin, destination -> cost, capacity)). """

def relax_to_graph(lines: list[str]) -> Graph:
    """ Generates a graph from the lines in a Relax4 file """

    try:
        vertex_count = int(lines[0])
    except (IndexError, ValueError) as e:
        raise ValueError('Failed to read number of vertices (line 1)') from e

    try:
        edge_count = int(lines[1])
    except (IndexError, ValueError) as e:
        raise ValueError('Failed to read number of edges (line 2)') from e

    expected_lines = 2 + vertex_count + edge_count
    if len(lines) != expected_lines:
        raise ValueError(f'Wrong number of lines (got {len(lines)}, expected {expected_lines})')

    edges = {}
    for i in range(edge_count):
        values = lines[i + 2].split()

        try:
            origin = int(values[0])
            if origin not in range(1, vertex_count + 1):
                raise IndexError()
        except (ValueError, IndexError) as e:
            raise ValueError(f'Failed to parse origin in edge {i + 1} (line {i + 3})') from e

        try:
            destination = int(values[1])
            if destination not in range(1, vertex_count + 1):
                raise IndexError()
        except (ValueError, IndexError) as e:
            raise ValueError(f'Failed to parse destination in edge {i + 1} (line {i + 3})') from e

        try:
            cost = int(values[2])
        except (ValueError, IndexError) as e:
            raise ValueError(f'Failed to parse cost in edge {i + 1} (line {i + 3})') from e

        try:
            capacity = int(values[3])
        except (ValueError, IndexError) as e:
            raise ValueError(f'Failed to parse capacity in edge {i + 1} (line {i + 3})') from e

        edges[(origin, destination)] = (cost, capacity)

    vertices = {}
    for i in range(vertex_count):
        try:
            vertices[i + 1] = int(lines[i + 2 + edge_count])
        except ValueError as e:
            raise ValueError(\
                f'Failed to parse flow of vertex {i + 1} (line {i + edge_count + 1})') from e

    balance = sum(vertices.values())
    if balance != 0:
        raise ValueError(f'Unbalanced model (balance = {balance})')

    return (vertices, edges)

def graph_to_lp(graph: Graph) -> str:
    vertices, edges = graph

    objective = 'min: ' + ' + '.join([ f'{c}x{o}_{d}' for ((o, d), (c, _)) in edges.items() ]) + ';'

    flow_restrictions = []
    for v, f in vertices.items():
        in_edges  = [ o for (o, d) in edges if d == v ]
        out_edges = [ d for (o, d) in edges if o == v ]
        if len(in_edges) + len(out_edges) == 0:
            continue
        flow_restrictions.append(' '.join([ f'- x{o}_{v}' for o in in_edges ]) + \
                                 ' '.join([ f'+ x{v}_{d}' for d in out_edges ]) + f' = {f};')

    flow = '\n'.join(flow_restrictions)
    maxflow = '\n'.join([ f'x{o}_{d} <= {c};' for ((o, d), (_, c)) in edges.items() ])
    integer = 'int ' + ', '.join([ f'x{o}_{d}' for (o, d) in edges ]) + ';'

    return '\n'.join([objective, '', flow, '', maxflow, '', integer])

def main():
    """ Entry point to the script """

    lines = []
    while True:
        try:
            lines.append(input())
        except EOFError:
            break

    try:
        print(graph_to_lp(relax_to_graph(lines)))
    except ValueError as e:
        print(str(e), file=stderr)

if __name__ == '__main__':
    main()
