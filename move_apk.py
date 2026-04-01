import os
import shutil
import random
from pathlib import Path

# ================= 配置区域 =================

# 源目录
SRC_ROOT = Path(r"D:\LibProbe\ground_truth\GT1")
SRC_WHITEBOX = SRC_ROOT / "whitebox_apk"
SRC_MAPPING = SRC_ROOT / "mapping"
SRC_BLACKBOX = SRC_ROOT / "blackbox_apk"

# 目标目录
DST_ROOT = Path(r"D:\LibProbe\ground_truth_part\GT1")
DST_WHITEBOX = DST_ROOT / "whitebox_apk"
DST_MAPPING = DST_ROOT / "mapping"
DST_BLACKBOX = DST_ROOT / "blackbox_apk"

# 限制条件
MAX_SIZE_MB = 20 * 1024 * 1024  # 20MB in bytes
TARGET_WHITEBOX_COUNT = 200     # 目标白盒数量
TARGET_BLACKBOX_COUNT = 50      # 目标黑盒数量 (5-10之间)

# ===========================================

def ensure_dir(path: Path):
    """如果目录不存在则创建"""
    if not path.exists():
        os.makedirs(path)
        print(f"[创建目录] {path}")

def get_project_name(filename: str, suffix: str) -> str:
    """去除后缀获取项目名 (前缀)"""
    return filename.replace(suffix, "")

def main():
    # 1. 准备目标目录
    ensure_dir(DST_WHITEBOX)
    ensure_dir(DST_MAPPING)
    ensure_dir(DST_BLACKBOX)

    print(f"正在扫描 {SRC_WHITEBOX} ...")

    # 2. 扫描并筛选符合条件的 (白盒, Mapping) 对
    valid_candidates = [] # 存储元组: (项目名, 白盒文件名, Mapping文件名)

    # 获取所有白盒文件
    whitebox_files = list(SRC_WHITEBOX.glob("*_whitebox.apk"))
    
    for wb_path in whitebox_files:
        # 2.1 检查文件大小
        if wb_path.stat().st_size > MAX_SIZE_MB:
            continue

        wb_filename = wb_path.name
        # 提取项目名 (假设格式为 ProjectName_whitebox.apk)
        project_name = get_project_name(wb_filename, "_whitebox.apk")
        
        # 2.2 检查对应的 Mapping 文件是否存在
        mapping_filename = f"{project_name}_mapping.txt"
        mapping_path = SRC_MAPPING / mapping_filename

        if mapping_path.exists():
            valid_candidates.append({
                "project": project_name,
                "wb_path": wb_path,
                "map_path": mapping_path
            })

    print(f"满足条件 (小于20MB 且 有Mapping) 的文件共有: {len(valid_candidates)} 对")

    # 3. 随机挑选 50 个白盒及其 Mapping
    selected_projects = []
    if len(valid_candidates) <= TARGET_WHITEBOX_COUNT:
        selected_projects = valid_candidates
        print(f"[提示] 符合条件的文件不足 {TARGET_WHITEBOX_COUNT} 个，将复制所有 {len(valid_candidates)} 个文件。")
    else:
        selected_projects = random.sample(valid_candidates, TARGET_WHITEBOX_COUNT)
        print(f"[筛选] 已随机挑选 {TARGET_WHITEBOX_COUNT} 对文件。")

    # 执行复制 (白盒 + Mapping)
    print("\n--- 开始复制 Whitebox 和 Mapping ---")
    for item in selected_projects:
        # 复制白盒
        shutil.copy2(item["wb_path"], DST_WHITEBOX / item["wb_path"].name)
        # 复制 Mapping
        shutil.copy2(item["map_path"], DST_MAPPING / item["map_path"].name)
        print(f"已复制: {item['project']}")

    # 4. 从这 50 个项目中，挑选 5-10 个对应的黑盒 APK
    print("\n--- 开始筛选并复制 Blackbox ---")
    
    # 找出这 50 个项目中，哪些有对应的黑盒文件
    projects_with_blackbox = []
    for item in selected_projects:
        project_name = item["project"]
        bb_filename = f"{project_name}_blackbox.apk"
        bb_path = SRC_BLACKBOX / bb_filename
        
        if bb_path.exists():
            projects_with_blackbox.append({
                "project": project_name,
                "bb_path": bb_path
            })

    print(f"在选中的项目中，有 {len(projects_with_blackbox)} 个包含对应的黑盒 APK。")

    # 随机抽取 10 个 (如果不足则全部复制)
    final_bb_count = min(len(projects_with_blackbox), TARGET_BLACKBOX_COUNT)
    selected_blackboxes = random.sample(projects_with_blackbox, final_bb_count)

    for item in selected_blackboxes:
        shutil.copy2(item["bb_path"], DST_BLACKBOX / item["bb_path"].name)
        print(f"已复制黑盒: {item['project']}")

    print("\n" + "="*30)
    print(f"任务完成！")
    print(f"白盒文件: {len(selected_projects)} -> {DST_WHITEBOX}")
    print(f"Mapping : {len(selected_projects)} -> {DST_MAPPING}")
    print(f"黑盒文件: {len(selected_blackboxes)} -> {DST_BLACKBOX}")
    print("="*30)

if __name__ == "__main__":
    main()