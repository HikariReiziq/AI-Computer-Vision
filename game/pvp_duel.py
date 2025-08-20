# pvp_duel.py
# Simple PvP turn-based arena with skills, cooldowns, shield, dash, dan fireball.
# Jalankan di terminal: python pvp_duel.py

import random
import os
import time

WIDTH = 9
HEIGHT = 5

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def clamp(v, a, b):
    return max(a, min(b, v))

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

class Player:
    def __init__(self, name, symbol, x, y):
        self.name = name
        self.symbol = symbol
        self.x = x
        self.y = y
        self.max_hp = 120
        self.hp = self.max_hp
        self.base_attack = 12
        # cooldowns stored as {skill_name: remaining_turns}
        self.cooldowns = {"fireball":0, "shield":0, "dash":0, "heal":0}
        # effect flags
        self.shield_active = 0   # remaining turns shield reduces damage by 50%
        self.evade_chance = 0.0  # chance (0..1) to fully evade next incoming attack
        self.stunned = 0         # turns stunned (skip action)
    
    def is_alive(self):
        return self.hp > 0

    def pos(self):
        return (self.x, self.y)
    
    def reduce_cooldowns(self):
        for k in self.cooldowns:
            if self.cooldowns[k] > 0:
                self.cooldowns[k] -= 1
        if self.shield_active > 0:
            self.shield_active -= 1
        if self.stunned > 0:
            self.stunned -= 1

    def take_damage(self, dmg):
        # evade check
        if random.random() < self.evade_chance:
            self.evade_chance = 0.0
            return 0, "evaded"
        self.evade_chance = 0.0
        # shield check
        if self.shield_active > 0:
            dmg = (dmg + 1) // 2  # reduce by 50% (rounded)
        self.hp = max(0, self.hp - dmg)
        return dmg, "hit"

    def basic_attack(self, target):
        # can hit if adjacent (Manhattan distance 1)
        dist = manhattan(self.pos(), target.pos())
        if dist <= 1:
            damage = self.base_attack
            dealt, status = target.take_damage(damage)
            return True, f"{self.name} menyerang {target.name} dan {status} {dealt} dmg."
        else:
            return False, f"Jarak terlalu jauh (jarak {dist}). Basic attack gagal."

    def skill_fireball(self, target):
        # range 3, damage 30, cooldown 3
        if self.cooldowns["fireball"] > 0:
            return False, "Fireball masih cooldown."
        dist = manhattan(self.pos(), target.pos())
        if dist <= 3:
            damage = 30
            dealt, status = target.take_damage(damage)
            self.cooldowns["fireball"] = 3
            return True, f"{self.name} melempar Fireball ke {target.name} dan {status} {dealt} dmg."
        else:
            return False, f"Fireball gagal — target terlalu jauh (jarak {dist})."

    def skill_shield(self):
        # reduce incoming damage by 50% for next turn, cooldown 4
        if self.cooldowns["shield"] > 0:
            return False, "Shield masih cooldown."
        self.shield_active = 1  # aktif selama 1 turn
        self.cooldowns["shield"] = 4
        return True, f"{self.name} mengaktifkan Shield — mengurangi damage 50% selama 1 giliran."

    def skill_dash(self, dx, dy):
        # move up to 2 tiles in chosen direction, gain 50% evade chance for next incoming attack, cooldown 3
        if self.cooldowns["dash"] > 0:
            return False, "Dash masih cooldown."
        nx = clamp(self.x + dx*2, 0, WIDTH-1)
        ny = clamp(self.y + dy*2, 0, HEIGHT-1)
        self.x, self.y = nx, ny
        self.evade_chance = 0.5
        self.cooldowns["dash"] = 3
        return True, f"{self.name} melakukan Dash ke ({self.x},{self.y}) dan mendapatkan 50% chance evade."

    def skill_heal(self):
        # heal 25 HP, cooldown 4
        if self.cooldowns["heal"] > 0:
            return False, "Heal masih cooldown."
        amount = 25
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        healed = self.hp - old_hp
        self.cooldowns["heal"] = 4
        return True, f"{self.name} menggunakan Heal dan memulihkan {healed} HP."

    def status_str(self):
        cd = ", ".join(f"{k}:{v}" for k,v in self.cooldowns.items())
        return f"{self.name} HP:{self.hp}/{self.max_hp} Pos:({self.x},{self.y}) Shield:{self.shield_active} Evade:{int(self.evade_chance*100)}% Cooldowns[{cd}]"

