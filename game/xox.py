# xox_16x16_gui_ai.py
# Modernized XOX 16x16 GUI (Gomoku-like) dengan AI
# Perbaikan terakhir: tambahkan skor khusus untuk setiap 5-in-a-row window
# (setiap window 5 berurutan pada garis memberi 1 poin pada pemain yang memilikinya).
# Triple (3-in-row) skor tetap terpisah. Semua window distinct dihitung.
# Jalankan: python xox_16x16_gui_ai.py

import pygame
import sys
import random
from itertools import product

# --- konfigurasi ---
SIZE = 16        # ukuran papan (16x16)
WIN_LEN = 5      # panjang beruntun untuk "5-win"
TRIPLE_LEN = 3   # panjang yang dihitung untuk skor
CELL = 44        # ukuran tiap kotak dalam pixel
MARGIN = 18      # margin di sekeliling grid
UI_HEIGHT = 160  # ruang bawah untuk tombol/status

GRID_W = CELL * SIZE
GRID_H = CELL * SIZE
WIN_W = GRID_W + MARGIN * 2
WIN_H = GRID_H + MARGIN * 2 + UI_HEIGHT

FPS = 60

# warna modern
BG_TOP = (24, 30, 54)
BG_BOTTOM = (18, 143, 155)
BOARD_BG = (245, 247, 250)
LINE_COL = (200, 210, 218)
CELL_HOVER = (231, 245, 255)
X_COL = (45,125,220)
O_COL = (220,60,60)
ACCENT = (255, 183, 77)
BUTTON_BG = (34, 40, 49)
BUTTON_HOVER = (58, 66, 81)
TEXT = (20,20,20)
WHITE = (255,255,255)

# highlight colors for 5-in-a-row windows
HIGHLIGHT_X = (100,170,255,140)
HIGHLIGHT_O = (255,150,150,140)

pygame.init()
# fonts
try:
    font = pygame.font.SysFont('Segoe UI', 16)
    big_font = pygame.font.SysFont('Segoe UI', 24)
except:
    font = pygame.font.SysFont(None, 16)
    big_font = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("XOX 16x16 — Modern GUI + AI + 5-in-row scoring")
clock = pygame.time.Clock()

# papan: matrix SIZE x SIZE, values: '.', 'X', 'O'
EMPTY = '.'

def create_board():
    return [[EMPTY for _ in range(SIZE)] for __ in range(SIZE)]

board = create_board()
turn_X = True   # True = X, False = O

# score tracking: count distinct triples per player and count distinct fives per player
score_triple_X = 0
score_triple_O = 0
score_five_X = 0
score_five_O = 0
tracked_triples_X = set()
tracked_triples_O = set()
tracked_fives_X = set()
tracked_fives_O = set()

# track first 5-in-row occurrence for info
first_five_symbol = None
first_five_cells = []

# UI elements
restart_rect = pygame.Rect(MARGIN, GRID_H + MARGIN*2 + 14, 140, 40)
mode_rect = pygame.Rect(restart_rect.right + 14, restart_rect.y, 160, 40)
diff_rect = pygame.Rect(mode_rect.right + 12, restart_rect.y, 160, 40)
continue_rect = pygame.Rect(diff_rect.right + 12, restart_rect.y, 160, 40)

# AI settings
vs_ai = True
ai_symbol = 'O'  # AI plays O by default; human X
ai_difficulty = 'hard'  # 'easy' or 'hard'

# AI timing
ai_think_delay = 350
ai_timer = 0

# helper: draw rounded rect
def draw_round_rect(surface, rect, color, radius=8, width=0):
    pygame.draw.rect(surface, color, rect, border_radius=radius, width=width)

# background gradient
def draw_gradient_background():
    for i in range(WIN_H):
        t = i / WIN_H
        r = int(BG_TOP[0] * (1-t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1-t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1-t) + BG_BOTTOM[2] * t)
        pygame.draw.line(screen, (r,g,b), (0,i), (WIN_W,i))

# draw board panel and grid
def draw_board_panel():
    panel = pygame.Rect(MARGIN-6, MARGIN-6, GRID_W+12, GRID_H+12)
    draw_round_rect(screen, panel, WHITE, radius=12)
    inner = pygame.Rect(MARGIN, MARGIN, GRID_W, GRID_H)
    pygame.draw.rect(screen, BOARD_BG, inner, border_radius=8)
    for i in range(1, SIZE):
        x = MARGIN + i * CELL
        pygame.draw.line(screen, LINE_COL, (x, MARGIN+6), (x, MARGIN + GRID_H-6), 1)
    for i in range(1, SIZE):
        y = MARGIN + i * CELL
        pygame.draw.line(screen, LINE_COL, (MARGIN+6, y), (MARGIN + GRID_W-6, y), 1)

