# xox_16x16_gui.py
# XOX 16x16 GUI clickable (Gomoku-like, win = 5 in a row)
import pygame
import sys

# --- konfigurasi ---
SIZE = 16        # ukuran papan (16x16)
WIN_LEN = 5      # panjang beruntun untuk menang
CELL = 40        # ukuran tiap kotak dalam pixel
MARGIN = 10      # margin di sekeliling grid
UI_HEIGHT = 80   # ruang bawah untuk tombol/status

GRID_W = CELL * SIZE
GRID_H = CELL * SIZE
WIN_W = GRID_W + MARGIN * 2
WIN_H = GRID_H + MARGIN * 2 + UI_HEIGHT

FPS = 60

# warna
WHITE = (250,250,250)
BLACK = (20,20,20)
GRAY = (200,200,200)
LINE_COL = (40,40,40)
X_COL = (45,125,220)
O_COL = (220,60,60)
HIGHLIGHT = (255, 215, 0, 160)  # gold semi-transparent

pygame.init()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("XOX 16x16 - Klik untuk main (Menang: 5 beruntun)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

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
restart_rect = pygame.Rect(MARGIN, GRID_H + MARGIN*2, 120, 40)

def draw_grid():
    # background
    screen.fill(WHITE)
    # grid background rect
    grid_rect = pygame.Rect(MARGIN, MARGIN, GRID_W, GRID_H)
    pygame.draw.rect(screen, GRAY, grid_rect)
    # lines
    for i in range(SIZE + 1):
        # vertical lines
        x = MARGIN + i * CELL
        pygame.draw.line(screen, LINE_COL, (x, MARGIN), (x, MARGIN + GRID_H))
        # horizontal lines
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
                # draw X as two lines
                offset = int(CELL*0.28)
                pygame.draw.line(screen, X_COL, (cx - offset, cy - offset), (cx + offset, cy + offset), 3)
                pygame.draw.line(screen, X_COL, (cx - offset, cy + offset), (cx + offset, cy - offset), 3)
            else:
                # draw O as circle
                radius = int(CELL*0.32)
                pygame.draw.circle(screen, O_COL, (cx, cy), radius, 3)

def highlight_win(cells):
    if not cells:
        return
    # create semi-transparent surface
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    surf.fill(HIGHLIGHT)
    for (r,c) in cells:
        x = MARGIN + c * CELL
        y = MARGIN + r * CELL
        screen.blit(surf, (x, y))
    # redraw pieces on top
    draw_pieces()

def check_win_at(r, c, sym):
    # returns list of winning cells if win found using (r,c) as last move, else []
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dr, dc in directions:
        cells = [(r,c)]
        # forward
        rr, cc = r+dr, c+dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            cells.append((rr,cc))
            rr += dr; cc += dc
        # backward
        rr, cc = r-dr, c-dc
        while 0 <= rr < SIZE and 0 <= cc < SIZE and board[rr][cc] == sym:
            cells.insert(0,(rr,cc))
            rr -= dr; cc -= dc
        if len(cells) >= WIN_LEN:
            # if longer than WIN_LEN, we can choose contiguous WIN_LEN inside the list that includes (r,c)
            # but simplest: take the whole contiguous segment
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

def draw_ui():
    # bottom UI rect
    ui_rect = pygame.Rect(0, GRID_H + MARGIN, WIN_W, UI_HEIGHT + MARGIN)
    pygame.draw.rect(screen, WHITE, ui_rect)
    # restart button
    pygame.draw.rect(screen, (180,180,180), restart_rect)
    txt = font.render("Restart (R)", True, BLACK)
    screen.blit(txt, (restart_rect.x + 10, restart_rect.y + 10))
    # status text
    if game_over:
        status = f"Game over! Pemenang: {winner}" if winner else "Game over! Seri"
    else:
        status = "Giliran: X" if turn_X else "Giliran: O"
    status_surf = big_font.render(status, True, BLACK)
    screen.blit(status_surf, (restart_rect.right + 20, restart_rect.y + 4))
    # instruction
    ins = font.render("Klik kotak untuk tempatkan simbol. Tekan Q untuk keluar.", True, BLACK)
    screen.blit(ins, (restart_rect.right + 20, restart_rect.y + 40))

# main loop
running = True
while running:
    clock.tick(FPS)
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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # click restart?
            if restart_rect.collidepoint(mx, my):
                reset_game()
                continue
            # click inside grid?
            if MARGIN <= mx < MARGIN + GRID_W and MARGIN <= my < MARGIN + GRID_H and not game_over:
                c = (mx - MARGIN) // CELL
                r = (my - MARGIN) // CELL
                if 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == EMPTY:
                    board[r][c] = 'X' if turn_X else 'O'
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

    # draw everything
    draw_grid()
    # highlight before pieces so highlight under them (we later redraw pieces on top)
    if winning_cells:
        highlight_win(winning_cells)
    else:
        draw_pieces()
    draw_pieces()  # ensure pieces are on top
    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()
