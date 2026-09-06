# 手势切水果 (Gesture Fruit Slicer)

基于摄像头的体感小游戏：伸出食指快速挥动，切开飞起的水果，小心炸弹！

技术栈：Python + Pygame + OpenCV + MediaPipe（手部 21 关键点追踪，CPU 实时）

## 玩法

- 举起食指，快速挥动即可切开水果，+1 分
- 同一刀切中 3 个及以上触发连击，双倍加分
- 切到炸弹：立即游戏结束
- 漏掉水果（掉出屏幕底部）：扣一颗心
- 3 颗心用完，游戏结束

## 环境要求

- macOS / Windows / Linux
- Python 3.8 – 3.12（新版本 MediaPipe 暂不支持 3.13+）
- 摄像头

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

> **macOS 首次运行**会弹出摄像头权限申请，请点击「允许」。
> 如果没有弹窗且报错：系统设置 → 隐私与安全性 → 相机 → 勾选你运行本程序的终端 App（Terminal / iTerm / VS Code）。

## 操作

| 操作 | 效果 |
|---|---|
| 快速挥动食指 | 切割 |
| 挥动手指 / 空格 | 开始、重新开始 |
| R | 重新开始 |
| ESC | 退出 |

## 调参

所有手感参数集中在 `config.py`：

- `SLICE_MIN_SPEED`：触发切割的最低挥动速度，切不动就调低（如 600），误切就调高
- `TIP_SMOOTHING`：指尖平滑系数，光标抖就调小（更稳但更滞后）
- `TRACK_LOST_GRACE`：指尖短暂丢失的宽限时间，刀光闪断就调大
- `GRAVITY` / `LAUNCH_VY`：水果抛物线手感
- `SPAWN_INTERVAL_START`：开局出水果的频率
- `BOMB_*`：炸弹出现概率

## 项目结构

```
config.py        全局参数（窗口、物理、玩法手感）
hand_tracker.py  摄像头 + MediaPipe 手部追踪，输出食指指尖坐标
blade.py         刀光轨迹 + 速度阈值切割判定（点到线段碰撞）
entities.py      水果 / 炸弹 / 两半果体 / 果汁粒子 / 飘字
main.py          游戏主循环（菜单、计分、生成、连击）
```

## 常见问题

- **mediapipe 安装失败**：确认 Python 版本 ≤ 3.12；必要时用 `python3.12 -m venv .venv` 指定版本
- **画面卡顿**：关闭其他占用摄像头的 App；把 `config.py` 里的 `WINDOW_W/H` 调小
- **切不到水果**：调低 `SLICE_MIN_SPEED`
- **误切**：调高 `SLICE_MIN_SPEED`
- **指尖追踪不灵敏/光标消失**：加强正面光照（减少运动模糊）；调大 `TRACK_LOST_GRACE`、调小 `TIP_SMOOTHING`