# draw X/O pieces
shadow_offset = 2

def draw_pieces():
    for r in range(SIZE):
        for c in range(SIZE):
            val = board[r][c]
            if val == EMPTY:
                continue
            cx = MARGIN + c * CELL + CELL // 2
            cy = MARGIN + r * CELL + CELL // 2
            if val == 'X':
                offset = int(CELL*0.32)
                pygame.draw.line(screen, (0,0,0,30), (cx - offset + shadow_offset, cy - offset + shadow_offset), (cx + offset + shadow_offset, cy + offset + shadow_offset), 4)
                pygame.draw.line(screen, (0,0,0,30), (cx - offset + shadow_offset, cy + offset + shadow_offset), (cx + offset + shadow_offset, cy - offset + shadow_offset), 4)
                pygame.draw.line(screen, X_COL, (cx - offset, cy - offset), (cx + offset, cy + offset), 4)
                pygame.draw.line(screen, X_COL, (cx - offset, cy + offset), (cx + offset, cy - offset), 4)
            else:
                radius = int(CELL*0.36)
                pygame.draw.circle(screen, (0,0,0,30), (cx+shadow_offset, cy+shadow_offset), radius, 0)
                pygame.draw.circle(screen, O_COL, (cx, cy), radius, 4)

# highlight a set of cells (iterable of (r,c))
def highlight_cells(cells, color=(255,220,120,120)):
    if not cells:
        return
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    surf.fill(color)
    for (r,c) in cells:
        x = MARGIN + c * CELL
        y = MARGIN + r * CELL
        screen.blit(surf, (x, y))

# scan all distinct contiguous windows of length L for symbol sym

def find_all_windows_of_length(L, sym):
    found = set()
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr,dc in directions:
        for r in range(SIZE):
            for c in range(SIZE):
                cells = []
                ok = True
                for i in range(L):
                    rr = r + i*dr
                    cc = c + i*dc
                    if not (0 <= rr < SIZE and 0 <= cc < SIZE):
                        ok = False
                        break
                    if board[rr][cc] != sym:
                        ok = False
                        break
                    cells.append((rr,cc))
                if ok:
                    found.add(frozenset(cells))
    return found

# update scores globally after a move by scanning entire board for triples and fives

def update_scores_global():
    global score_triple_X, score_triple_O, score_five_X, score_five_O
    global tracked_triples_X, tracked_triples_O, tracked_fives_X, tracked_fives_O
    # triples
    found_X_triples = find_all_windows_of_length(TRIPLE_LEN, 'X')
    for t in found_X_triples:
        if t not in tracked_triples_X:
            tracked_triples_X.add(t)
            score_triple_X += 1
    found_O_triples = find_all_windows_of_length(TRIPLE_LEN, 'O')
    for t in found_O_triples:
        if t not in tracked_triples_O:
            tracked_triples_O.add(t)
            score_triple_O += 1
    # fives (windows of length WIN_LEN) -> count each distinct window as 1 point
    found_X_fives = find_all_windows_of_length(WIN_LEN, 'X')
    for fset in found_X_fives:
        if fset not in tracked_fives_X:
            tracked_fives_X.add(fset)
            score_five_X += 1
    found_O_fives = find_all_windows_of_length(WIN_LEN, 'O')
    for fset in found_O_fives:
        if fset not in tracked_fives_O:
            tracked_fives_O.add(fset)
            score_five_O += 1

# immediate five detection for highlighting first occurrence

def check_five_at(r, c, sym):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr,dc in directions:
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

# board full check

def board_full():
    for row in board:
        for cell in row:
            if cell == EMPTY:
                return False
    return True

# AI implementation (immediate win/block + heuristic)

def immediate_win_block(sym):
    for r,c in product(range(SIZE), range(SIZE)):
        if board[r][c] != EMPTY:
            continue
        board[r][c] = sym
        cells = check_five_at(r,c,sym)
        board[r][c] = EMPTY
        if cells:
            return (r,c)
    return None


