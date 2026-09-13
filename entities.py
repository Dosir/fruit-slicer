"""游戏实体：水果、炸弹、切开的两半、果汁粒子、得分飘字。"""

import math
import os
import random

import pygame

from config import GRAVITY, LAUNCH_VX_MAX, LAUNCH_VY, WINDOW_W

# (名字, 主色, 深色, 半径)
FRUIT_TYPES = (
    ("西瓜", (102, 187, 106), (46, 125, 50), 46),
    ("橙子", (255, 167, 38), (225, 120, 0), 34),
)

# 切开后露出的果肉 / 白瓤颜色（贴近真实果肉）
FRUIT_FLESH = {
    "西瓜": ((244, 104, 98), (214, 232, 176)),
    "橙子": ((255, 200, 120), (255, 244, 224)),
}

# 真实果体贴图：由 tools/render_emoji.swift 生成，等比缩放到碰撞直径
_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_FRUIT_SPRITE_FILES = {"西瓜": "watermelon.png", "橙子": "orange.png"}


def _scale_sprite(img, r):
    w, h = img.get_size()
    scale = (2 * r) / max(w, h)
    return pygame.transform.smoothscale(
        img, (max(1, int(w * scale)), max(1, int(h * scale))))


FRUIT_SPRITES = {}  # 由 main 在 set_mode 之后调用 load_fruit_sprites() 填充


def load_fruit_sprites():
    """建窗后调用：加载并 convert_alpha，把贴图转成显示格式（blit 快 ~26 倍）。"""
    for _name, _color, _dark, _r in FRUIT_TYPES:
        _path = os.path.join(_ASSET_DIR, _FRUIT_SPRITE_FILES.get(_name, ""))
        _img = None
        if os.path.exists(_path):
            try:
                _img = pygame.image.load(_path)
                _img = _scale_sprite(_img, _r)
                _img = _img.convert_alpha()   # 转成显示表面格式，避免每帧逐像素转换
            except pygame.error:
                _img = None
        FRUIT_SPRITES[_name] = _img


_SHADOW_CACHE = {}


def _soft_shadow(r):
    """按半径缓存的圆形软阴影（alpha 渐变）。"""
    surf = _SHADOW_CACHE.get(r)
    if surf is not None:
        return surf
    side = 2 * r + 10
    surf = pygame.Surface((side, side), pygame.SRCALPHA)
    c = r + 5
    steps = max(3, r // 3)
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        pygame.draw.circle(surf, (0, 0, 0, int(70 * i / steps)), (c, c), rr)
    _SHADOW_CACHE[r] = surf
    return surf


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
        self.inner, self.pith = FRUIT_FLESH.get(self.name, (self.color, (255, 255, 255)))
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = launch_velocity(x)
        self.sliced = False

    def draw(self, surf):
        cx, cy, r = int(self.x), int(self.y), self.r
        sprite = FRUIT_SPRITES.get(self.name)
        if sprite is not None:
            shadow = _soft_shadow(r)
            surf.blit(shadow, (cx - shadow.get_width() // 2 + 3,
                               cy - shadow.get_height() // 2 + 6))
            surf.blit(sprite, (cx - sprite.get_width() // 2,
                               cy - sprite.get_height() // 2))
            return
        # 贴图缺失时的兜底：回退到圆形 + 纹路
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

    def __init__(self, x, y, vx, vy, r, color, dark, inner, pith, name, flat_angle):
        self.r = r
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color, self.dark = color, dark
        self.inner, self.pith = inner, pith
        self.name = name
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
        pygame.draw.polygon(surf, self.inner, pts)                 # 果肉
        rind = max(3, int(self.r * 0.20))
        pygame.draw.lines(surf, self.color, False, pts, rind)      # 果皮
        pygame.draw.lines(surf, self.pith, False, pts, rind // 2)  # 白瓤
        pygame.draw.line(surf, self.dark, pts[0], pts[-1], 3)      # 切口
        if self.name == "西瓜":                                     # 籽
            for la in (40, 90, 140):
                a = math.radians(self.rot + la)
                sx = self.x + self.r * 0.55 * math.cos(a)
                sy = self.y + self.r * 0.55 * math.sin(a)
                pygame.draw.ellipse(surf, (40, 30, 26),
                                    (int(sx - 3), int(sy - 4), 6, 8))
        elif self.name == "橙子":                                   # 瓣纹
            for la in (30, 60, 90, 120, 150):
                a = math.radians(self.rot + la)
                ex = self.x + self.r * 0.80 * math.cos(a)
                ey = self.y + self.r * 0.80 * math.sin(a)
                pygame.draw.line(surf, (240, 208, 150),
                                 (int(self.x), int(self.y)),
                                 (int(ex), int(ey)), 2)


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
