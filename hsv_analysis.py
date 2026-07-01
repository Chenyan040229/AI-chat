"""
HSV 色彩空间分布 - 核密度估计(KDE)折线图
用于分析不同情绪类别图片的 HSV 分布特征

数据集结构：
  dataset/
    calm/
    happy/
    nostalgic/
    depressed/
    fear/
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.stats import gaussian_kde

# ============ 配置区域 ============

# 数据集根目录（修改为你的实际路径）
DATASET_DIR = './dataset'

# 情绪类别（文件夹名称）
CATEGORIES = ['calm', 'happy', 'nostalgic', 'depressed', 'fear']

# 中文标签映射
LABEL_MAP = {
    'calm': '平静',
    'happy': '高兴',
    'nostalgic': '怀旧',
    'depressed': '压抑',
    'fear': '害怕'
}

# 每个类别对应的线条颜色
COLOR_MAP = {
    'calm': '#1f77b4',       # 蓝色
    'happy': '#ff7f0e',      # 橙色
    'nostalgic': '#2ca02c',  # 绿色
    'depressed': '#d62728',  # 红色
    'fear': '#9467bd'        # 紫色
}

# 中文字体配置（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 如果中文字体仍然无法显示，取消下面这行注释并修改字体路径
# FONT_PROP = FontProperties(fname='C:/Windows/Fonts/msyh.ttc')


# ============ 核心函数 ============

def extract_hsv_values(image_dir):
    """
    从指定目录的所有图片中提取 HSV 值
    返回: H值列表, S值列表, V值列表
    """
    h_values = []
    s_values = []
    v_values = []

    if not os.path.exists(image_dir):
        print(f"⚠️ 目录不存在: {image_dir}")
        return np.array(h_values), np.array(s_values), np.array(v_values)

    image_files = [f for f in os.listdir(image_dir)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]

    print(f"📂 {os.path.basename(image_dir)}: 找到 {len(image_files)} 张图片")

    for img_file in image_files:
        img_path = os.path.join(image_dir, img_file)
        img = cv2.imread(img_path)

        if img is None:
            continue

        # 转换为 HSV 色彩空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 提取所有像素的 H, S, V 值（降采样加速）
        hsv_small = cv2.resize(hsv, (100, 100))
        h_values.extend(hsv_small[:, :, 0].flatten())
        s_values.extend(hsv_small[:, :, 1].flatten())
        v_values.extend(hsv_small[:, :, 2].flatten())

    return np.array(h_values), np.array(s_values), np.array(v_values)


def compute_kde(data, x_range, bandwidth=0.1):
    """
    计算核密度估计
    data: 数据数组
    x_range: 评估点的 x 范围
    bandwidth: 带宽系数（越小越尖锐）
    """
    if len(data) == 0:
        return np.zeros_like(x_range)

    data = data.astype(float)

    # 根据数据范围自动调整带宽
    bw = bandwidth * np.std(data)
    if bw < 1e-6:
        bw = 1.0

    try:
        kde = gaussian_kde(data, bw_method=bw)
        density = kde(x_range)
        return density
    except Exception as e:
        print(f"KDE 计算失败: {e}")
        return np.zeros_like(x_range)


def plot_hsv_distributions(all_data, save_path='hsv_distribution.png'):
    """
    绘制 HSV 三通道的 KDE 分布图（1×3 子图）
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 三个通道的配置
    channels = [
        {
            'key': 'h',
            'title': '色相(H)分布',
            'xlabel': '色相值',
            'ylabel': '密度',
            'x_range': np.linspace(0, 180, 500),
            'bandwidth': 0.08
        },
        {
            'key': 's',
            'title': '饱和度(S)分布',
            'xlabel': '饱和度值',
            'ylabel': '密度',
            'x_range': np.linspace(0, 255, 500),
            'bandwidth': 0.1
        },
        {
            'key': 'v',
            'title': '亮度(V)分布',
            'xlabel': '亮度值',
            'ylabel': '密度',
            'x_range': np.linspace(0, 255, 500),
            'bandwidth': 0.1
        }
    ]

    for ax, config in zip(axes, channels):
        for category in CATEGORIES:
            data = all_data[category][config['key']]

            if len(data) == 0:
                continue

            # 计算 KDE
            density = compute_kde(
                data,
                config['x_range'],
                bandwidth=config['bandwidth']
            )

            # 绘制曲线
            label = LABEL_MAP.get(category, category)
            ax.plot(
                config['x_range'], density,
                color=COLOR_MAP[category],
                label=label,
                linewidth=2,
                alpha=0.8
            )
            ax.fill_between(
                config['x_range'], density,
                color=COLOR_MAP[category],
                alpha=0.1
            )

        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.set_xlabel(config['xlabel'], fontsize=12)
        ax.set_ylabel(config['ylabel'], fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.suptitle('不同情绪类别图片的 HSV 色彩空间分布', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f'\n✅ 图表已保存: {save_path}')


def add_color_bars(all_data, save_path='hsv_distribution_full.png'):
    """
    绘制完整版本（包含底部色相/饱和度/亮度参考色带）
    """
    fig = plt.figure(figsize=(18, 7))

    # 上方三个子图
    gs = fig.add_gridspec(2, 3, height_ratios=[5, 1], hspace=0.35, wspace=0.3)
    axes = [fig.add_subplot(gs[0, i]) for i in range(3)]

    channels = [
        {'key': 'h', 'title': '色相(H)分布', 'xlabel': '色相值', 'ylabel': '密度',
         'x_range': np.linspace(0, 180, 500), 'bandwidth': 0.08},
        {'key': 's', 'title': '饱和度(S)分布', 'xlabel': '饱和度值', 'ylabel': '密度',
         'x_range': np.linspace(0, 255, 500), 'bandwidth': 0.1},
        {'key': 'v', 'title': '亮度(V)分布', 'xlabel': '亮度值', 'ylabel': '密度',
         'x_range': np.linspace(0, 255, 500), 'bandwidth': 0.1}
    ]

    for ax, config in zip(axes, channels):
        for category in CATEGORIES:
            data = all_data[category][config['key']]
            if len(data) == 0:
                continue

            density = compute_kde(data, config['x_range'], bandwidth=config['bandwidth'])

            label = LABEL_MAP.get(category, category)
            ax.plot(config['x_range'], density,
                    color=COLOR_MAP[category], label=label,
                    linewidth=2, alpha=0.8)
            ax.fill_between(config['x_range'], density,
                            color=COLOR_MAP[category], alpha=0.1)

        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.set_xlabel(config['xlabel'], fontsize=12)
        ax.set_ylabel(config['ylabel'], fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)

    # 底部色带参考
    # 色相色带
    ax_h = fig.add_subplot(gs[1, 0])
    hue_bar = np.linspace(0, 180, 256).reshape(1, -1)
    hue_bar_rgb = cv2.cvtColor(hue_bar.astype(np.uint8), cv2.COLOR_HSV2RGB)
    ax_h.imshow(hue_bar_rgb, aspect='auto')
    ax_h.set_xlabel('色相值', fontsize=10)
    ax_h.set_title('色相色带 (0-179)', fontsize=10)
    ax_h.set_yticks([])

    # 饱和度色带
    ax_s = fig.add_subplot(gs[1, 1])
    s_values = np.linspace(0, 255, 256).reshape(1, -1)
    s_bar = np.zeros((1, 256, 3), dtype=np.uint8)
    s_bar[:, :, 0] = 100  # H=100 (绿色区域)
    s_bar[:, :, 1] = s_values  # S 变化
    s_bar[:, :, 2] = 150  # V=150
    s_bar_rgb = cv2.cvtColor(s_bar, cv2.COLOR_HSV2RGB)
    ax_s.imshow(s_bar_rgb, aspect='auto')
    ax_s.set_xlabel('饱和度值', fontsize=10)
    ax_s.set_title('饱和度色带 (H=100, V=150)', fontsize=10)
    ax_s.set_yticks([])

    # 亮度色带
    ax_v = fig.add_subplot(gs[1, 2])
    v_values = np.linspace(0, 255, 256).reshape(1, -1)
    v_bar = np.zeros((1, 256, 3), dtype=np.uint8)
    v_bar[:, :, 2] = v_values  # V 变化
    v_bar_rgb = cv2.cvtColor(v_bar, cv2.COLOR_HSV2RGB)
    ax_v.imshow(v_bar_rgb, aspect='auto')
    ax_v.set_xlabel('亮度值', fontsize=10)
    ax_v.set_title('亮度色带 (S=0)', fontsize=10)
    ax_v.set_yticks([])

    plt.suptitle('不同情绪类别图片的 HSV 色彩空间分布', fontsize=16, fontweight='bold', y=1.02)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f'\n✅ 完整图表已保存: {save_path}')


