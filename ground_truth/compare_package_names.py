# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================

import os
import shutil
from typing import Set

BLACKBOX_DIR = r"D:\LibProbe\ground_truth\blackbox_apk"
WHITEBOX_DIR = r"D:\LibProbe\ground_truth\whitebox_apk"
MAPPING_DIR = r"D:\LibProbe\ground_truth\mapping"
DESTINATION_DIR = r"D:\LibProbe\ground_truth\GT2\blackbox_apk"

def extract_package_name(filename: str) -> str:
    """提取文件名中的 Package Name"""
    basename = os.path.basename(filename)
    last_underscore_index = basename.rfind('_')
    
    if last_underscore_index != -1:
        return basename[:last_underscore_index]
    else:
        return os.path.splitext(basename)[0]

def get_packages_from_dir(directory_path: str) -> Set[str]:
    """遍历文件夹，提取所有文件的包名并返回一个集合 (Set)"""
    package_set: Set[str] = set()
    if not os.path.exists(directory_path):
        print(f"错误：路径不存在或无法访问 -> {directory_path}")
        return package_set

    for item_name in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, item_name)):
            package_name = extract_package_name(item_name)
            package_set.add(package_name)
            
    return package_set

def get_blackbox_whitebox_only_intersection() -> Set[str]:
    """
    计算 '仅在 黑盒 & 白盒 中共有' 的包名集合。
    """
    print("--- 正在计算目标包名列表 ---")
    
    # 1. 获取三个集合
    blackbox_packages = get_packages_from_dir(BLACKBOX_DIR)
    whitebox_packages = get_packages_from_dir(WHITEBOX_DIR)
    mapping_packages = get_packages_from_dir(MAPPING_DIR)
    
    print(f"已读取黑盒文件数: {len(blackbox_packages)}")
    print(f"已读取白盒文件数: {len(whitebox_packages)}")
    print(f"已读取Mapping文件数: {len(mapping_packages)}\n")
    
    # 2. 计算 '仅在 黑盒 & 白盒 中共有' 的包名
    # (Blackbox ∩ Whitebox) - Mapping
    common_bw_only = (blackbox_packages & whitebox_packages) - mapping_packages
    
    return common_bw_only

