"""
Simple Tic-Tac-Toe Agent
Expects the game state as a 3x3 list of lists:
[['', '', ''],
 ['', '', ''],
 ['', '', '']]
and returns a move as (row, col).
"""

import random
import json
import sys

def find_empty_cells(board):
    """Return list of empty cells as (row, col)."""
    empty = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == "":
                empty.append((i, j))
    return empty

def random_agent_move(board):
    """Pick a random empty cell."""
    empty = find_empty_cells(board)
    if not empty:
        return None  # board full
    return random.choice(empty)

def main():
    # Read input JSON from stdin (or file)
    input_data = sys.stdin.read()
    data = json.loads(input_data)
    board = data.get("board", [[""]*3 for _ in range(3)])

    # Get move
    move = random_agent_move(board)

    # Output move as JSON to stdout
    output = {"move": move}  # move is [row, col]
    print(json.dumps(output))

if __name__ == "__main__":
    main()