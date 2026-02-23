#!/usr/bin/env python3
"""Tkinter GUI for KenKen puzzle editing, random generation, and solving."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Tuple

from kenken_solver import Cage, KenKenPuzzle, KenKenSolver, generate_random_puzzle

Cell = Tuple[int, int]


class KenKenApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("KenKen Solver GUI")

        self.size_var = tk.IntVar(value=4)
        self.seed_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")

        top = ttk.Frame(root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Size:").pack(side=tk.LEFT)
        ttk.Spinbox(top, from_=3, to=9, width=4, textvariable=self.size_var).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Button(top, text="New Grid", command=self.new_grid).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="Seed:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Entry(top, width=10, textvariable=self.seed_var).pack(side=tk.LEFT)
        ttk.Button(top, text="Generate Random Puzzle", command=self.generate_random).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Solve", command=self.solve).pack(side=tk.LEFT, padx=4)

        main = ttk.Frame(root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        self.grid_frame = ttk.LabelFrame(main, text="Cage IDs per Cell")
        self.grid_frame.pack(side=tk.LEFT, padx=(0, 8))

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        rules_frame = ttk.LabelFrame(right, text="Cage rules (one per line: ID OP TARGET)")
        rules_frame.pack(fill=tk.BOTH, expand=True)
        self.rules_text = tk.Text(rules_frame, width=28, height=14)
        self.rules_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        solution_frame = ttk.LabelFrame(right, text="Solved Grid")
        solution_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.solution_text = tk.Text(solution_frame, width=28, height=10, state=tk.DISABLED)
        self.solution_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        ttk.Label(root, textvariable=self.status_var, padding=8).pack(fill=tk.X)

        self.cell_vars: Dict[Cell, tk.StringVar] = {}
        self.new_grid()

    def new_grid(self) -> None:
        size = self.size_var.get()
        for child in self.grid_frame.winfo_children():
            child.destroy()

        self.cell_vars = {}
        for r in range(size):
            for c in range(size):
                var = tk.StringVar(value=f"{r * size + c + 1}")
                self.cell_vars[(r, c)] = var
                e = ttk.Entry(self.grid_frame, width=4, justify="center", textvariable=var)
                e.grid(row=r, column=c, padx=2, pady=2)

        self.rules_text.delete("1.0", tk.END)
        for i in range(1, size * size + 1):
            self.rules_text.insert(tk.END, f"{i} = 1\n")
        self.set_solution_text("")
        self.status_var.set("New grid created. Edit IDs and cage rules.")

    def parse_puzzle(self) -> KenKenPuzzle:
        size = self.size_var.get()
        id_to_cells: Dict[str, List[Cell]] = {}
        for (r, c), var in self.cell_vars.items():
            cage_id = var.get().strip()
            if not cage_id:
                raise ValueError(f"Missing cage ID at cell ({r},{c}).")
            id_to_cells.setdefault(cage_id, []).append((r, c))

        rules: Dict[str, Tuple[str, int]] = {}
        for raw in self.rules_text.get("1.0", tk.END).splitlines():
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Invalid rule line: '{line}'")
            cage_id, op, target = parts
            if op not in {"+", "-", "*", "/", "="}:
                raise ValueError(f"Unsupported op '{op}' in line: '{line}'")
            rules[cage_id] = (op, int(target))

        cages: List[Cage] = []
        for cage_id, cells in id_to_cells.items():
            if cage_id not in rules:
                raise ValueError(f"Missing rule for cage ID '{cage_id}'.")
            op, target = rules[cage_id]
            if op == "=" and len(cells) != 1:
                raise ValueError(f"Cage '{cage_id}' uses '=' but has {len(cells)} cells.")
            cages.append(Cage(target=target, op=op, cells=tuple(cells)))

        return KenKenPuzzle(size=size, cages=cages)

    def generate_random(self) -> None:
        try:
            size = self.size_var.get()
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
            puzzle = generate_random_puzzle(size=size, seed=seed)

            for child in self.grid_frame.winfo_children():
                child.destroy()
            self.cell_vars = {}

            for idx, cage in enumerate(puzzle.cages, start=1):
                cage_id = str(idx)
                for r, c in cage.cells:
                    var = tk.StringVar(value=cage_id)
                    self.cell_vars[(r, c)] = var

            for r in range(size):
                for c in range(size):
                    e = ttk.Entry(self.grid_frame, width=4, justify="center", textvariable=self.cell_vars[(r, c)])
                    e.grid(row=r, column=c, padx=2, pady=2)

            self.rules_text.delete("1.0", tk.END)
            for idx, cage in enumerate(puzzle.cages, start=1):
                self.rules_text.insert(tk.END, f"{idx} {cage.op} {cage.target}\n")

            self.set_solution_text("")
            self.status_var.set("Random puzzle generated.")
        except Exception as exc:
            messagebox.showerror("Generate failed", str(exc))

    def solve(self) -> None:
        try:
            puzzle = self.parse_puzzle()
            solver = KenKenSolver(puzzle)
            if not solver.solve():
                self.set_solution_text("No solution found.")
                self.status_var.set("No solution found.")
                return

            out = "\n".join(" ".join(str(v) for v in row) for row in solver.grid)
            self.set_solution_text(out)
            self.status_var.set("Solved.")
        except Exception as exc:
            messagebox.showerror("Solve failed", str(exc))

    def set_solution_text(self, text: str) -> None:
        self.solution_text.configure(state=tk.NORMAL)
        self.solution_text.delete("1.0", tk.END)
        self.solution_text.insert(tk.END, text)
        self.solution_text.configure(state=tk.DISABLED)


def main() -> None:
    root = tk.Tk()
    KenKenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
