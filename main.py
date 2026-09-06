"""手势切水果 —— 基于摄像头手部追踪的体感小游戏。

运行:  python main.py
操作:  菜单/结算界面 挥动食指 或按 空格 开始；R 重开；ESC 退出
"""

import math
import os
import random
import sys
import time

import cv2
import pygame

from blade import Blade, seg_point_dist
from config import (
    BOMB_BASE_P, BOMB_MAX_P, BOMB_P_PER_SCORE, BLADE_TIP_RADIUS, CAMERA_INDEX,
    COMBO_BONUS_MIN, FPS, LIVES, SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_START,
    WAVE_SIZE, WINDOW_H, WINDOW_W,
)
from entities import Bomb, Fruit, HalfFruit, Particle, Popup
from hand_tracker import HandTracker

os.environ.setdefault("SDL_VIDEO_CENTERED", "1")


def load_font(size):
    """优先加载中文字体（macOS 内置），失败则退回 pygame 默认字体。"""
    for name in ("pingfangsc", "hiraginosansgb", "heiti", "stheiti",
                 "arialunicodems", "simhei"):
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def draw_heart(surf, cx, cy, size, color):
    """参数方程画一颗心。"""
    pts = []
    for i in range(0, 630, 15):
        t = math.radians(i / 10)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * size / 16, cy - y * size / 16))
    pygame.draw.polygon(surf, color, pts)


