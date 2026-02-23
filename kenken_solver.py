#!/usr/bin/env python3
"""KenKen puzzle solver for grid sizes 3x3 to 9x9.

Supports two usage modes:
1. Load a puzzle from a JSON file.
2. Interactive input mode to build a puzzle manually.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from itertools import permutations, product
from typing import Dict, List, Optional, Sequence, Tuple

Cell = Tuple[int, int]


@dataclass(frozen=True)
class Cage:
    target: int
    op: str
    cells: Tuple[Cell, ...]


@dataclass
class KenKenPuzzle:
    size: int
    cages: List[Cage]

    @staticmethod
    def from_dict(data: Dict) -> "KenKenPuzzle":
        size = int(data["size"])
        cages = []
        for raw in data["cages"]:
            cells = tuple((int(r), int(c)) for r, c in raw["cells"])
            cages.append(Cage(target=int(raw["target"]), op=str(raw["op"]), cells=cells))
        return KenKenPuzzle(size=size, cages=cages)


class KenKenSolver:
    def __init__(self, puzzle: KenKenPuzzle) -> None:
        if not (3 <= puzzle.size <= 9):
            raise ValueError("Grid size must be between 3 and 9.")
        self.puzzle = puzzle
        self.n = puzzle.size
        self.values = tuple(range(1, self.n + 1))
        self.grid: List[List[int]] = [[0] * self.n for _ in range(self.n)]
        self.row_used = [set() for _ in range(self.n)]
        self.col_used = [set() for _ in range(self.n)]

        self.cell_to_cage: Dict[Cell, int] = {}
        for i, cage in enumerate(puzzle.cages):
            for cell in cage.cells:
                if cell in self.cell_to_cage:
                    raise ValueError(f"Cell {cell} appears in multiple cages.")
                self.cell_to_cage[cell] = i

        expected_cells = {(r, c) for r in range(self.n) for c in range(self.n)}
        if set(self.cell_to_cage) != expected_cells:
            missing = expected_cells - set(self.cell_to_cage)
            extra = set(self.cell_to_cage) - expected_cells
            raise ValueError(f"Cages must cover all cells exactly once. Missing={missing}, extra={extra}")

        self.cage_candidates: List[List[Tuple[int, ...]]] = []
        for cage in puzzle.cages:
            self.cage_candidates.append(self._generate_cage_candidates(cage))

    def _apply_op(self, values: Sequence[int], op: str) -> int:
        if op == "+":
            return sum(values)
        if op == "*":
            result = 1
            for v in values:
                result *= v
            return result
        if op == "-":
            result = values[0]
            for v in values[1:]:
                result -= v
            return result
        if op == "/":
            result = values[0]
            for v in values[1:]:
                if v == 0 or result % v != 0:
                    return -10**9
                result //= v
            return result
        if op == "=":
            if len(values) != 1:
                raise ValueError("'=' operation requires exactly one cell.")
            return values[0]
        raise ValueError(f"Unsupported operator '{op}'.")

    def _satisfies_cage(self, cage: Cage, vals: Sequence[int]) -> bool:
        if cage.op == "=":
            return len(vals) == 1 and vals[0] == cage.target

        if cage.op in {"+", "*"}:
            return self._apply_op(vals, cage.op) == cage.target

        # For subtraction/division, standard KenKen allows any order.
        if cage.op in {"-", "/"}:
            if len(vals) == 2:
                a, b = vals
                if cage.op == "-":
                    return abs(a - b) == cage.target
                bigger, smaller = max(a, b), min(a, b)
                return smaller != 0 and bigger % smaller == 0 and bigger // smaller == cage.target

            for perm in permutations(vals):
                if self._apply_op(perm, cage.op) == cage.target:
                    return True
            return False

        raise ValueError(f"Unsupported operator '{cage.op}'.")

    def _generate_cage_candidates(self, cage: Cage) -> List[Tuple[int, ...]]:
        out: List[Tuple[int, ...]] = []
        for vals in product(self.values, repeat=len(cage.cells)):
            if self._satisfies_cage(cage, vals):
                out.append(vals)
        if not out:
            raise ValueError(f"No valid combinations for cage {cage}.")
        return out

    def _cell_domain(self, r: int, c: int) -> List[int]:
        if self.grid[r][c] != 0:
            return [self.grid[r][c]]

        candidates = [v for v in self.values if v not in self.row_used[r] and v not in self.col_used[c]]
        cage_idx = self.cell_to_cage[(r, c)]
        cage = self.puzzle.cages[cage_idx]
        valid_vals = set()

        assigned = {}
        for i, (cr, cc) in enumerate(cage.cells):
            gv = self.grid[cr][cc]
            if gv != 0:
                assigned[i] = gv

        for combo in self.cage_candidates[cage_idx]:
            ok = True
            for idx, value in assigned.items():
                if combo[idx] != value:
                    ok = False
                    break
            if ok:
                pos = cage.cells.index((r, c))
                valid_vals.add(combo[pos])

        return [v for v in candidates if v in valid_vals]

    def _select_unassigned_cell(self) -> Optional[Cell]:
        best_cell: Optional[Cell] = None
        best_domain: Optional[List[int]] = None

        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] != 0:
                    continue
                domain = self._cell_domain(r, c)
                if len(domain) == 0:
                    return (r, c)
                if best_domain is None or len(domain) < len(best_domain):
                    best_domain = domain
                    best_cell = (r, c)
                    if len(best_domain) == 1:
                        return best_cell
        return best_cell

    def solve(self) -> bool:
        cell = self._select_unassigned_cell()
        if cell is None:
            return True

        r, c = cell
        domain = self._cell_domain(r, c)
        if not domain:
            return False

        for v in domain:
            self.grid[r][c] = v
            self.row_used[r].add(v)
            self.col_used[c].add(v)

            if self.solve():
                return True

            self.grid[r][c] = 0
            self.row_used[r].remove(v)
            self.col_used[c].remove(v)

        return False


def load_puzzle(path: str) -> KenKenPuzzle:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return KenKenPuzzle.from_dict(data)


def interactive_puzzle() -> KenKenPuzzle:
    size = int(input("Grid size (3-9): ").strip())
    cage_count = int(input("Number of cages: ").strip())
    cages = []
    print("Enter each cage as: target op r1,c1;r2,c2;...  (0-indexed coordinates)")
    for i in range(cage_count):
        raw = input(f"Cage {i + 1}: ").strip()
        target_s, op, cells_raw = raw.split(maxsplit=2)
        cells = []
        for token in cells_raw.split(";"):
            r_s, c_s = token.split(",")
            cells.append((int(r_s), int(c_s)))
        cages.append(Cage(target=int(target_s), op=op, cells=tuple(cells)))
    return KenKenPuzzle(size=size, cages=cages)


def print_grid(grid: List[List[int]]) -> None:
    for row in grid:
        print(" ".join(str(v) for v in row))


def main() -> None:
    parser = argparse.ArgumentParser(description="KenKen puzzle solver (3x3 to 9x9).")
    parser.add_argument("--input", help="Path to puzzle JSON file.")
    parser.add_argument("--interactive", action="store_true", help="Enter puzzle manually.")
    args = parser.parse_args()

    if not args.input and not args.interactive:
        parser.error("Use --input <file.json> or --interactive")

    puzzle = interactive_puzzle() if args.interactive else load_puzzle(args.input)
    solver = KenKenSolver(puzzle)
    solved = solver.solve()

    if not solved:
        print("No solution found.")
        raise SystemExit(1)

    print("Solved grid:")
    print_grid(solver.grid)


if __name__ == "__main__":
    main()