def score_position(r, c, sym):
    score = 0
    opp = 'X' if sym == 'O' else 'O'
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        count = 1
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            count += 1
            rr += dr; cc += dc
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            count += 1
            rr -= dr; cc -= dc
        score += (10 ** (count if count<=6 else 6))
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
    empties = [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == EMPTY]
    if not empties:
        return None
    if difficulty == 'easy':
        return random.choice(empties)
    win_move = immediate_win_block(sym)
    if win_move:
        return win_move
    opp = 'X' if sym == 'O' else 'O'
    block = immediate_win_block(opp)
    if block:
        return block
    best_score = None
    best_moves = []
    for (r,c) in empties:
        s = score_position(r,c,sym)
        center_bonus = - (abs(r - SIZE//2) + abs(c - SIZE//2))
        s += center_bonus
        if best_score is None or s > best_score:
            best_score = s
            best_moves = [(r,c)]
        elif s == best_score:
            best_moves.append((r,c))
    return random.choice(best_moves)

# UI drawing: buttons, info panel, hover cell highlight

def draw_ui():
    ui_panel = pygame.Rect(MARGIN-6, GRID_H + MARGIN - 2, GRID_W+12, UI_HEIGHT+8)
    draw_round_rect(screen, ui_panel, (255,255,255,40), radius=12)
    mx, my = pygame.mouse.get_pos()
    restart_hover = restart_rect.collidepoint(mx,my)
    draw_round_rect(screen, restart_rect, BUTTON_HOVER if restart_hover else BUTTON_BG, radius=10)
    t = font.render('Restart (R)', True, WHITE)
    screen.blit(t, (restart_rect.x + 14, restart_rect.y + 10))
    mode_hover = mode_rect.collidepoint(mx,my)
    draw_round_rect(screen, mode_rect, BUTTON_HOVER if mode_hover else BUTTON_BG, radius=10)
    mode_label = 'Mode: vs AI' if vs_ai else 'Mode: 2-Player'
    t2 = font.render(mode_label + ' (M)', True, WHITE)
    screen.blit(t2, (mode_rect.x + 14, mode_rect.y + 10))
    diff_hover = diff_rect.collidepoint(mx,my)
    draw_round_rect(screen, diff_rect, BUTTON_HOVER if diff_hover else BUTTON_BG, radius=10)
    diff_label = f'AI: {ai_difficulty.title()} (1/2)'
    t3 = font.render(diff_label, True, WHITE)
    screen.blit(t3, (diff_rect.x + 14, diff_rect.y + 10))
    cont_hover = continue_rect.collidepoint(mx,my)
    draw_round_rect(screen, continue_rect, BUTTON_HOVER if cont_hover else BUTTON_BG, radius=10)
    cont_label = 'Play until full'
    t4 = font.render(cont_label, True, WHITE)
    screen.blit(t4, (continue_rect.x + 14, continue_rect.y + 10))

    left_x = MARGIN
    status_y = restart_rect.bottom + 8
    turn_label = 'Turn: X' if turn_X else 'Turn: O'
    tturn = big_font.render(turn_label, True, WHITE)
    screen.blit(tturn, (left_x, status_y))

    # show both triple and five scores
    score_s = font.render(f'3-in-row - X: {score_triple_X}   O: {score_triple_O}', True, WHITE)
    screen.blit(score_s, (left_x, status_y + 36))
    score_f = font.render(f'5-in-row - X: {score_five_X}   O: {score_five_O}', True, WHITE)
    screen.blit(score_f, (left_x, status_y + 60))

    info_x = WIN_W - 420
    if first_five_symbol:
        info = big_font.render(f'First 5-in-row: {first_five_symbol}', True, ACCENT)
        screen.blit(info, (info_x, status_y))
    else:
        info = font.render('No 5-in-row yet. Game continues until board full.', True, WHITE)
        screen.blit(info, (info_x, status_y + 6))

    hint = font.render('Click a cell to place piece. R restart. M toggle mode. 1/2 difficulty. C change AI symbol.', True, WHITE)
    screen.blit(hint, (left_x, status_y + 96))

# reset function

def reset_game():
    global board, turn_X, score_triple_X, score_triple_O, score_five_X, score_five_O
    global tracked_triples_X, tracked_triples_O, tracked_fives_X, tracked_fives_O
    global first_five_symbol, first_five_cells, ai_timer
    board = create_board()
    turn_X = True
    score_triple_X = 0
    score_triple_O = 0
    score_five_X = 0
    score_five_O = 0
    tracked_triples_X = set()
    tracked_triples_O = set()
    tracked_fives_X = set()
    tracked_fives_O = set()
    first_five_symbol = None
    first_five_cells = []
    ai_timer = 0

# handle placing a move at r,c for current symbol

def place_move(r, c, sym):
    global turn_X, first_five_symbol, first_five_cells
    board[r][c] = sym
    # update scores globally (scan all triples & fives)
    update_scores_global()
    # record first 5-in-a-row cells (for info) if not recorded yet
    if not first_five_symbol:
        cells5 = check_five_at(r, c, sym)
        if cells5:
            first_five_symbol = sym
            first_five_cells = cells5
    # advance turn
    turn_X = not turn_X

# main loop
running = True
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
                if vs_ai:
                    ai_symbol = 'X' if ai_symbol == 'O' else 'O'
                    reset_game()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if restart_rect.collidepoint(mx, my):
                reset_game()
                continue
            if mode_rect.collidepoint(mx, my):
                vs_ai = not vs_ai
                reset_game()
                continue
            if diff_rect.collidepoint(mx, my):
                ai_difficulty = 'easy' if ai_difficulty == 'hard' else 'hard'
                continue
            # click grid
            if MARGIN <= mx < MARGIN + GRID_W and MARGIN <= my < MARGIN + GRID_H:
                c = (mx - MARGIN) // CELL
                r = (my - MARGIN) // CELL
                if 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == EMPTY:
                    current_sym = 'X' if turn_X else 'O'
                    human_turn = True
                    if vs_ai and current_sym == ai_symbol:
                        human_turn = False
                    if human_turn:
                        place_move(r, c, current_sym)
                        ai_timer = 0

    # AI move
    if vs_ai:
        current_sym = 'X' if turn_X else 'O'
        if current_sym == ai_symbol:
            if ai_timer >= ai_think_delay:
                mv = ai_choose_move(ai_symbol, difficulty=ai_difficulty)
                if mv:
                    r,c = mv
                    place_move(r,c,ai_symbol)
                ai_timer = 0

    # draw everything
    draw_gradient_background()
    draw_board_panel()
    # hover cell
    mx, my = pygame.mouse.get_pos()
    if MARGIN <= mx < MARGIN + GRID_W and MARGIN <= my < MARGIN + GRID_H:
        c_hover = (mx - MARGIN) // CELL
        r_hover = (my - MARGIN) // CELL
        if 0 <= r_hover < SIZE and 0 <= c_hover < SIZE and board[r_hover][c_hover] == EMPTY:
            surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            surf.fill((*CELL_HOVER, 180))
            screen.blit(surf, (MARGIN + c_hover*CELL, MARGIN + r_hover*CELL))

    # highlight ALL current 5-in-row windows for both players
    current_X_fives = find_all_windows_of_length(WIN_LEN, 'X')
    current_O_fives = find_all_windows_of_length(WIN_LEN, 'O')
    # highlight O first (red), then X (blue) so X highlight sits on top if overlapping
    for f in current_O_fives:
        highlight_cells(list(f), color=HIGHLIGHT_O)
    for f in current_X_fives:
        highlight_cells(list(f), color=HIGHLIGHT_X)

    # also highlight first found 5-in-a-row (kept as accent)
    if first_five_cells:
        highlight_cells(first_five_cells, color=(255,200,120,120))

    draw_pieces()
    draw_ui()

    # if board full: show final summary pop-up (overlay)
    if board_full():
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((10,10,10,200))
        screen.blit(overlay, (0,0))
        # summary box
        box = pygame.Rect(WIN_W//2 - 320, WIN_H//2 - 140, 640, 280)
        draw_round_rect(screen, box, (255,255,255), radius=12)
        title = big_font.render('Game Complete — Final Scores', True, TEXT)
        screen.blit(title, (box.x + 20, box.y + 20))
        stext = font.render(f'X 3-in-row count: {score_X}', True, TEXT)
        screen.blit(stext, (box.x + 20, box.y + 80))
        stext2 = font.render(f'O 3-in-row count: {score_O}', True, TEXT)
        screen.blit(stext2, (box.x + 20, box.y + 110))
        if first_five_found:
            fw = font.render(f'First 5-in-row by: {"X" if first_five_found=="X" else "O"}', True, ACCENT)
            screen.blit(fw, (box.x + 20, box.y + 150))
        # declare score winner
        if score_X > score_O:
            result = 'Winner by score: X'
        elif score_O > score_X:
            result = 'Winner by score: O'
        else:
            result = 'Score tied'
        res = big_font.render(result, True, ACCENT)
        screen.blit(res, (box.x + 20, box.y + 190))
        info = font.render('Press R to restart or Q to quit.', True, TEXT)
        screen.blit(info, (box.x + 20, box.y + 230))

    pygame.display.flip()

pygame.quit()
sys.exit()
