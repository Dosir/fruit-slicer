"""指尖刀光轨迹与切割碰撞判定。"""

import math
from collections import deque

import pygame

from config import (
    BLADE_TIP_RADIUS, MAX_TRAIL_POINTS, SLICE_MAX_LEN, SLICE_MIN_SPEED,
    TRACK_LOST_GRACE, TRAIL_MAX_AGE,
)


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
        self.lost_at = None        # 指尖开始丢失的时间，用于短时宽限

    def update(self, tip, now):
        """tip: 当前指尖 (x, y) 或 None；now: time.perf_counter() 秒。"""
        self.slice_segments = []
        self._prune(now)
        if tip is None:
            # 偶发丢检不清空轨迹：宽限期内恢复时从上一点桥接，刀光不闪断
            if self.lost_at is None:
                self.lost_at = now
            if now - self.lost_at > TRACK_LOST_GRACE:
                self.points.clear()
            return
        self.lost_at = None
        if self.points:
            px, py, pt = self.points[-1]
            # 跨过丢失间隙的两点也照常算速度，快速挥动不会因丢帧而断刀
            seg_len = math.hypot(tip[0] - px, tip[1] - py)
            speed = seg_len / max(now - pt, 1e-4)
            # 丢检跳变会产生横跨半屏的假切割线段，长度超限视为幽灵切割、不参与判定
            if seg_len <= SLICE_MAX_LEN and speed >= SLICE_MIN_SPEED:
                self.slice_segments.append((px, py, tip[0], tip[1]))
        self.points.append((tip[0], tip[1], now))
        self._prune(now)

    def _prune(self, now):
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
