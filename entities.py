"""游戏实体：水果、炸弹、切开的两半、果汁粒子、得分飘字。"""

import math
import random

import pygame

from config import GRAVITY, LAUNCH_VX_MAX, LAUNCH_VY, WINDOW_W

# (名字, 主色, 深色, 半径)
FRUIT_TYPES = (
    ("西瓜", (102, 187, 106), (46, 125, 50), 46),
    ("橙子", (255, 167, 38), (225, 120, 0), 34),
    ("苹果", (239, 83, 80), (183, 28, 28), 32),
    ("猕猴桃", (156, 204, 101), (85, 139, 47), 30),
    ("柠檬", (230, 220, 90), (175, 164, 30), 28),
)


def launch_velocity(x):
    """从 x 处向屏幕中部上抛的初速度 (vx, vy)。"""
    vx = (WINDOW_W * random.uniform(0.35, 0.65) - x) * random.uniform(0.5, 1.4)
    vx = max(-LAUNCH_VX_MAX, min(LAUNCH_VX_MAX, vx))
    return vx, random.randint(*LAUNCH_VY)


class _Airborne:
    """公共部分：重力运动与出屏判断。"""

    def update(self, dt):
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def fell_off(self, screen_h):
        return self.y - self.r > screen_h and self.vy > 0


class Fruit(_Airborne):
    def __init__(self, x, y):
        self.name, self.color, self.dark, self.r = random.choice(FRUIT_TYPES)
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = launch_velocity(x)
        self.sliced = False

    def draw(self, surf):
        cx, cy, r = int(self.x), int(self.y), self.r
        pygame.draw.circle(surf, self.dark, (cx + 3, cy + 4), r)    # 阴影
        pygame.draw.circle(surf, self.color, (cx, cy), r)
        pygame.draw.circle(surf, self.dark, (cx, cy), r, 3)         # 描边
        if self.name == "西瓜":                                      # 深色条纹
            for dx in (-r * 0.55, 0.0, r * 0.55):
                half = math.sqrt(max(r * r - dx * dx, 0.0)) * 0.85
                pygame.draw.line(surf, self.dark,
                                 (cx + dx, cy - half), (cx + dx, cy + half), 4)
        else:                                                        # 高光
            pygame.draw.circle(surf, (255, 255, 255),
                               (cx - r // 3, cy - r // 3), max(r // 5, 3))


class Bomb(_Airborne):
    R = 26

    def __init__(self, x, y):
        self.r = self.R
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = launch_velocity(x)
        self.t = 0.0

    def update(self, dt):
        super().update(dt)
        self.t += dt

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(surf, (58, 58, 64), (cx, cy), self.r)
        pygame.draw.circle(surf, (18, 18, 22), (cx, cy), self.r, 3)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 7, cy - 3), 4)  # 眼睛
        pygame.draw.circle(surf, (255, 255, 255), (cx + 7, cy - 3), 4)
        pygame.draw.line(surf, (150, 120, 70),
                         (cx, cy - self.r), (cx + 10, cy - self.r - 12), 4)  # 引线
        if int(self.t * 8) % 2 == 0:                                     # 火花闪烁
            pygame.draw.circle(surf, (255, 200, 60), (cx + 11, cy - self.r - 14), 4)
            pygame.draw.circle(surf, (255, 120, 40), (cx + 11, cy - self.r - 14), 7, 2)


class HalfFruit(_Airborne):
    """半个果体：切口沿切割线，边旋转边飞出。"""

    def __init__(self, x, y, vx, vy, r, color, dark, flat_angle):
        self.r = r
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color, self.dark = color, dark
        self.rot = flat_angle
        self.spin = random.uniform(-220, 220)

    def update(self, dt):
        super().update(dt)
        self.rot += self.spin * dt

    def draw(self, surf):
        pts = []
        for i in range(0, 181, 12):  # 半圆弧，闭合边即切口
            a = math.radians(self.rot + i)
            pts.append((int(self.x + self.r * math.cos(a)),
                        int(self.y + self.r * math.sin(a))))
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.line(surf, self.dark, pts[0], pts[-1], 4)


class Particle:
    """果汁粒子。"""

    def __init__(self, x, y, color):
        ang = random.uniform(0, math.tau)
        speed = random.uniform(60, 420)
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = math.cos(ang) * speed, math.sin(ang) * speed - 120
        self.r = random.randint(3, 7)
        self.life = random.uniform(0.4, 0.9)
        self.max_life = self.life
        self.color = color

    def update(self, dt):
        self.vy += GRAVITY * 0.6 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surf):
        f = max(self.life / self.max_life, 0.0)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)),
                           max(int(self.r * f), 1))


class Popup:
    """向上飘并淡出的文字。"""

    def __init__(self, x, y, text, color, font, life=0.8):
        self.x, self.y = float(x), float(y)
        self.img = font.render(text, True, color)
        self.life = self.max_life = life

    def update(self, dt):
        self.y -= 55 * dt
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        self.img.set_alpha(int(255 * self.life / self.max_life))
        surf.blit(self.img, (self.x - self.img.get_width() / 2, self.y))
