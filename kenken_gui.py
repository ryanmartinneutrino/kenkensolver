#!/usr/bin/env python3
"""Interactive Tkinter GUI for building, saving, loading, and solving KenKen puzzles."""

from __future__ import annotations

import json
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set, Tuple

from kenken_solver import Cage, KenKenPuzzle, KenKenSolver

Cell = Tuple[int, int]
OPERATORS = {"+", "-", "*", "/", "="}
BLOCK_COLORS = [
    "#fce4ec",
    "#e8f5e9",
    "#e3f2fd",
    "#fff8e1",
    "#f3e5f5",
    "#e0f2f1",
    "#fbe9e7",
    "#ede7f6",
]


@dataclass
class BlockDef:
    block_id: int
    cells: Set[Cell] = field(default_factory=set)
    op: str = "+"
    target: Optional[int] = None
    rule_cell: Optional[Cell] = None
    color: str = "#ffffff"


class KenKenApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("KenKen Builder + Solver")

        self.size_var = tk.IntVar(value=4)
        self.cell_px_var = tk.IntVar(value=76)
        self.status_var = tk.StringVar(value="Choose puzzle size and click New Grid.")
        self.solve_time_var = tk.StringVar(value="Solve time: --")

        self.blocks: Dict[int, BlockDef] = {}
        self.cell_to_block: Dict[Cell, int] = {}
        self.current_block_id: Optional[int] = None
        self.solution_grid: Optional[List[List[int]]] = None

        self.op_var = tk.StringVar(value="+")
        self.target_var = tk.StringVar(value="")
        self.rule_cell_var = tk.StringVar(value="")

        self._build_ui()
        self.new_grid()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Size (3-9):").pack(side=tk.LEFT)
        ttk.Spinbox(top, from_=3, to=9, width=4, textvariable=self.size_var).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Button(top, text="New Grid", command=self.new_grid).pack(side=tk.LEFT)
        ttk.Button(top, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Save Puzzle", command=self.save_puzzle).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Load Puzzle", command=self.load_puzzle).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Solve", command=self.solve).pack(side=tk.LEFT, padx=(12, 4))

        ttk.Label(top, textvariable=self.solve_time_var).pack(side=tk.RIGHT)

        body = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(body, text="Puzzle Grid")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        right = ttk.LabelFrame(body, text="Block Editor")
        right.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))

        ctrl = ttk.Frame(right, padding=8)
        ctrl.pack(fill=tk.BOTH)

        ttk.Label(ctrl, text="Cell size:").grid(row=0, column=0, sticky="w")
        ttk.Scale(ctrl, from_=48, to=110, variable=self.cell_px_var, command=lambda _v: self.redraw()).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        ttk.Button(ctrl, text="New Block", command=self.new_block).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(ctrl, text="Delete Block", command=self.delete_selected_block).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=(8, 0)
        )

        ttk.Label(ctrl, text="Blocks:").grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.block_list = tk.Listbox(ctrl, width=22, height=10)
        self.block_list.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.block_list.bind("<<ListboxSelect>>", self.on_block_select)

        ttk.Label(ctrl, text="Operator:").grid(row=4, column=0, sticky="w", pady=(10, 2))
        ttk.Combobox(ctrl, width=6, state="readonly", textvariable=self.op_var, values=sorted(OPERATORS)).grid(
            row=4, column=1, sticky="w", pady=(10, 2)
        )

        ttk.Label(ctrl, text="Target:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(ctrl, textvariable=self.target_var, width=10).grid(row=5, column=1, sticky="w", pady=2)

        ttk.Label(ctrl, text="Rule cell (r,c):").grid(row=6, column=0, sticky="w", pady=2)
        self.rule_cell_combo = ttk.Combobox(ctrl, width=10, textvariable=self.rule_cell_var, state="readonly")
        self.rule_cell_combo.grid(row=6, column=1, sticky="w", pady=2)

        ttk.Button(ctrl, text="Apply Rule", command=self.apply_rule_to_selected).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        hint = (
            "How to use:\n"
            "1) Click New Block.\n"
            "2) Click cells on grid to add/remove from selected block.\n"
            "3) Set operator, target, and rule cell.\n"
            "4) Repeat until all cells belong to blocks.\n"
            "5) Click Solve."
        )
        ttk.Label(ctrl, text=hint, justify="left", wraplength=220).grid(row=8, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ctrl.columnconfigure(1, weight=1)
        ctrl.rowconfigure(3, weight=1)

        ttk.Label(self.root, textvariable=self.status_var, padding=8).pack(fill=tk.X)

    def _grid_size(self) -> int:
        size = self.size_var.get()
        if not (3 <= size <= 9):
            raise ValueError("Grid size n must be between 3 and 9.")
        return size

    def clear_all(self) -> None:
        self.blocks = {}
        self.cell_to_block = {}
        self.current_block_id = None
        self.solution_grid = None
        self.op_var.set("+")
        self.target_var.set("")
        self.rule_cell_var.set("")
        self.refresh_block_list()
        self.redraw()
        self.solve_time_var.set("Solve time: --")
        self.status_var.set("Cleared all blocks and solution values.")

    def new_grid(self) -> None:
        try:
            self._grid_size()
        except ValueError as exc:
            messagebox.showerror("Invalid size", str(exc))
            return
        self.clear_all()
        self.status_var.set("New empty grid created. Create blocks using mouse clicks.")

    def new_block(self) -> None:
        next_id = max(self.blocks.keys(), default=0) + 1
        block = BlockDef(block_id=next_id, color=BLOCK_COLORS[(next_id - 1) % len(BLOCK_COLORS)])
        self.blocks[next_id] = block
        self.current_block_id = next_id
        self.refresh_block_list()
        self._select_block_in_list(next_id)
        self.update_editor_for_selected_block()
        self.redraw()
        self.status_var.set(f"Created block #{next_id}. Click cells to add/remove.")

    def delete_selected_block(self) -> None:
        block = self.get_selected_block()
        if not block:
            return
        for cell in list(block.cells):
            self.cell_to_block.pop(cell, None)
        del self.blocks[block.block_id]
        self.current_block_id = None
        self.refresh_block_list()
        self.update_editor_for_selected_block()
        self.redraw()
        self.status_var.set("Deleted selected block.")

    def on_block_select(self, _event: tk.Event) -> None:
        selection = self.block_list.curselection()
        if not selection:
            self.current_block_id = None
            self.update_editor_for_selected_block()
            self.redraw()
            return
        line = self.block_list.get(selection[0])
        block_id = int(line.split()[1].lstrip("#"))
        self.current_block_id = block_id
        self.update_editor_for_selected_block()
        self.redraw()

    def get_selected_block(self) -> Optional[BlockDef]:
        if self.current_block_id is None:
            return None
        return self.blocks.get(self.current_block_id)

    def on_canvas_click(self, event: tk.Event) -> None:
        size = self._grid_size()
        cell_px = self.cell_px_var.get()
        c = event.x // cell_px
        r = event.y // cell_px
        if not (0 <= r < size and 0 <= c < size):
            return

        block = self.get_selected_block()
        if not block:
            self.status_var.set("Select or create a block first.")
            return

        cell = (r, c)
        owner = self.cell_to_block.get(cell)
        if owner is None:
            block.cells.add(cell)
            self.cell_to_block[cell] = block.block_id
            if block.rule_cell is None:
                block.rule_cell = cell
        elif owner == block.block_id:
            block.cells.remove(cell)
            del self.cell_to_block[cell]
            if block.rule_cell == cell:
                block.rule_cell = min(block.cells) if block.cells else None
        else:
            self.status_var.set(f"Cell {cell} already belongs to block #{owner}. Select that block to edit it.")
            return

        self.update_editor_for_selected_block()
        self.refresh_block_list()
        self.redraw()

    def update_editor_for_selected_block(self) -> None:
        block = self.get_selected_block()
        if not block:
            self.op_var.set("+")
            self.target_var.set("")
            self.rule_cell_var.set("")
            self.rule_cell_combo.configure(values=[])
            return

        self.op_var.set(block.op)
        self.target_var.set("" if block.target is None else str(block.target))
        sorted_cells = sorted(block.cells)
        options = [f"{r},{c}" for r, c in sorted_cells]
        self.rule_cell_combo.configure(values=options)
        if block.rule_cell and block.rule_cell in block.cells:
            self.rule_cell_var.set(f"{block.rule_cell[0]},{block.rule_cell[1]}")
        elif options:
            self.rule_cell_var.set(options[0])
            block.rule_cell = sorted_cells[0]
        else:
            self.rule_cell_var.set("")

    def apply_rule_to_selected(self) -> None:
        block = self.get_selected_block()
        if not block:
            self.status_var.set("Select a block first.")
            return
        if not block.cells:
            messagebox.showerror("Invalid block", "Selected block has no cells.")
            return

        op = self.op_var.get().strip()
        if op not in OPERATORS:
            messagebox.showerror("Invalid operator", "Operator must be one of +, -, *, /, =")
            return

        try:
            target = int(self.target_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid target", "Target must be an integer.")
            return

        if op == "=" and len(block.cells) != 1:
            messagebox.showerror("Invalid '=' block", "Operator '=' requires exactly one cell.")
            return

        if op in {"-", "/"} and len(block.cells) != 2:
            messagebox.showerror("Invalid block size", "Operators '-' and '/' require exactly two cells.")
            return

        if op == "=":
            n = self._grid_size()
            if not (1 <= target <= n):
                messagebox.showerror("Invalid '=' value", f"For '=' cages, target must be between 1 and {n}.")
                return

        rule_raw = self.rule_cell_var.get().strip()
        if not rule_raw:
            messagebox.showerror("Missing rule cell", "Choose a rule cell in this block.")
            return
        try:
            rr, cc = (int(x) for x in rule_raw.split(",", maxsplit=1))
            rule_cell = (rr, cc)
        except Exception:
            messagebox.showerror("Invalid rule cell", "Rule cell must be in 'row,col' format.")
            return
        if rule_cell not in block.cells:
            messagebox.showerror("Invalid rule cell", "Rule cell must be one of the block's cells.")
            return

        block.op = op
        block.target = target
        block.rule_cell = rule_cell
        self.refresh_block_list()
        self.redraw()
        self.status_var.set(f"Applied rule to block #{block.block_id}.")

    def refresh_block_list(self) -> None:
        self.block_list.delete(0, tk.END)
        for block_id in sorted(self.blocks):
            block = self.blocks[block_id]
            rule = "?"
            if block.target is not None:
                rule = f"{block.op}{block.target}" if block.op != "=" else str(block.target)
            self.block_list.insert(tk.END, f"ID #{block_id}  cells={len(block.cells)}  rule={rule}")

    def _select_block_in_list(self, block_id: int) -> None:
        for idx in range(self.block_list.size()):
            if self.block_list.get(idx).startswith(f"ID #{block_id} "):
                self.block_list.selection_clear(0, tk.END)
                self.block_list.selection_set(idx)
                self.block_list.activate(idx)
                return

    def _adjacent(self, a: Cell, b: Cell) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _is_connected(self, cells: Set[Cell]) -> bool:
        if not cells:
            return False
        stack = [next(iter(cells))]
        visited = set()
        while stack:
            cell = stack.pop()
            if cell in visited:
                continue
            visited.add(cell)
            for other in cells:
                if other not in visited and self._adjacent(cell, other):
                    stack.append(other)
        return len(visited) == len(cells)

    def validate_before_solve(self) -> None:
        n = self._grid_size()
        expected_cells = {(r, c) for r in range(n) for c in range(n)}

        if set(self.cell_to_block) != expected_cells:
            missing = expected_cells - set(self.cell_to_block)
            raise ValueError(f"All cells must belong to a block before solving. Missing cells: {sorted(missing)}")

        if not self.blocks:
            raise ValueError("No blocks defined.")

        for block in self.blocks.values():
            if not block.cells:
                raise ValueError(f"Block #{block.block_id} has no cells.")
            if not self._is_connected(block.cells):
                raise ValueError(f"Block #{block.block_id} cells must be adjacent/connected.")
            if block.target is None:
                raise ValueError(f"Block #{block.block_id} is missing a target.")
            if block.op not in OPERATORS:
                raise ValueError(f"Block #{block.block_id} has invalid operator '{block.op}'.")
            if block.rule_cell is None or block.rule_cell not in block.cells:
                raise ValueError(f"Block #{block.block_id} must have exactly one rule cell in the block.")
            if block.op == "=" and len(block.cells) != 1:
                raise ValueError(f"Block #{block.block_id} uses '=' and must contain exactly one cell.")
            if block.op in {"-", "/"} and len(block.cells) != 2:
                raise ValueError(f"Block #{block.block_id} uses '{block.op}' and must contain exactly two cells.")
            if block.op == "=" and not (1 <= block.target <= n):
                raise ValueError(f"Block #{block.block_id} with '=' must have target between 1 and {n}.")

    def to_puzzle(self) -> KenKenPuzzle:
        cages = []
        for block_id in sorted(self.blocks):
            block = self.blocks[block_id]
            cages.append(Cage(target=int(block.target), op=block.op, cells=tuple(sorted(block.cells))))
        return KenKenPuzzle(size=self._grid_size(), cages=cages)

    def solve(self) -> None:
        try:
            self.validate_before_solve()
            puzzle = self.to_puzzle()
            solver = KenKenSolver(puzzle)
            t0 = time.perf_counter()
            solved = solver.solve()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.solve_time_var.set(f"Solve time: {elapsed_ms:.2f} ms")

            if not solved:
                self.solution_grid = None
                self.status_var.set("No solution found.")
                messagebox.showinfo("No solution", "No solution found for this puzzle.")
                self.redraw()
                return

            self.solution_grid = solver.grid
            self.redraw()
            self.status_var.set("Solved successfully.")
        except Exception as exc:
            messagebox.showerror("Solve failed", str(exc))

    def redraw(self) -> None:
        self.canvas.delete("all")
        n = self._grid_size()
        cell_px = self.cell_px_var.get()
        w = n * cell_px
        h = n * cell_px
        self.canvas.configure(width=w, height=h, scrollregion=(0, 0, w, h))

        # Fill cells
        for r in range(n):
            for c in range(n):
                x0, y0 = c * cell_px, r * cell_px
                x1, y1 = x0 + cell_px, y0 + cell_px
                bid = self.cell_to_block.get((r, c))
                fill = "white"
                if bid is not None and bid in self.blocks:
                    fill = self.blocks[bid].color
                if bid is not None and bid == self.current_block_id:
                    fill = "#ffe082"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#d9d9d9", width=1)

        # Block heavy borders
        for r in range(n):
            for c in range(n):
                cell = (r, c)
                owner = self.cell_to_block.get(cell)
                x0, y0 = c * cell_px, r * cell_px
                x1, y1 = x0 + cell_px, y0 + cell_px

                top_owner = self.cell_to_block.get((r - 1, c)) if r > 0 else None
                left_owner = self.cell_to_block.get((r, c - 1)) if c > 0 else None
                bottom_owner = self.cell_to_block.get((r + 1, c)) if r + 1 < n else None
                right_owner = self.cell_to_block.get((r, c + 1)) if c + 1 < n else None

                if owner != top_owner:
                    self.canvas.create_line(x0, y0, x1, y0, width=3)
                if owner != left_owner:
                    self.canvas.create_line(x0, y0, x0, y1, width=3)
                if owner != bottom_owner:
                    self.canvas.create_line(x0, y1, x1, y1, width=3)
                if owner != right_owner:
                    self.canvas.create_line(x1, y0, x1, y1, width=3)

        # Rule labels and solution numbers
        for block in self.blocks.values():
            if block.rule_cell and block.target is not None:
                rr, cc = block.rule_cell
                x0, y0 = cc * cell_px, rr * cell_px
                label = str(block.target) if block.op == "=" else f"{block.target}{block.op}"
                self.canvas.create_text(x0 + 6, y0 + 6, text=label, anchor="nw", font=("Arial", max(8, cell_px // 6)))

        if self.solution_grid:
            for r in range(n):
                for c in range(n):
                    x = c * cell_px + cell_px / 2
                    y = r * cell_px + cell_px / 2 + 8
                    self.canvas.create_text(x, y, text=str(self.solution_grid[r][c]), font=("Arial", max(14, cell_px // 2), "bold"))

    def _puzzle_json(self) -> Dict:
        data = {
            "size": self._grid_size(),
            "cages": [],
        }
        for block_id in sorted(self.blocks):
            block = self.blocks[block_id]
            data["cages"].append(
                {
                    "id": block_id,
                    "target": block.target,
                    "op": block.op,
                    "cells": [[r, c] for r, c in sorted(block.cells)],
                    "rule_cell": list(block.rule_cell) if block.rule_cell else None,
                }
            )
        return data

    def save_puzzle(self) -> None:
        try:
            self.validate_before_solve()
        except Exception:
            # allow partial saves, but warn user
            pass

        path = filedialog.asksaveasfilename(
            title="Save KenKen puzzle",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._puzzle_json(), f, indent=2)
        self.status_var.set(f"Saved puzzle to {Path(path).name}")

    def load_puzzle(self) -> None:
        path = filedialog.askopenfilename(
            title="Load KenKen puzzle",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.size_var.set(int(data["size"]))
        self.clear_all()

        for idx, cage in enumerate(data.get("cages", []), start=1):
            block_id = int(cage.get("id", idx))
            cells = {tuple(cell) for cell in cage["cells"]}
            block = BlockDef(
                block_id=block_id,
                cells=cells,
                op=str(cage["op"]),
                target=int(cage["target"]),
                color=BLOCK_COLORS[(block_id - 1) % len(BLOCK_COLORS)],
            )
            if cage.get("rule_cell") is not None:
                rc = tuple(cage["rule_cell"])
                block.rule_cell = rc if rc in cells else min(cells)
            else:
                block.rule_cell = min(cells)

            self.blocks[block_id] = block
            for cell in cells:
                if cell in self.cell_to_block:
                    raise ValueError(f"Cell {cell} appears in multiple blocks in loaded file.")
                self.cell_to_block[cell] = block_id

        self.current_block_id = min(self.blocks) if self.blocks else None
        self.refresh_block_list()
        if self.current_block_id is not None:
            self._select_block_in_list(self.current_block_id)
        self.update_editor_for_selected_block()
        self.solution_grid = None
        self.redraw()
        self.status_var.set(f"Loaded puzzle from {Path(path).name}")


def main() -> None:
    root = tk.Tk()
    KenKenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
