"""指尖刀光轨迹与切割碰撞判定。"""

import math
from collections import deque

import pygame

from config import BLADE_TIP_RADIUS, MAX_TRAIL_POINTS, SLICE_MIN_SPEED, TRAIL_MAX_AGE


def seg_point_dist(seg, px, py):
    """点到线段的最短距离。seg = (x1, y1, x2, y2)。"""
    x1, y1, x2, y2 = seg
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-6:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


class Blade:
    """记录指尖轨迹；指尖速度足够快时产生切割线段。"""

    def __init__(self):
        self.points = deque()      # (x, y, 时间戳)
        self.slice_segments = []   # 本帧产生的切割线段 [(x1, y1, x2, y2)]

    def update(self, tip, now):
        """tip: 当前指尖 (x, y) 或 None；now: time.perf_counter() 秒。"""
        self.slice_segments = []
        if tip is None:
            self.points.clear()
            return
        if self.points:
            px, py, pt = self.points[-1]
            speed = math.hypot(tip[0] - px, tip[1] - py) / max(now - pt, 1e-4)
            if speed >= SLICE_MIN_SPEED:
                self.slice_segments.append((px, py, tip[0], tip[1]))
        self.points.append((tip[0], tip[1], now))
        while self.points and now - self.points[0][2] > TRAIL_MAX_AGE:
            self.points.popleft()
        while len(self.points) > MAX_TRAIL_POINTS:
            self.points.popleft()

    def hits(self, x, y, r):
        return any(seg_point_dist(s, x, y) <= r + BLADE_TIP_RADIUS
                   for s in self.slice_segments)

    def draw(self, surf, now):
        for i in range(1, len(self.points)):
            x1, y1, t1 = self.points[i - 1]
            x2, y2, _ = self.points[i]
            f = max(0.0, 1.0 - (now - t1) / TRAIL_MAX_AGE)  # 越旧越淡越细
            pygame.draw.line(surf, (int(150 + 105 * f), int(210 + 45 * f), 255),
                             (x1, y1), (x2, y2), max(1, int(8 * f)))
        if self.points:
            x, y, _ = self.points[-1]
            pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)), 5)