class Game:
    def __init__(self):
        p1 = Player("Player 1", "A", 0, HEIGHT//2)
        p2 = Player("Player 2", "B", WIDTH-1, HEIGHT//2)
        self.players = [p1, p2]
        self.turn = 1

    def draw(self):
        grid = [["." for _ in range(WIDTH)] for __ in range(HEIGHT)]
        for p in self.players:
            if p.is_alive():
                grid[p.y][p.x] = p.symbol
        clear()
        print("=== ARENA ===")
        for row in grid:
            print(" ".join(row))
        print()
        for p in self.players:
            print(p.status_str())
        print("="*20)

    def get_player(self, idx):
        return self.players[idx]

    def input_action(self, p: Player):
        if p.stunned > 0:
            input(f"{p.name} stunned! Tekan Enter untuk skip giliran...")
            return ("skip", None)

        print(f"{p.name}, pilih aksi:")
        print("1) Move (up/down/left/right)")
        print("2) Basic Attack (hanya jarak 1)")
        print("3) Fireball (range 3, dmg 30, cd 3)")
        print("4) Shield (reduce dmg 50% 1 turn, cd 4)")
        print("5) Dash (bergerak 2 tile, 50% evade next hit, cd 3)")
        print("6) Heal (restore 25 HP, cd 4)")
        print("7) Pass")
        choice = input("Masukkan nomor aksi: ").strip()
        if choice == "1":
            dir = input("Arah (w=up, s=down, a=left, d=right): ").strip().lower()
            mapping = {"w":(0,-1),"s":(0,1),"a":(-1,0),"d":(1,0)}
            if dir in mapping:
                dx,dy = mapping[dir]
                nx = clamp(p.x + dx, 0, WIDTH-1)
                ny = clamp(p.y + dy, 0, HEIGHT-1)
                return ("move", (nx,ny))
            else:
                print("Arah tidak valid. Aksi batal.")
                time.sleep(0.8)
                return ("none", None)
        elif choice == "2":
            return ("attack", None)
        elif choice == "3":
            return ("fireball", None)
        elif choice == "4":
            return ("shield", None)
        elif choice == "5":
            dir = input("Arah dash (w=up, s=down, a=left, d=right): ").strip().lower()
            mapping = {"w":(0,-1),"s":(0,1),"a":(-1,0),"d":(1,0)}
            if dir in mapping:
                dx,dy = mapping[dir]
                return ("dash", (dx,dy))
            else:
                print("Arah tidak valid. Aksi batal.")
                time.sleep(0.8)
                return ("none", None)
        elif choice == "6":
            return ("heal", None)
        elif choice == "7":
            return ("pass", None)
        else:
            print("Pilihan tidak valid.")
            time.sleep(0.8)
            return ("none", None)

    def resolve_action(self, actor: Player, action, arg, opponent: Player):
        if action == "move":
            nx, ny = arg
            # cannot move into opponent
            if (nx,ny) == opponent.pos():
                return False, f"Posisi ({nx},{ny}) ditempati lawan. Move dibatalkan."
            actor.x, actor.y = nx, ny
            return True, f"{actor.name} bergerak ke ({nx},{ny})."
        elif action == "attack":
            ok, msg = actor.basic_attack(opponent)
            return ok, msg
        elif action == "fireball":
            ok, msg = actor.skill_fireball(opponent)
            return ok, msg
        elif action == "shield":
            ok, msg = actor.skill_shield()
            return ok, msg
        elif action == "dash":
            dx,dy = arg
            ok, msg = actor.skill_dash(dx,dy)
            # prevent dash into opponent tile: if collided, push back to adjacent tile
            if ok and actor.pos() == opponent.pos():
                # push back one tile along direction (reverse)
                actor.x = clamp(actor.x - dx, 0, WIDTH-1)
                actor.y = clamp(actor.y - dy, 0, HEIGHT-1)
                msg += " (collision -> repositioned)."
            return ok, msg
        elif action == "heal":
            ok, msg = actor.skill_heal()
            return ok, msg
        elif action == "pass" or action == "skip":
            return True, f"{actor.name} melewatkan giliran."
        elif action == "none":
            return False, "Tidak ada aksi dilakukan."
        else:
            return False, "Aksi tidak dikenali."

    def run(self):
        while all(p.is_alive() for p in self.players):
            self.draw()
            print(f"-- Turn {self.turn} --")
            # Player 1 then Player 2
            for i in range(2):
                actor = self.get_player(i)
                opponent = self.get_player(1-i)
                if not actor.is_alive():
                    continue
                # show small summary before action
                print()
                print(f"{actor.name} giliran.")
                action, arg = self.input_action(actor)
                ok, msg = self.resolve_action(actor, action, arg, opponent)
                print(msg)
                # check immediate death
                if not opponent.is_alive():
                    break
                # short pause
                time.sleep(0.6)
            # after both acted, reduce cooldowns/effects
            for p in self.players:
                p.reduce_cooldowns()
            self.turn += 1
        # someone died
        self.draw()
        p1, p2 = self.players
        if p1.is_alive() and not p2.is_alive():
            print(">>> Player 1 MENANG! 🎉")
        elif p2.is_alive() and not p1.is_alive():
            print(">>> Player 2 MENANG! 🎉")
        else:
            print(">>> Seri! Keduanya tumbang bersamaan.")
        print("Terima kasih sudah bermain.")

if __name__ == "__main__":
    game = Game()
    game.run()
