"""背景音乐 —— 用 numpy 现场合成《我是一个粉刷匠》，无需外部音频文件。

旋律来源：波兰儿歌《我是一个粉刷匠》(1=C, 2/4)，只用 do/re/mi/fa/sol 五个音。
"""

import numpy as np
import pygame

SAMPLE_RATE = 44100

# 简谱音名 -> 频率（C 大调，1 = C5）
_NOTE_FREQ = {
    1: 523.25,   # do
    2: 587.33,   # re
    3: 659.26,   # mi
    4: 698.46,   # fa
    5: 783.99,   # sol
}

# 全曲四个乐句：(音名, 时值[拍])
MELODY = [
    # 我是一个粉刷匠，粉刷本领强
    (5, 0.5), (3, 0.5), (5, 0.5), (3, 0.5),
    (5, 0.5), (3, 0.5), (1, 1.0),
    (2, 0.5), (4, 0.5), (3, 0.5), (2, 0.5), (5, 2.0),
    # 我要把那新房子，刷得很漂亮
    (5, 0.5), (3, 0.5), (5, 0.5), (3, 0.5),
    (5, 0.5), (3, 0.5), (1, 1.0),
    (2, 0.5), (4, 0.5), (3, 0.5), (2, 0.5), (1, 2.0),
    # 刷了房顶又刷墙，刷子飞舞忙
    (2, 0.5), (2, 0.5), (4, 0.5), (4, 0.5),
    (3, 0.5), (1, 0.5), (5, 1.0),
    (2, 0.5), (4, 0.5), (3, 0.5), (2, 0.5), (5, 2.0),
    # 哎呀我的小鼻子，变呀变了样
    (5, 0.5), (3, 0.5), (5, 0.5), (3, 0.5),
    (5, 0.5), (3, 0.5), (1, 1.0),
    (2, 0.5), (4, 0.5), (3, 0.5), (2, 0.5), (1, 2.0),
]


def _synth_note(freq, dur):
    """合成单个音符：基频 + 少量二次泛音，指数衰减（音乐盒音色）。"""
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n) / SAMPLE_RATE
    decay = np.exp(-t * 5.0)
    wave = (np.sin(2 * np.pi * freq * t)
            + 0.35 * np.sin(2 * np.pi * 2 * freq * t)) * decay
    attack = max(1, int(SAMPLE_RATE * 0.006))
    wave[:attack] *= np.linspace(0.0, 1.0, attack)
    return wave


def build_music(tempo=108.0):
    """合成整首曲子，返回可循环播放的 pygame.mixer.Sound。"""
    beat = 60.0 / tempo
    parts = [_synth_note(_NOTE_FREQ[n], d * beat) for n, d in MELODY]
    mono = np.concatenate(parts)
    stereo = (np.repeat(mono, 2).reshape(-1, 2)) * 0.5
    samples = np.ascontiguousarray((stereo * 32767).astype(np.int16))
    return pygame.sndarray.make_sound(samples)