def move_files(package_names_to_move: Set[str]):
    """
    根据包名列表，剪切对应的 Blackbox APK 文件到目标文件夹。
    """
    if not package_names_to_move:
        print("没有找到需要移动的包名。操作结束。")
        return

    # 1. 创建目标文件夹（如果不存在）
    if not os.path.exists(DESTINATION_DIR):
        print(f"目标文件夹不存在，正在创建: {DESTINATION_DIR}")
        os.makedirs(DESTINATION_DIR)
    
    # 2. 遍历黑盒源文件夹，查找匹配的文件
    moved_count = 0
    
    print("--- 正在执行文件剪切操作 (Move) ---")
    
    for filename in os.listdir(BLACKBOX_DIR):
        full_source_path = os.path.join(BLACKBOX_DIR, filename)
        
        # 仅处理文件
        if os.path.isfile(full_source_path):
            package_name = extract_package_name(filename)
            
            # 检查这个文件的包名是否在我们的目标列表中
            if package_name in package_names_to_move:
                # 构造目标路径
                full_destination_path = os.path.join(DESTINATION_DIR, filename)
                
                try:
                    # 使用 shutil.move 执行剪切操作
                    shutil.move(full_source_path, full_destination_path)
                    print(f"✅ 成功剪切: {filename}")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ 剪切失败 {filename}: {e}")

    print("\n" + "=" * 60)
    print(f"操作完成！")
    print(f"原始目标包名数量: {len(package_names_to_move)}")
    print(f"成功剪切文件数量: {moved_count}")
    print(f"文件已被剪切到: {DESTINATION_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    # 1. 计算出需要移动的包名集合
    target_packages = get_blackbox_whitebox_only_intersection()
    
    print(f"需要移动的 '仅在黑盒 & 白盒中共有' 包名数量: **{len(target_packages)}**")
    print(f"列表: {sorted(list(target_packages))}\n")
    
    # 2. 根据集合执行文件移动操作
    move_files(target_packages)


# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================
# ========================================================================================

import os
from typing import Set

BLACKBOX_DIR = r"D:\LibProbe\ground_truth\blackbox_apk"
WHITEBOX_DIR = r"D:\LibProbe\ground_truth\whitebox_apk"
MAPPING_DIR = r"D:\LibProbe\ground_truth\mapping"


def extract_package_name(filename: str) -> str:
    """
    根据文件名，提取 Package Name。
    规则: 文件名部分，取最后一个下划线 '_' 之前的所有内容。
    """
    # 找到最后一个下划线 '_' 的位置
    last_underscore_index = filename.rfind('_')
    
    # 截取下划线之前的部分作为包名
    if last_underscore_index != -1:
        return filename[:last_underscore_index]
    else:
        # 如果没有下划线（不太可能，但作为防御性编程），返回不含扩展名的部分
        return os.path.splitext(filename)[0]

def get_packages_from_dir(directory_path: str) -> Set[str]:
    """
    遍历指定文件夹，提取所有文件的包名并返回一个集合 (Set)。
    """
    package_set: Set[str] = set()
    
    if not os.path.exists(directory_path):
        print(f"错误：路径不存在或无法访问 -> {directory_path}")
        return package_set

    # 遍历文件夹中的所有文件和文件夹
    for item_name in os.listdir(directory_path):
        full_path = os.path.join(directory_path, item_name)
        
        # 仅处理文件 (跳过子文件夹)
        if os.path.isfile(full_path):
            # 这里我们只将文件名 (item_name) 传给提取函数，因为后缀名已经在 item_name 中
            package_name = extract_package_name(item_name)
            package_set.add(package_name)
            
    return package_set

def compare_packages():
    """
    执行包名提取、集合运算和结果输出。
    """
    print("--- 1. 正在读取文件并提取包名集合 ---")
    
    # 获取三个集合
    blackbox_packages = get_packages_from_dir(BLACKBOX_DIR)
    whitebox_packages = get_packages_from_dir(WHITEBOX_DIR)
    mapping_packages = get_packages_from_dir(MAPPING_DIR)

    # 打印初始统计
    print(f"黑盒 ({os.path.basename(BLACKBOX_DIR)}) 包名总数: {len(blackbox_packages)}")
    print(f"白盒 ({os.path.basename(WHITEBOX_DIR)}) 包名总数: {len(whitebox_packages)}")
    print(f"Mapping ({os.path.basename(MAPPING_DIR)}) 包名总数: {len(mapping_packages)}\n")

    # --- 2. 集合运算和比对 ---

    # 总体交集
    common_to_all = blackbox_packages & whitebox_packages & mapping_packages

    # 独有部分 (仅存在于其中一个集合)
    only_in_blackbox = blackbox_packages - whitebox_packages - mapping_packages
    only_in_whitebox = whitebox_packages - blackbox_packages - mapping_packages
    only_in_mapping = mapping_packages - blackbox_packages - whitebox_packages
    
    # 两两交集（排除三者共有）
    common_bw_only = (blackbox_packages & whitebox_packages) - mapping_packages
    common_bm_only = (blackbox_packages & mapping_packages) - whitebox_packages
    common_wm_only = (whitebox_packages & mapping_packages) - blackbox_packages

    # --- 3. 结果输出 ---
    
    print("=" * 60)
    print("--- 详细统计结果 (按交集和独有部分分类) ---")
    print("=" * 60)

    # A. 三者共有的部分
    print(f"A. 三者共有的包名 (Blackbox & Whitebox & Mapping): **{len(common_to_all)}** 个")
    print(f"   列表: {sorted(list(common_to_all))}\n")

    # B. 两两共有的部分 (不含第三者)
    print("B. 仅在两组中出现的包名:")
    print(f"   - 仅在 黑盒 & 白盒 中共有: **{len(common_bw_only)}** 个")
    print(f"     列表: {sorted(list(common_bw_only))}")

    print(f"   - 仅在 黑盒 & Mapping 中共有: **{len(common_bm_only)}** 个")
    print(f"     列表: {sorted(list(common_bm_only))}")
    
    print(f"   - 仅在 白盒 & Mapping 中共有: **{len(common_wm_only)}** 个")
    print(f"     列表: {sorted(list(common_wm_only))}\n")

    # C. 某个集合独有的部分
    print("C. 仅在某个集合中独有的包名:")
    print(f"   - 仅存在于 **黑盒 (Blackbox)** 中的包名: **{len(only_in_blackbox)}** 个")
    print(f"     列表: {sorted(list(only_in_blackbox))}")

    print(f"   - 仅存在于 **白盒 (Whitebox)** 中的包名: **{len(only_in_whitebox)}** 个")
    print(f"     列表: {sorted(list(only_in_whitebox))}")

    print(f"   - 仅存在于 **Mapping** 中的包名: **{len(only_in_mapping)}** 个")
    print(f"     列表: {sorted(list(only_in_mapping))}")
    
    print("\n" + "=" * 60)
    
    total_unique = len(blackbox_packages | whitebox_packages | mapping_packages)
    print(f"所有文件中不重复的包名总数 (总并集): **{total_unique}** 个")
    print(f"（核对: {len(common_to_all) + len(common_bw_only) + len(common_bm_only) + len(common_wm_only) + len(only_in_blackbox) + len(only_in_whitebox) + len(only_in_mapping)}）")


# 运行代码
if __name__ == "__main__":
    compare_packages()