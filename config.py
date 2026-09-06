# 全局配置：所有手感参数都在这里调

# 窗口
WINDOW_W, WINDOW_H = 1280, 720
FPS = 60

# 摄像头
CAMERA_INDEX = 0

# 刀光
MAX_TRAIL_POINTS = 24        # 轨迹最多保留的点数
TRAIL_MAX_AGE = 0.20         # 轨迹点存活时间（秒）
SLICE_MIN_SPEED = 850        # 触发切割的指尖最低速度（像素/秒）
BLADE_TIP_RADIUS = 10        # 判定时给指尖加的缓冲半径

# 物理
GRAVITY = 1500.0             # 重力加速度（像素/秒^2）
LAUNCH_VY = (-1250, -900)    # 上抛初速度范围（像素/秒）
LAUNCH_VX_MAX = 650          # 水平初速度上限

# 玩法
LIVES = 3                    # 初始生命
SPAWN_INTERVAL_START = 1.35  # 开局出水果的间隔（秒）
SPAWN_INTERVAL_MIN = 0.55    # 间隔下限（随得分递减）
WAVE_SIZE = (1, 4)           # 每波水果数量范围
BOMB_BASE_P = 0.06           # 炸弹基础概率
BOMB_P_PER_SCORE = 0.0035    # 每得 1 分增加的炸弹概率
BOMB_MAX_P = 0.22            # 炸弹概率上限
COMBO_BONUS_MIN = 3          # 同一刀切中 >=3 个触发连击奖励
