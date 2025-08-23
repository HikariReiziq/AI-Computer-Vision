# xox_16x16_gui_ai.py
# XOX 16x16 GUI clickable (Gomoku-like, win = 5 in a row)
# Menambahkan mode melawan AI dengan dua level: Easy (random) dan Hard (heuristic: immediate win/block + scoring)
# Jalankan: python xox_16x16_gui_ai.py

import pygame
import sys
import random

# --- konfigurasi ---
SIZE = 16        # ukuran papan (16x16)
WIN_LEN = 5      # panjang beruntun untuk menang
CELL = 40        # ukuran tiap kotak dalam pixel
MARGIN = 10      # margin di sekeliling grid
UI_HEIGHT = 110  # ruang bawah untuk tombol/status (lebih tinggi agar ada instruksi)

GRID_W = CELL * SIZE
GRID_H = CELL * SIZE
WIN_W = GRID_W + MARGIN * 2
WIN_H = GRID_H + MARGIN * 2 + UI_HEIGHT

FPS = 60

# warna
WHITE = (250,250,250)
BLACK = (20,20,20)
GRAY = (220,220,220)
LINE_COL = (40,40,40)
X_COL = (45,125,220)
O_COL = (220,60,60)
HIGHLIGHT = (255, 215, 0, 160)  # gold semi-transparent
SELECT_BG = (200, 230, 255)

pygame.init()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("XOX 16x16 - Klik untuk main (Menang: 5 beruntun) + AI")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 36)

# papan: matrix SIZE x SIZE, values: '.', 'X', 'O'
EMPTY = '.'

