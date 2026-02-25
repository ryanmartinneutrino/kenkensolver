# KenKen Puzzle Builder + Solver

Offline KenKen application for Linux (air-gapped friendly) with a mouse/keyboard GUI for creating and solving puzzles.

## What this app now supports

- Grid size `n x n` where `3 <= n <= 9`.
- Interactive block (cage) creation directly on a visual grid.
- Mouse-based cell assignment/removal for each block.
- Rule editing per block:
  - operator in `{+, -, *, /, =}`
  - integer target
  - explicit rule cell location
- Distinct visual block borders and in-cell rule labels.
- Solve button that applies all KenKen constraints:
  - values `1..n`
  - no duplicates in any row/column
  - all block rules satisfied
- Solve time display.
- Clear/reset workflow.
- Save puzzle to JSON and load it later.

## Requirements

- Python 3.9+
- Tkinter (usually included in standard Linux Python packages)

## Run the GUI

```bash
python3 kenken_gui.py
```

## GUI usage workflow

1. Set puzzle size (3–9) and click **New Grid**.
2. Click **New Block**.
3. Click cells in the grid to add/remove them from the selected block.
4. Set **Operator**, **Target**, and choose a **Rule cell (r,c)**.
5. Click **Apply Rule**.
6. Repeat steps 2–5 until all cells are assigned to blocks.
7. Click **Solve**.

### Helpful actions

- **Delete Block**: removes selected block and frees its cells.
- **Clear All**: resets blocks and solution on the current grid size.
- **Save Puzzle**: writes puzzle JSON to disk.
- **Load Puzzle**: restores a saved puzzle.
- **Cell size slider**: visually resize puzzle cells.

## Validation rules enforced before solve

- Grid size must be between 3 and 9.
- Every cell must belong to exactly one block.
- Each block must be connected by edge adjacency.
- Every block must have exactly one rule cell in that block.
- Every block must have one operator and one integer target.
- `=` blocks must have exactly one cell and target in `1..n`.
- `-` and `/` blocks must have exactly two cells.

## CLI solver (still available)

Solve from JSON:

```bash
python3 kenken_solver.py --input examples/sample_4x4.json
```

Or interactive terminal input:

```bash
python3 kenken_solver.py --interactive
```

## JSON format

The loader accepts the base format below. The GUI also saves optional fields (`id`, `rule_cell`) to preserve editor metadata.

```json
{
  "size": 4,
  "cages": [
    {
      "target": 4,
      "op": "+",
      "cells": [[0, 0], [1, 0]],
      "rule_cell": [0, 0],
      "id": 1
    },
    {
      "target": 3,
      "op": "=",
      "cells": [[2, 2]],
      "rule_cell": [2, 2],
      "id": 2
    }
  ]
}
```

## Tests

```bash
python3 -m unittest -v
```
