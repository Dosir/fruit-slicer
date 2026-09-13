# 全局配置：所有手感参数都在这里调

# 窗口
WINDOW_W, WINDOW_H = 1280, 720
FPS = 60

# 摄像头
CAMERA_INDEX = 0
CAMERA_SIZE = (640, 480)     # 采集分辨率；越低推理越快，指尖坐标按比例映射不受影响

# 刀光
MAX_TRAIL_POINTS = 24        # 轨迹最多保留的点数
TRAIL_MAX_AGE = 0.20         # 轨迹点存活时间（秒）
SLICE_MIN_SPEED = 1000       # 触发切割的指尖最低速度（像素/秒）
SLICE_MAX_LEN = WINDOW_W / 3  # 切割线段长度上限（像素）：超过视为幽灵切割（丢检跳变），不参与判定
BLADE_TIP_RADIUS = 10        # 判定时给指尖加的缓冲半径
TRACK_LOST_GRACE = 0.2      # 指尖短暂丢失的宽限时间（秒），期内恢复则桥接切割
TIP_SMOOTH_MIN = 0.3         # 慢速（瞄准）时的 EMA 系数下限：越小越稳但越滞后
TIP_SMOOTH_SPEED = 900       # 平滑释放速度（像素/秒）：挥动达到该速度后不再平滑（跟手）
TIP_PREDICT_MAX = 0.05       # 指尖外推时长上限（秒）：追踪线程暂时卡住时光标冻结而不是滑飞

# 物理
GRAVITY = 1500.0             # 重力加速度（像素/秒^2）
LAUNCH_VY = (-1250, -900)    # 上抛初速度范围（像素/秒）
LAUNCH_VX_MAX = 650          # 水平初速度上限

# 玩法
GAME_DURATION = 120          # 一局时长（秒），倒计时结束游戏结束
SPAWN_INTERVAL_START = 1.35  # 开局出水果的间隔（秒）
SPAWN_INTERVAL_MIN = 0.55    # 间隔下限（随得分递减）
WAVE_SIZE = (1, 4)           # 每波水果数量范围
BOMB_BASE_P = 0.06           # 炸弹基础概率
BOMB_P_PER_SCORE = 0.0035    # 每得 1 分增加的炸弹概率
BOMB_MAX_P = 0.22            # 炸弹概率上限
COMBO_BONUS_MIN = 3          # 同一刀切中 >=3 个触发连击奖励

# 背景音乐
MUSIC_ENABLED = True         # 是否播放背景音乐（《我是一个粉刷匠》）
MUSIC_VOLUME = 0.35          # 音量 0~1
