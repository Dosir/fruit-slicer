"""摄像头 + MediaPipe 手部追踪封装（追踪线程化：后台推理，主线程无阻塞读取）。"""

import math
import threading
import time

import cv2
import mediapipe as mp

from config import TIP_PREDICT_MAX, TIP_SMOOTH_MIN, TIP_SMOOTH_SPEED


class HandTracker:
    """后台线程完成摄像头采集与 MediaPipe 推理，主线程无阻塞读取最新结果。

    推理单帧耗时 20~40ms，放在游戏主循环里会把帧率拖到 30fps 以下。改为
    生产者-消费者结构：追踪线程以摄像头速率（约 30fps）产出最新画面与指尖；
    游戏主线程每帧 read() 立即返回，帧率不再受推理耗时拖累。
    """

    def __init__(self, camera_index=0, target_size=(1280, 720),
                 camera_size=(640, 480)):
        self.target_w, self.target_h = target_size
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                "无法打开摄像头。请检查：1) 摄像头是否被其他 App 占用；"
                "2) macOS 相机权限（系统设置 -> 隐私与安全性 -> 相机，"
                "勾选你运行本程序的终端 App）。"
            )
        # 低分辨率采集：landmark 是归一化坐标，映射到窗口尺寸不受影响，
        # 而小帧让 MediaPipe 推理明显更快（Intel Mac 上尤为关键）。
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_size[1])
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 只缓冲一帧，降低采集延迟
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.3,
        )

        self._lock = threading.Lock()
        self._frame = None   # 最新一帧（已镜像、已缩放），None = 尚未采到
        self._tips = []      # 最近两次追踪到的指尖 [(x, y, 采集时刻)]
        self._smooth = None  # 指尖 EMA 平滑状态（仅追踪线程访问）
        self._last_seen = None  # 上次检测到指尖的采集时刻（仅追踪线程访问，算帧间速度）
        self._running = True
        self._thread = threading.Thread(target=self._track_loop, daemon=True)
        self._thread.start()

    def _track_loop(self):
        """追踪线程主循环：采集 → 推理 → EMA 平滑 → 发布最新结果。"""
        while self._running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)  # 暂时读不到帧：稍作退避，避免空转
                continue
            captured_at = time.perf_counter()  # 采集时刻，供主线程外推指尖
            frame = cv2.flip(frame, 1)  # 镜像，让移动方向和现实中一致

            result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            tip = None
            if result.multi_hand_landmarks:
                lm = result.multi_hand_landmarks[0].landmark[8]  # 食指指尖
                raw = (lm.x * self.target_w, lm.y * self.target_h)
                if self._smooth is None:
                    tip = raw
                else:
                    # 速度自适应 EMA：慢速瞄准用强平滑（稳），快速挥刀弱平滑（跟手）。
                    # 按帧间速度在 [alpha_min, 1.0] 间线性插值，速度越快 alpha 越大。
                    dt = captured_at - (self._last_seen or captured_at)
                    dx = raw[0] - self._smooth[0]
                    dy = raw[1] - self._smooth[1]
                    speed = math.hypot(dx, dy) / max(dt, 1e-4)  # 像素/秒
                    alpha = min(max(speed / TIP_SMOOTH_SPEED, TIP_SMOOTH_MIN), 1.0)
                    tip = (self._smooth[0] + alpha * dx,
                           self._smooth[1] + alpha * dy)
                self._smooth = tip
                self._last_seen = captured_at
            else:
                # 丢失即重置平滑状态：恢复时直接取原始检测值，避免带着旧位置滞后
                self._smooth = None
                self._last_seen = None

            frame = cv2.resize(frame, (self.target_w, self.target_h))
            with self._lock:
                self._frame = frame
                if tip is None:
                    self._tips = []
                else:
                    self._tips.append((tip[0], tip[1], captured_at))
                    if len(self._tips) > 2:
                        self._tips.pop(0)

    def read(self):
        """返回 (frame_bgr, tip)，均可能为 None。

        frame_bgr: 最新摄像头画面（已镜像、已缩放到窗口尺寸）。追踪线程未
        产出新帧时返回上一帧的同一对象，主线程可据此跳过重复的转色与建面。
        tip: 指尖 (x, y)，窗口坐标系；按最近两次追踪结果向当前时刻线性外推，
        补齐追踪帧率（约 30fps）与游戏帧率（60fps）之间的空档，并抵消一部分
        采集 + 推理延迟。未检测到手时为 None。
        """
        with self._lock:
            frame = self._frame
            tips = self._tips[:]
        now = time.perf_counter()
        if not tips:
            return frame, None
        x, y, t = tips[-1]
        if len(tips) == 2:
            px, py, pt = tips[0]
            span = t - pt
            if span > 1e-4:
                # 外推时长封顶：追踪线程暂时卡住时光标冻结，而不是沿旧速度滑飞
                ahead = min(now - t, TIP_PREDICT_MAX)
                if ahead > 0:
                    k = ahead / span
                    x += (x - px) * k
                    y += (y - py) * k
        return frame, (x, y)

    def release(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self.cap.release()
        self.hands.close()
