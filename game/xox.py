# xox_16x16.py
# Tic-tac-toe pada papan 16x16, kemenangan = 5 beruntun.
import os

SIZE = 16
WIN_LEN = 5
EMPTY = "."

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def create_board():
    return [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

def print_board(board):
    # header
    header = "   " + " ".join(f"{i:2d}" for i in range(SIZE))
    print(header)
    for r in range(SIZE):
        row_str = " ".join(f"{cell:2s}" for cell in board[r])
        print(f"{r:2d} {row_str}")

def valid_move(board, r, c):
    return 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == EMPTY

def check_win(board, r, c, symbol):
    # check 4 directions (horizontal, vertical, diag \, diag /)
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for dr, dc in directions:
        count = 1
        # forward
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == symbol:
            count += 1
            rr += dr; cc += dc
        # backward
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == symbol:
            count += 1
