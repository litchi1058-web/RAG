"""分析测试集数据质量"""
import sys
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

def analyze_test_set():
    """分析测试集数据质量"""
    test_dir = Path(__file__).parent / "data" / "custom" / "测试集"
    
    print("="*60)
    print("测试集数据质量分析")
    print("="*60)
    
    # 统计每个类别
    class_stats = defaultdict(list)
    
    for class_dir in test_dir.iterdir():
        if class_dir.is_dir():
            class_name = class_dir.name
            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    try:
                        img = Image.open(img_path)
                        width, height = img.size
                        mode = img.mode
                        
                        # 检查图片质量
                        is_valid = True
                        issues = []
                        
                        # 检查尺寸
                        if width < 100 or height < 100:
                            issues.append(f"尺寸过小({width}x{height})")
                            is_valid = False
                        
                        # 检查模式
                        if mode not in ['RGB', 'L']:
                            issues.append(f"异常模式({mode})")
                            is_valid = False
                        
                        # 检查文件大小
                        file_size = img_path.stat().st_size
                        if file_size < 1024:  # < 1KB
                            issues.append(f"文件过小({file_size}B)")
                            is_valid = False
                        
                        class_stats[class_name].append({
                            'path': img_path,
                            'width': width,
                            'height': height,
                            'mode': mode,
                            'file_size': file_size,
                            'is_valid': is_valid,
                            'issues': issues
                        })
                    except Exception as e:
                        class_stats[class_name].append({
                            'path': img_path,
                            'is_valid': False,
                            'issues': [f"无法打开: {e}"]
                        })
    
    # 输出统计
    print(f"\n总类别数: {len(class_stats)}")
    total_images = sum(len(v) for v in class_stats.values())
    print(f"总图片数: {total_images}")
    
    print(f"\n各类别详情:")
    for class_name in sorted(class_stats.keys()):
        images = class_stats[class_name]
        valid_count = sum(1 for img in images if img['is_valid'])
        invalid_count = len(images) - valid_count
        
        print(f"\n  类别 {class_name}:")
        print(f"    总数: {len(images)}")
        print(f"    有效: {valid_count}")
        print(f"    问题: {invalid_count}")
        
        if invalid_count > 0:
            print(f"    问题图片:")
            for img in images:
                if not img['is_valid']:
                    print(f"      - {img['path'].name}: {', '.join(img['issues'])}")
        
        # 尺寸统计
        widths = [img.get('width', 0) for img in images if img.get('width')]
        heights = [img.get('height', 0) for img in images if img.get('height')]
        if widths:
            print(f"    尺寸范围: {min(widths)}x{min(heights)} ~ {max(widths)}x{max(heights)}")
    
    # 总结
    total_valid = sum(sum(1 for img in images if img['is_valid']) for images in class_stats.values())
    total_invalid = total_images - total_valid
    
    print(f"\n{'='*60}")
    print(f"总结:")
    print(f"  有效图片: {total_valid} ({total_valid/total_images*100:.1f}%)")
    print(f"  问题图片: {total_invalid} ({total_invalid/total_images*100:.1f}%)")
    print(f"{'='*60}")

if __name__ == "__main__":
    analyze_test_set()