def create_board():
    return [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

board = create_board()
turn_X = True   # True = X, False = O
game_over = False
winner = None
winning_cells = []  # list of (r,c) to highlight

# tombol restart
restart_rect = pygame.Rect(MARGIN, GRID_H + MARGIN*2 + 6, 120, 36)

# AI settings
vs_ai = False
ai_symbol = 'O'  # AI plays O by default; human X
ai_difficulty = 'hard'  # 'easy' or 'hard'

# --- helper functions ---

def draw_grid():
    # background
    screen.fill(WHITE)
    # grid background rect
    grid_rect = pygame.Rect(MARGIN, MARGIN, GRID_W, GRID_H)
    pygame.draw.rect(screen, GRAY, grid_rect)
    # lines
    for i in range(SIZE + 1):
        # vertical
        x = MARGIN + i * CELL
        pygame.draw.line(screen, LINE_COL, (x, MARGIN), (x, MARGIN + GRID_H))
        # horizontal
        y = MARGIN + i * CELL
        pygame.draw.line(screen, LINE_COL, (MARGIN, y), (MARGIN + GRID_W, y))

def draw_pieces():
    for r in range(SIZE):
        for c in range(SIZE):
            val = board[r][c]
            if val == EMPTY:
                continue
            cx = MARGIN + c * CELL + CELL // 2
            cy = MARGIN + r * CELL + CELL // 2
            if val == 'X':
                offset = int(CELL*0.28)
                pygame.draw.line(screen, X_COL, (cx - offset, cy - offset), (cx + offset, cy + offset), 3)
                pygame.draw.line(screen, X_COL, (cx - offset, cy + offset), (cx + offset, cy - offset), 3)
            else:
                radius = int(CELL*0.32)
                pygame.draw.circle(screen, O_COL, (cx, cy), radius, 3)

def highlight_win(cells):
    if not cells:
        return
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    surf.fill(HIGHLIGHT)
    for (r,c) in cells:
        x = MARGIN + c * CELL
        y = MARGIN + r * CELL
        screen.blit(surf, (x, y))
    draw_pieces()

def check_win_at(r, c, sym):
    # returns list of winning cells if win found using (r,c) as last move, else []
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        cells = [(r,c)]
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            cells.append((rr,cc))
            rr += dr; cc += dc
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            cells.insert(0,(rr,cc))
            rr -= dr; cc -= dc
        if len(cells) >= WIN_LEN:
            return cells
    return []

def board_full():
    for row in board:
        for cell in row:
            if cell == EMPTY:
                return False
    return True

def reset_game():
    global board, turn_X, game_over, winner, winning_cells
    board = create_board()
    turn_X = True
    game_over = False
    winner = None
    winning_cells = []

# --- AI implementation ---

def immediate_win_block(sym):
    # if exists a move for sym that wins immediately return that move
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != EMPTY:
                continue
            board[r][c] = sym
            cells = check_win_at(r,c,sym)
            board[r][c] = EMPTY
            if cells:
                return (r,c)
    return None

def score_position(r, c, sym):
    # simple heuristic: sum max contiguous lengths in 4 directions for sym
    score = 0
    opp = 'X' if sym == 'O' else 'O'
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        count = 1
        # forward
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            count += 1
            rr += dr; cc += dc
        # backward
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            count += 1
            rr -= dr; cc -= dc
        # weighted: longer contiguous is exponentially better
        score += (10 ** (count if count<=6 else 6))
        # small penalty if move gives opponent big threat (adjacent opp pieces)
        opp_count = 0
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == opp:
            opp_count += 1
            rr += dr; cc += dc
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == opp:
            opp_count += 1
            rr -= dr; cc -= dc
        if opp_count >= WIN_LEN-1:
            score -= 10**6
    return score


def ai_choose_move(sym, difficulty='hard'):
    # Easy: random available
    empties = [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == EMPTY]
    if not empties:
        return None
    if difficulty == 'easy':
        return random.choice(empties)
    # Hard: immediate win, block opponent immediate win, then heuristic scoring
    # 1) immediate win for AI
    win_move = immediate_win_block(sym)
    if win_move:
        return win_move
    # 2) block opponent immediate win
    opp = 'X' if sym == 'O' else 'O'
    block = immediate_win_block(opp)
    if block:
        return block
    # 3) heuristic: compute scores and pick best (random tie-break)
    best_score = None
    best_moves = []
    for (r,c) in empties:
        s = score_position(r,c,sym)
        # also prefer center-ish positions slightly
        center_bonus = - (abs(r - SIZE//2) + abs(c - SIZE//2))
        s += center_bonus
        if best_score is None or s > best_score:
            best_score = s
            best_moves = [(r,c)]
        elif s == best_score:
            best_moves.append((r,c))
    return random.choice(best_moves)

# --- UI drawing ---

def draw_ui():
    ui_rect = pygame.Rect(0, GRID_H + MARGIN, WIN_W, UI_HEIGHT + MARGIN)
    pygame.draw.rect(screen, WHITE, ui_rect)
    # restart button
    pygame.draw.rect(screen, (180,180,180), restart_rect)
    txt = font.render("Restart (R)", True, BLACK)
    screen.blit(txt, (restart_rect.x + 12, restart_rect.y + 10))
    # mode button/text
    mode_txt = "Mode: vs AI" if vs_ai else "Mode: 2-Player"
    mode_surf = font.render(mode_txt + " (M to toggle)", True, BLACK)
    screen.blit(mode_surf, (restart_rect.right + 16, restart_rect.y + 8))
    diff_surf = font.render(f"AI difficulty: {ai_difficulty} (1=easy,2=hard)", True, BLACK)
    screen.blit(diff_surf, (restart_rect.right + 16, restart_rect.y + 32))
    # status text
    if game_over:
        status = f"Game over! Pemenang: {winner}" if winner else "Game over! Seri"
    else:
        status = "Giliran: X" if turn_X else "Giliran: O"
        if vs_ai and not turn_X and ai_symbol == 'O':
            status += " (AI thinking...)"
        if vs_ai and turn_X and ai_symbol == 'X':
            status += " (AI thinking...)"
    status_surf = big_font.render(status, True, BLACK)
    screen.blit(status_surf, (MARGIN, restart_rect.bottom + 6))
    ins = font.render("Klik kotak untuk tempatkan simbol. Tekan Q untuk keluar.", True, BLACK)
    screen.blit(ins, (restart_rect.right + 16, restart_rect.y + 56))

# --- main loop ---
running = True
ai_next_move_delay = 400  # ms delay to simulate thinking
ai_timer = 0

while running:
    dt = clock.tick(FPS)
    ai_timer += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
                break
            if event.key == pygame.K_r:
                reset_game()
            if event.key == pygame.K_m:
                vs_ai = not vs_ai
                reset_game()
            if event.key == pygame.K_1:
                ai_difficulty = 'easy'
            if event.key == pygame.K_2:
                ai_difficulty = 'hard'
            if event.key == pygame.K_c:
                # toggle which symbol AI uses (X or O)
                if vs_ai:
                    ai_symbol = 'X' if ai_symbol == 'O' else 'O'
                    reset_game()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if restart_rect.collidepoint(mx, my):
                reset_game()
                continue
            if MARGIN <= mx < MARGIN + GRID_W and MARGIN <= my < MARGIN + GRID_H and not game_over:
                c = (mx - MARGIN) // CELL
                r = (my - MARGIN) // CELL
                if 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == EMPTY:
                    # if playing vs AI ensure human can only play when it's their turn
                    current_sym = 'X' if turn_X else 'O'
                    human_turn = True
                    if vs_ai and current_sym == ai_symbol:
                        human_turn = False
                    if human_turn:
                        board[r][c] = current_sym
                        cells = check_win_at(r, c, board[r][c])
                        if cells:
                            game_over = True
                            winner = board[r][c]
                            winning_cells = cells
                        else:
                            if board_full():
                                game_over = True
                                winner = None
                                winning_cells = []
                            else:
                                turn_X = not turn_X
                                ai_timer = 0

    # AI move handling
    if vs_ai and not game_over:
        current_sym = 'X' if turn_X else 'O'
        if current_sym == ai_symbol:
            # AI's turn and enough thinking delay passed
            if ai_timer >= ai_next_move_delay:
                move = ai_choose_move(ai_symbol, difficulty=ai_difficulty)
                if move:
                    r,c = move
                    board[r][c] = ai_symbol
                    cells = check_win_at(r,c,ai_symbol)
                    if cells:
                        game_over = True
                        winner = ai_symbol
                        winning_cells = cells
                    else:
                        if board_full():
                            game_over = True
                            winner = None
                            winning_cells = []
                        else:
                            turn_X = not turn_X
                ai_timer = 0

    # draw
    draw_grid()
    if winning_cells:
        highlight_win(winning_cells)
    else:
        draw_pieces()
    draw_pieces()
    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()