class Game:
    MENU, PLAYING, OVER = range(3)

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("手势切水果")
        self.clock = pygame.time.Clock()
        self.font_big = load_font(60)
        self.font_mid = load_font(34)
        self.font_small = load_font(22)
        self.tracker = HandTracker(CAMERA_INDEX, (WINDOW_W, WINDOW_H))
        self.blade = Blade()
        self.best = 0
        self.bg = None
        # 每帧复用的覆盖层
        self.tint = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.tint.fill((0, 0, 0, 55))
        self.dim = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.flash_surf = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.state = self.MENU
        self.reset()

    def reset(self):
        self.fruits, self.bombs, self.halves = [], [], []
        self.particles, self.popups = [], []
        self.score = 0
        self.lives = LIVES
        self.spawn_timer = 0.9
        self.flash = 0.0
        self.over_since = 0.0

    # ---------- 生成与判定 ----------

    def spawn_wave(self):
        bomb_p = min(BOMB_BASE_P + self.score * BOMB_P_PER_SCORE, BOMB_MAX_P)
        n_max = min(WAVE_SIZE[1], 2 + self.score // 12)
        for _ in range(random.randint(WAVE_SIZE[0], n_max)):
            x = random.uniform(WINDOW_W * 0.15, WINDOW_W * 0.85)
            if random.random() < bomb_p:
                self.bombs.append(Bomb(x, WINDOW_H + 60))
            else:
                self.fruits.append(Fruit(x, WINDOW_H + 60))

    def split_fruit(self, fruit, seg):
        x1, y1, x2, y2 = seg
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm                      # 切割线法线方向
        flat = math.degrees(math.atan2(dy, dx))             # 切口朝向
        for sign in (1, -1):
            self.halves.append(HalfFruit(
                fruit.x, fruit.y,
                fruit.vx * 0.4 + nx * sign * random.uniform(120, 280),
                fruit.vy * 0.4 + ny * sign * random.uniform(120, 280) - 80,
                fruit.r, fruit.color, fruit.dark, flat,
            ))
        for _ in range(12):
            self.particles.append(Particle(fruit.x, fruit.y, fruit.color))
        self.popups.append(Popup(fruit.x, fruit.y - fruit.r - 6, "+1",
                                 (255, 255, 255), self.font_small))

    def explode(self, bomb):
        for color in ((255, 120, 40), (255, 200, 60), (110, 110, 110)) * 12:
            self.particles.append(Particle(bomb.x, bomb.y, color))
        self.flash = 1.0
        self.bombs.remove(bomb)
        self.best = max(self.best, self.score)
        self.state = self.OVER
        self.over_since = time.perf_counter()

    def handle_slices(self):
        total_cut = 0
        for seg in self.blade.slice_segments:
            for fruit in self.fruits:
                if not fruit.sliced and \
                        seg_point_dist(seg, fruit.x, fruit.y) <= fruit.r + BLADE_TIP_RADIUS:
                    fruit.sliced = True
                    total_cut += 1
                    self.split_fruit(fruit, seg)
            for bomb in list(self.bombs):
                if seg_point_dist(seg, bomb.x, bomb.y) <= bomb.r + BLADE_TIP_RADIUS:
                    self.explode(bomb)
                    return                                   # 切中炸弹，直接结束
        if total_cut:
            self.fruits = [f for f in self.fruits if not f.sliced]
            if total_cut >= COMBO_BONUS_MIN:
                bonus = total_cut * 2
                self.score += bonus
                self.popups.append(Popup(WINDOW_W / 2, WINDOW_H * 0.3,
                                         f"连击 x{total_cut}  +{bonus}",
                                         (255, 215, 0), self.font_mid))
            else:
                self.score += total_cut

    def lose_life(self):
        self.lives -= 1
        self.flash = max(self.flash, 0.5)
        if self.lives <= 0:
            self.best = max(self.best, self.score)
            self.state = self.OVER
            self.over_since = time.perf_counter()

    # ---------- 更新 ----------

    def update_fx(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for h in self.halves:
            h.update(dt)
        self.halves = [h for h in self.halves if h.y - h.r < WINDOW_H + 80]
        for p in self.popups:
            p.update(dt)
        self.popups = [p for p in self.popups if p.life > 0]
        self.flash = max(0.0, self.flash - dt * 1.5)

    def update_world(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            interval = max(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_START - self.score * 0.015)
            self.spawn_timer = interval * random.uniform(0.85, 1.25)

        for f in self.fruits:
            f.update(dt)
        for b in self.bombs:
            b.update(dt)
        self.update_fx(dt)

        for f in [f for f in self.fruits if f.fell_off(WINDOW_H)]:
            self.fruits.remove(f)
            self.lose_life()
        for b in [b for b in self.bombs if b.fell_off(WINDOW_H)]:
            self.bombs.remove(b)

    # ---------- 渲染 ----------

    def draw_text_center(self, font, text, y, color=(255, 255, 255)):
        img = font.render(text, True, color)
        self.screen.blit(img, ((WINDOW_W - img.get_width()) // 2, y))

    def draw(self, now):
        surf = self.screen
        surf.fill((0, 0, 0))
        if self.bg is not None:
            surf.blit(self.bg, (0, 0))
        surf.blit(self.tint, (0, 0))

        for h in self.halves:
            h.draw(surf)
        for f in self.fruits:
            f.draw(surf)
        for b in self.bombs:
            b.draw(surf)
        for p in self.particles:
            p.draw(surf)
        for p in self.popups:
            p.draw(surf)

        if self.state != self.PLAYING:  # 菜单/结算界面压暗
            self.dim.fill((0, 0, 0, 150))
            surf.blit(self.dim, (0, 0))

        self.blade.draw(surf, now)      # 刀光最后画，菜单时也能看清指尖

        if self.flash > 0:
            self.flash_surf.fill((255, 30, 30, int(self.flash * 130)))
            surf.blit(self.flash_surf, (0, 0))

        if self.state == self.PLAYING:
            img = self.font_mid.render(f"得分 {self.score}", True, (255, 255, 255))
            shadow = self.font_mid.render(f"得分 {self.score}", True, (0, 0, 0))
            surf.blit(shadow, (22, 18))
            surf.blit(img, (20, 16))
            for i in range(LIVES):
                color = (255, 70, 90) if i < self.lives else (60, 60, 60)
                draw_heart(surf, WINDOW_W - 34 - i * 42, 36, 15, color)
        elif self.state == self.MENU:
            self.draw_text_center(self.font_big, "手势切水果", WINDOW_H * 0.18)
            self.draw_text_center(self.font_mid, "举起食指，快速挥动即可切开水果",
                                  WINDOW_H * 0.42)
            self.draw_text_center(self.font_mid, "切到炸弹立即结束，漏掉水果扣一颗心",
                                  WINDOW_H * 0.42 + 52, (255, 170, 120))
            self.draw_text_center(self.font_small, "挥动手指 或 按 空格键 开始（ESC 退出）",
                                  WINDOW_H * 0.42 + 120, (180, 220, 255))
        else:
            self.draw_text_center(self.font_big, "游戏结束", WINDOW_H * 0.18, (255, 80, 80))
            self.draw_text_center(self.font_mid, f"得分 {self.score}    最佳 {self.best}",
                                  WINDOW_H * 0.42)
            tip = ("挥动手指 或 按 空格键 再来一局"
                   if time.perf_counter() - self.over_since > 1.0 else "…")
            self.draw_text_center(self.font_small, tip, WINDOW_H * 0.42 + 70, (180, 220, 255))

        pygame.display.flip()

    # ---------- 主循环 ----------

    def run(self):
        running = True
        while running:
            now = time.perf_counter()
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r) \
                            and self.state != self.PLAYING:
                        self.reset()
                        self.state = self.PLAYING

            frame, tip = self.tracker.read()
            if frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.bg = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
            self.blade.update(tip, now)

            if self.state == self.PLAYING:
                self.update_world(dt)
                if self.blade.slice_segments:
                    self.handle_slices()
            elif self.state == self.MENU:
                if self.blade.slice_segments:                # 挥手即可开始
                    self.reset()
                    self.state = self.PLAYING
            else:                                            # OVER
                self.update_fx(dt)                           # 爆炸粒子继续飘
                if self.blade.slice_segments and now - self.over_since > 1.0:
                    self.reset()
                    self.state = self.PLAYING

            self.draw(now)

        self.tracker.release()
        pygame.quit()


def main():
    try:
        game = Game()
    except RuntimeError as err:
        print(f"启动失败: {err}")
        sys.exit(1)
    game.run()


if __name__ == "__main__":
    main()
