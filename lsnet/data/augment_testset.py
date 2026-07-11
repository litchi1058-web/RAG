# -*- coding: utf-8 -*-
"""
测试集数据增强脚本
对测试集进行多种数据增强，扩充数据集并过滤噪声样本
"""
import os
import random
import shutil
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import numpy as np
from tqdm import tqdm


class TestSetAugmenter:
    """测试集数据增强器"""

    def __init__(self, input_dir, output_dir, augmentations_per_image=5, seed=42):
        """
        Args:
            input_dir: str 输入目录（原始测试集）
            output_dir: str 输出目录（增强后的测试集）
            augmentations_per_image: int 每张图片生成的增强版本数量
            seed: int 随机种子
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.augmentations_per_image = augmentations_per_image
        self.seed = seed

        random.seed(seed)
        np.random.seed(seed)

        # 图像质量检查阈值
        self.min_size = 64  # 最小尺寸
        self.max_size = 4096  # 最大尺寸

    def is_valid_image(self, img_path):
        """
        检查图片是否有效（过滤噪声样本）

        Args:
            img_path: Path 图片路径

        Returns:
            bool: 是否有效
        """
        try:
            img = Image.open(img_path)

            # 检查尺寸
            width, height = img.size
            if width < self.min_size or height < self.min_size:
                return False, "图片尺寸太小"
            if width > self.max_size or height > self.max_size:
                return False, "图片尺寸太大"

            # 检查是否灰度图或异常
            if img.mode == 'L':
                return False, "灰度图"

            # 检查文件大小
            file_size = os.path.getsize(img_path)
            if file_size < 1000:  # 小于1KB可能是损坏的
                return False, "文件太小"

            return True, "正常"

        except Exception as e:
            return False, f"读取失败: {str(e)}"

    def horizontal_flip(self, image):
        """水平翻转"""
        return image.transpose(Image.FLIP_LEFT_RIGHT)

    def vertical_flip(self, image):
        """垂直翻转"""
        return image.transpose(Image.FLIP_TOP_BOTTOM)

    def random_rotation(self, image, max_degrees=15):
        """随机旋转"""
        degrees = random.uniform(-max_degrees, max_degrees)
        return image.rotate(degrees, expand=False, fillcolor=(255, 255, 255))

    def random_brightness(self, image, factor_range=(0.7, 1.3)):
        """随机调整亮度"""
        factor = random.uniform(*factor_range)
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def random_contrast(self, image, factor_range=(0.7, 1.3)):
        """随机调整对比度"""
        factor = random.uniform(*factor_range)
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def random_saturation(self, image, factor_range=(0.7, 1.3)):
        """随机调整饱和度"""
        factor = random.uniform(*factor_range)
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    def random_blur(self, image, radius_range=(0.5, 1.5)):
        """随机模糊"""
        from PIL import ImageFilter
        radius = random.uniform(*radius_range)
        return image.filter(ImageFilter.GaussianBlur(radius=radius))

    def random_crop_and_resize(self, image, crop_ratio_range=(0.8, 0.95)):
        """随机裁剪并调整大小"""
        width, height = image.size
        crop_ratio = random.uniform(*crop_ratio_range)

        new_width = int(width * crop_ratio)
        new_height = int(height * crop_ratio)

        # 随机裁剪位置
        left = random.randint(0, width - new_width)
        top = random.randint(0, height - new_height)
        right = left + new_width
        bottom = top + new_height

        cropped = image.crop((left, top, right, bottom))
        return cropped.resize((width, height), Image.Resampling.LANCZOS)

    def add_noise(self, image, noise_level=0.02):
        """添加高斯噪声"""
        img_array = np.array(image).astype(np.float32) / 255.0
        noise = np.random.normal(0, noise_level, img_array.shape)
        noisy_img = np.clip(img_array + noise, 0, 1)
        return Image.fromarray((noisy_img * 255).astype(np.uint8))

    def center_crop(self, image, crop_ratio=0.9):
        """中心裁剪"""
        width, height = image.size
        new_width = int(width * crop_ratio)
        new_height = int(height * crop_ratio)

        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height

        cropped = image.crop((left, top, right, bottom))
        return cropped.resize((width, height), Image.Resampling.LANCZOS)

    def get_augmentation_functions(self):
        """获取所有增强函数"""
        return [
            ('horizontal_flip', self.horizontal_flip),
            ('vertical_flip', self.vertical_flip),
            ('random_rotation', self.random_rotation),
            ('random_brightness', self.random_brightness),
            ('random_contrast', self.random_contrast),
            ('random_saturation', self.random_saturation),
            ('random_blur', self.random_blur),
            ('random_crop', self.random_crop_and_resize),
            ('center_crop', self.center_crop),
        ]

    def apply_random_augmentation(self, image):
        """
        随机应用多种增强

        Args:
            image: PIL.Image 输入图像

        Returns:
            list: 增强后的图像列表
        """
        augmented_images = []
        aug_funcs = self.get_augmentation_functions()

        # 确保至少生成指定数量的增强图片
        for i in range(self.augmentations_per_image):
            aug_img = image.copy()

            # 随机选择1-3种增强方式组合
            num_augs = random.randint(1, 3)
            selected_augs = random.sample(aug_funcs, min(num_augs, len(aug_funcs)))

            for aug_name, aug_func in selected_augs:
                try:
                    if aug_name == 'random_rotation':
                        aug_img = aug_func(aug_img, max_degrees=random.choice([10, 15, 20]))
                    elif aug_name == 'random_brightness':
                        aug_img = aug_func(aug_img, factor_range=(0.7, 1.3))
                    elif aug_name == 'random_contrast':
                        aug_img = aug_func(aug_img, factor_range=(0.8, 1.2))
                    elif aug_name == 'random_saturation':
                        aug_img = aug_func(aug_img, factor_range=(0.7, 1.3))
                    elif aug_name == 'random_crop':
                        aug_img = aug_func(aug_img, crop_ratio_range=(0.85, 0.95))
                    else:
                        aug_img = aug_func(aug_img)
                except Exception as e:
                    print(f"增强失败 {aug_name}: {e}")
                    aug_img = image.copy()

            augmented_images.append(aug_img)

        return augmented_images

    def process_dataset(self):
        """
        处理整个数据集

        Returns:
            dict: 处理统计信息
        """
        stats = {
            'total_original': 0,
            'valid_original': 0,
            'invalid_original': 0,
            'total_augmented': 0,
            'classes': {},
            'invalid_samples': []
        }

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 遍历所有类别
        class_dirs = sorted([d for d in self.input_dir.iterdir() if d.is_dir()])

        print(f"输入目录: {self.input_dir}")
        print(f"输出目录: {self.output_dir}")
        print(f"每张图片生成 {self.augmentations_per_image} 个增强版本")
        print("-" * 60)

        for class_dir in class_dirs:
            class_name = class_dir.name
            output_class_dir = self.output_dir / class_name
            output_class_dir.mkdir(exist_ok=True)

            print(f"\n处理类别: {class_name}")

            original_count = 0
            augmented_count = 0
            valid_count = 0
            invalid_list = []

            # 获取所有图片
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                image_files.extend(list(class_dir.glob(ext)))

            for img_path in tqdm(image_files, desc=f"  {class_name}"):
                original_count += 1

                # 检查图片有效性
                is_valid, reason = self.is_valid_image(img_path)

                if is_valid:
                    valid_count += 1

                    # 复制原始图片
                    output_path = output_class_dir / img_path.name
                    shutil.copy(img_path, output_path)

                    # 生成增强版本
                    try:
                        img = Image.open(img_path)
                        augmented_images = self.apply_random_augmentation(img)

                        for aug_idx, aug_img in enumerate(augmented_images):
                            aug_name = f"{img_path.stem}_aug{aug_idx + 1}{img_path.suffix}"
                            aug_path = output_class_dir / aug_name
                            aug_img.save(aug_path, quality=95)
                            augmented_count += 1

                    except Exception as e:
                        print(f"\n  处理图片 {img_path.name} 时出错: {e}")
                else:
                    invalid_list.append({
                        'file': img_path.name,
                        'reason': reason
                    })
                    stats['invalid_samples'].append({
                        'class': class_name,
                        'file': img_path.name,
                        'reason': reason
                    })

            stats['total_original'] += original_count
            stats['valid_original'] += valid_count
            stats['invalid_original'] += len(invalid_list)
            stats['total_augmented'] += augmented_count
            stats['classes'][class_name] = {
                'original': original_count,
                'valid': valid_count,
                'augmented': augmented_count,
                'total_after': valid_count + augmented_count,
                'invalid': invalid_list
            }

            print(f"  原始: {original_count}, 有效: {valid_count}, "
                  f"增强: +{augmented_count}, 最终: {valid_count + augmented_count}")

            if invalid_list:
                print(f"  无效样本 ({len(invalid_list)}):")
                for inv in invalid_list[:5]:  # 只显示前5个
                    print(f"    - {inv['file']}: {inv['reason']}")
                if len(invalid_list) > 5:
                    print(f"    ... 还有 {len(invalid_list) - 5} 个")

        return stats

    def print_summary(self, stats):
        """
        打印统计摘要

        Args:
            stats: dict 统计信息
        """
        print("\n" + "=" * 60)
        print("数据增强完成！统计摘要")
        print("=" * 60)

        print(f"\n原始数据:")
        print(f"  总图片数: {stats['total_original']}")
        print(f"  有效图片: {stats['valid_original']}")
        print(f"  无效图片: {stats['invalid_original']}")

        print(f"\n增强后数据:")
        print(f"  新增增强图片: {stats['total_augmented']}")
        print(f"  最终图片总数: {stats['valid_original'] + stats['total_augmented']}")

        print(f"\n各类别详情:")
        print("-" * 60)
        print(f"{'类别':<10} {'原始':<8} {'有效':<8} {'增强':<8} {'最终':<8}")
        print("-" * 60)

        total_final = 0
        for class_name, class_stats in stats['classes'].items():
            print(f"{class_name:<10} {class_stats['original']:<8} {class_stats['valid']:<8} "
                  f"{class_stats['augmented']:<8} {class_stats['total_after']:<8}")
            total_final += class_stats['total_after']

        print("-" * 60)
        print(f"{'总计':<10} {stats['total_original']:<8} {stats['valid_original']:<8} "
              f"{stats['total_augmented']:<8} {total_final:<8}")

        if stats['invalid_samples']:
            print(f"\n检测到 {len(stats['invalid_samples'])} 个无效/噪声样本:")
            print("建议检查这些样本是否应该删除或重新标注。")

        print(f"\n增强后的数据集已保存至: {self.output_dir}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='测试集数据增强工具')
    parser.add_argument('--input', '-i', type=str,
                        default='d:/bf/proj/RAG/lsnet/data/custom/测试集',
                        help='输入目录（原始测试集）')
    parser.add_argument('--output', '-o', type=str,
                        default='d:/bf/proj/RAG/lsnet/data/custom/测试集_augmented',
                        help='输出目录（增强后的测试集）')
    parser.add_argument('--num-aug', '-n', type=int, default=5,
                        help='每张图片生成的增强版本数量（默认5）')
    parser.add_argument('--seed', '-s', type=int, default=42,
                        help='随机种子')

    args = parser.parse_args()

    print("=" * 60)
    print("测试集数据增强工具")
    print("=" * 60)
    print(f"\n功能说明:")
    print("- 对有效图片生成多种增强版本（翻转、旋转、颜色调整等）")
    print("- 自动检测并记录无效/噪声样本（尺寸异常、灰度图等）")
    print("- 保留原始有效图片，新增增强图片")
    print()

    # 创建增强器
    augmenter = TestSetAugmenter(
        input_dir=args.input,
        output_dir=args.output,
        augmentations_per_image=args.num_aug,
        seed=args.seed
    )

    # 处理数据集
    stats = augmenter.process_dataset()

    # 打印摘要
    augmenter.print_summary(stats)


if __name__ == '__main__':
    main()
