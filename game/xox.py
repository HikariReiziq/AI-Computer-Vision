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
            rr -= dr; cc -= dc
        if count >= WIN_LEN:
            return True
    return False

def board_full(board):
    return all(cell != EMPTY for row in board for cell in row)

def input_move(player):
    while True:
        s = input(f"{player} - masukkan baris,kolom (contoh 3,5) atau q untuk keluar: ").strip()
        if s.lower() == "q":
            return None
        if "," in s:
            parts = s.split(",")
            if len(parts) == 2:
                try:
                    r = int(parts[0].strip())
                    c = int(parts[1].strip())
                    return (r, c)
                except:
                    pass
        print("Input tidak valid. Ulangi.")

def main():
    board = create_board()
    players = [("X","Player X"), ("O","Player O")]
    turn = 0
    clear()
    print("XOX 16x16 — Menang: 5 beruntun. Giliran bergantian.")
    while True:
        clear()
        print_board(board)
        symbol, name = players[turn % 2]
        mv = input_move(name)
        if mv is None:
            print("Keluar. Permainan dihentikan.")
            break
        r, c = mv
        if not (0 <= r < SIZE and 0 <= c < SIZE):
            print("Koordinat di luar papan. Tekan Enter untuk lanjut.")
            input()
            continue
        if not valid_move(board, r, c):
            print("Kotak sudah terisi. Tekan Enter untuk lanjut.")
            input()
            continue
        board[r][c] = symbol
        if check_win(board, r, c, symbol):
            clear()
            print_board(board)
            print(f"*** {name} ({symbol}) MENANG! ***")
            break
        if board_full(board):
            clear()
            print_board(board)
            print("*** Seri — papan penuh ***")
            break
        turn += 1


