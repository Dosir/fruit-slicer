"""摄像头 + MediaPipe 手部追踪封装。"""

import cv2
import mediapipe as mp


class HandTracker:
    """读取摄像头帧，输出食指指尖在窗口坐标系中的位置。"""

    def __init__(self, camera_index=0, target_size=(1280, 720)):
        self.target_w, self.target_h = target_size
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                "无法打开摄像头。请检查：1) 摄像头是否被其他 App 占用；"
                "2) macOS 相机权限（系统设置 -> 隐私与安全性 -> 相机，"
                "勾选你运行本程序的终端 App）。"
            )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )

    def read(self):
        """返回 (frame_bgr, tip)。

        frame_bgr: 已镜像、已缩放到窗口尺寸的 BGR 图像；读取失败时为 None。
        tip: 指尖 (x, y)，窗口坐标系（已镜像，符合直觉）；未检测到手时为 None。
        """
        ok, frame = self.cap.read()
        if not ok:
            return None, None
        frame = cv2.flip(frame, 1)  # 镜像，让移动方向和现实中一致

        h, w = frame.shape[:2]
        result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        tip = None
        if result.multi_hand_landmarks:
            lm = result.multi_hand_landmarks[0].landmark[8]  # 食指指尖
            tip = (lm.x * self.target_w, lm.y * self.target_h)

        frame = cv2.resize(frame, (self.target_w, self.target_h))
        return frame, tip

    def release(self):
        self.cap.release()
        self.hands.close()