# ============ 主程序 ============

def main():
    print("=" * 50)
    print("HSV 色彩空间分布分析")
    print("=" * 50)

    # 1. 提取所有类别的 HSV 值
    all_data = {}

    for category in CATEGORIES:
        category_dir = os.path.join(DATASET_DIR, category)
        h, s, v = extract_hsv_values(category_dir)
        all_data[category] = {'h': h, 's': s, 'v': v}

    # 2. 绘制分布图
    print("\n📊 正在生成分布图...")
    plot_hsv_distributions(all_data, save_path='hsv_distribution.png')
    add_color_bars(all_data, save_path='hsv_distribution_full.png')

    # 3. 打印统计信息
    print("\n" + "=" * 50)
    print("各情绪类别 HSV 统计信息")
    print("=" * 50)

    for category in CATEGORIES:
        label = LABEL_MAP[category]
        data = all_data[category]
        if len(data['h']) > 0:
            print(f"\n{label}({category}):")
            print(f"  H - 均值: {np.mean(data['h']):.1f}, 标准差: {np.std(data['h']):.1f}")
            print(f"  S - 均值: {np.mean(data['s']):.1f}, 标准差: {np.std(data['s']):.1f}")
            print(f"  V - 均值: {np.mean(data['v']):.1f}, 标准差: {np.std(data['v']):.1f}")


if __name__ == '__main__':
    main()
