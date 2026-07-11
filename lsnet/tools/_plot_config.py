# -*- coding: utf-8 -*-
"""LSNet 可视化工具 — matplotlib 中文字体配置"""
import sys
import matplotlib as mpl


def setup_chinese_font():
    """配置 matplotlib 中文字体（按优先级尝试多个字体）"""
    import matplotlib.pyplot as plt

    chinese_fonts = [
        'Microsoft YaHei',
        'SimHei',
        'SimSun',
        'KaiTi',
        'FangSong',
        'DengXian',
        'Microsoft JhengHei',
        'Arial Unicode MS',
    ]

    available = {f.name for f in mpl.font_manager.fontManager.ttflist}

    for font in chinese_fonts:
        if font in available:
            plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            return font

    plt.rcParams['axes.unicode_minus'] = False
    return None


def force_utf8_output():
    """强制 stdout/stderr 使用 UTF-8 编码"""
    if sys.stdout.encoding and sys.stdout.encoding.upper() != 'UTF-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    if sys.stderr.encoding and sys.stderr.encoding.upper() != 'UTF-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
