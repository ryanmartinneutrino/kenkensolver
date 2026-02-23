import unittest

from kenken_solver import KenKenPuzzle, KenKenSolver, generate_random_puzzle


class KenKenSolverTest(unittest.TestCase):
    def test_4x4_solves(self):
        puzzle = KenKenPuzzle.from_dict(
            {
                "size": 4,
                "cages": [
                    {"target": 4, "op": "+", "cells": [[0, 0], [1, 0]]},
                    {"target": 1, "op": "-", "cells": [[0, 1], [0, 2]]},
                    {"target": 2, "op": "/", "cells": [[0, 3], [1, 3]]},
                    {"target": 4, "op": "*", "cells": [[1, 1], [2, 1]]},
                    {"target": 3, "op": "+", "cells": [[1, 2], [2, 2]]},
                    {"target": 2, "op": "-", "cells": [[2, 0], [3, 0]]},
                    {"target": 4, "op": "+", "cells": [[2, 3], [3, 3]]},
                    {"target": 1, "op": "-", "cells": [[3, 1], [3, 2]]},
                ],
            }
        )
        solver = KenKenSolver(puzzle)
        self.assertTrue(solver.solve())
        self.assertEqual(
            solver.grid,
            [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [4, 1, 2, 3],
                [2, 3, 4, 1],
            ],
        )

    def test_random_puzzle_generation_is_solvable(self):
        puzzle = generate_random_puzzle(size=6, seed=1234)
        solver = KenKenSolver(puzzle)
        self.assertTrue(solver.solve())


if __name__ == "__main__":
    unittest.main()
