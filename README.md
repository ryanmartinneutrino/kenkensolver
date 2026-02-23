# KenKen Puzzle Solver

Offline KenKen solver for Linux laptops (air-gapped compatible). Supports grid sizes from **3x3 to 9x9**.

## Features

- Solves KenKen puzzles with operators `+`, `-`, `*`, `/`, and `=`.
- Enforces KenKen row/column constraints (digits `1..N`, no duplicates per row/column).
- Works with either:
  - **JSON puzzle input** (good for importing from websites manually), or
  - **Interactive mode** (build puzzle directly in terminal).

## Run

```bash
python3 kenken_solver.py --input examples/sample_4x4.json
```

or

```bash
python3 kenken_solver.py --interactive
```

## JSON format

```json
{
  "size": 4,
  "cages": [
    {"target": 4, "op": "+", "cells": [[0,0],[1,0]]},
    {"target": 3, "op": "=", "cells": [[2,2]]}
  ]
}
```

- Coordinates are **0-indexed** (`row`, `col`).
- Cages must cover every grid cell exactly once.

## Test

```bash
python3 -m unittest -v
```
