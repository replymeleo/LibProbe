import os
import re
import glob
import tarfile
import shutil
from typing import Optional, List, Set, Dict

# --- 配置路径常量 ---
# .tar.gz 源码包所在的目录
SOURCE_DIR = r"D:\LibProbe\whitebox_apk_source"
# 用于解压的临时工作目录
TEMP_DIR = r"D:\LibProbe\temp"
# 结果输出目录 (GT1\libnames)
OUTPUT_DIR = r"D:\LibProbe\ground_truth\GT1\libnames"

# --- 系统库/排除列表 ---
# 过滤掉系统库和常见的官方 Android/Kotlin 库
EXCLUDE_PREFIXES = [
    # Java/Android 系统和核心库
    "android", 
    "com.android.internal.util", 
    "dalvik", 
    "java", 
    "javax", 
    "org.apache", 
    "org.json", 
    "org.w3c.dom", 
    "org.xml.sax", 
    "org.xmlpull.v1", 
    "junit",
    "com.android.okhttp", 
    "org.apache.http", 
    "okio", 
    "okhttp3", 
    "com.android.org", 
    "com.android.volley",
    
    # 官方 AndroidX/Kotlin 库 - 按用户要求恢复排除
    "androidx", 
    "kotlin",   
    "kotlinx",  
    
    # Gradle/配置关键词，非库名
    "testImplementation", 
    "debugImplementation", 
    "releaseImplementation",
    "_COROUTINE", 
]

# --- 增加的常见依赖配置类型 ---
# 注意：配置类型正则将使用 re.IGNORECASE 进行匹配，所以不需要写 implementation|Implementation 等所有变体
COMMON_CONFIG_TYPES = [
    "implementation", "Implementation", "api", "compileOnly", "runtimeOnly", 
    "kapt", "ksp", "annotationProcessor", 
    "debugImplementation", "releaseImplementation", "testImplementation", 
    "compileOnlyApi", "runtimeOnlyApi", 
    "testCompileOnly", "testRuntimeOnly", 
    "providedCompile", "compile", "runtime", 
    "apk", "provided", "fullImplementation"
]
# 构建正则表达式字符串，例如 (?:implementation|api|compileOnly|...)
CONFIG_TYPES_REGEX = r'(?:' + '|'.join(COMMON_CONFIG_TYPES) + r')'


def find_project_root(extracted_dir: str) -> str:
    """
    基于 settings.gradle 递归查找真正的 Android 项目根目录。
    
    参数:
        extracted_dir: 初始解压的顶层目录。
        
    返回: 真正的项目根目录的路径 (可能是 extracted_dir 的子目录).
    """
    # 使用 os.walk 查找 settings.gradle
    for root, dirs, files in os.walk(extracted_dir):
        files_set = set(files)
        # 1. 优先查找包含 settings.gradle 的目录
        if "settings.gradle" in files_set or "settings.gradle.kts" in files_set:
            # 找到根目录，直接返回
            print(f"  [根目录] 找到项目根目录: {root} (通过 settings.gradle)")
            return root
        
        # 2. 退而求其次，查找包含 build.gradle 且存在 'app' 目录的目录
        if ("build.gradle" in files_set or "build.gradle.kts" in files_set) and "app" in dirs:
            print(f"  [根目录] 找到项目根目录: {root} (通过 build.gradle + app 目录)")
            return root

        # 阻止对嵌套模块进行深度扫描，只搜索到合理的深度
        rel_path_depth = os.path.relpath(root, extracted_dir).count(os.sep)
        if rel_path_depth > 5:
            dirs[:] = [] # 停止 os.walk 继续向下搜索

    # 备用方案：如果在遍历后没有找到确定的根目录，则使用初始解压路径
    print(f"  [根目录] 未在典型结构中找到 settings/build.gradle。使用解压根目录: {extracted_dir}")
    return extracted_dir


def extract_tar_gz(tar_path: str, temp_dir: str) -> Optional[str]:
    """
    将 .tar.gz 文件解压到临时目录。
    
    返回: *初始解压文件夹*的完整路径，如果解压失败则返回 None。
    """
    # 提取完整的项目名称（不带版本后缀），作为解压文件夹名
    project_name_full = os.path.basename(tar_path)
    project_name_dir = re.sub(r"\.tar\.gz|\.tgz|\.tar\.bz2|\.tbz$", "", project_name_full, flags=re.IGNORECASE)
    project_name_dir = project_name_dir.split('_')[0]
    
    extract_path = os.path.join(temp_dir, project_name_dir) # 这是最外层的临时目录

    # 确保目标路径是干净的
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path, exist_ok=True)

    try:
        print(f"  [解压中] 解压至: {extract_path}")
        # 使用 'r:*' 自动检测压缩格式
        with tarfile.open(tar_path, 'r:*') as tar: 
            tar.extractall(path=extract_path)
    except Exception as e:
        print(f"  [错误] 解压 {tar_path} 失败: {e}")
        return None

    # 返回初始解压目录，让 main 函数调用 find_project_root 查找真正的根目录
    return extract_path


def find_module_dir(project_root: str) -> List[str]:
    """
    通过解析 settings.gradle 文件来查找所有 Android 模块目录。

    返回: 包含所有模块目录完整路径的列表。
    """
    settings_file_path = None
    
    # 递归查找 settings.gradle 或 settings.gradle.kts (限制搜索深度)
    for root, _, files in os.walk(project_root):
        rel_path_depth = os.path.relpath(root, project_root).count(os.sep)
        if rel_path_depth > 2: # 限制对 settings 文件的搜索深度
            continue
            
        if 'settings.gradle' in files:
            settings_file_path = os.path.join(root, 'settings.gradle')
            break
        if 'settings.gradle.kts' in files:
            settings_file_path = os.path.join(root, 'settings.gradle.kts')
            break
    
    found_modules: Set[str] = set()
    
    if settings_file_path is None:
        # print("  [警告] 未找到 settings.gradle/kts 文件。") # 移动到 main 函数处理
        return []

    if settings_file_path:
        #print(f"  [模块] 正在解析 settings 文件: {settings_file_path}")
        try:
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  [错误] 读取 settings 文件失败: {e}")
            return [] 

        # 匹配任何被单引号或双引号包裹的、以冒号开头的字符串
        module_names_raw = re.findall(r"['\"]([:][a-zA-Z0-9:._-]+)['\"]", content)
        
        module_names = sorted(list(set(name.strip() for name in module_names_raw if name.strip())))
        print(f"  [解析] 发现包含的模块名: {module_names}") 
        
        for name in module_names:
            name = name.strip()
            if not name:
                continue
                
            # 将 Gradle 路径（例如 ':my-module:sub'）转换为文件系统路径
            relative_path_part = name.replace(':', os.sep).strip(os.sep)
            module_folder_name = relative_path_part.split(os.sep)[-1] 
            
            # --- 1. 尝试精确查找 settings.gradle 中定义的路径 ---
            exact_path = os.path.join(project_root, relative_path_part)
            
            # 检查: 目录存在 且 包含 build.gradle/kts 文件
            if os.path.isdir(exact_path) and (
                os.path.isfile(os.path.join(exact_path, 'build.gradle')) or 
                os.path.isfile(os.path.join(exact_path, 'build.gradle.kts'))
            ):
                found_modules.add(exact_path)
                print(f"  [解析] 模块 '{name}' 找到精确路径: {exact_path}")
                continue

            # --- 2. 备用方案：递归搜索模块文件夹名 (用于非标准项目结构) ---
            print(f"  [警告] 模块 '{name}' (期望路径: {exact_path}) 未找到，尝试递归搜索 '{module_folder_name}'...")
            
            found_by_search = False
            for root, dirs, files in os.walk(project_root):
                rel_path_depth = os.path.relpath(root, project_root).count(os.sep)
                if rel_path_depth > 5:
                    dirs[:] = [] 
                    continue
                
                # 如果当前目录名与模块名匹配，并且包含 build 文件
                if os.path.basename(root) == module_folder_name and any(f.endswith(('.gradle', '.gradle.kts')) for f in files):
                    if root not in found_modules:
                        found_modules.add(root)
                        print(f"  [解析] 模块 '{name}' 找到匹配路径: {root}")
                    found_by_search = True
                    break 
                    
            if not found_by_search:
                print(f"  [失败] 模块 '{name}' 无法通过精确路径或递归搜索找到。")


    final_modules = sorted(list(found_modules))
    #print(f"  [模块] 最终找到 {len(final_modules)} 个模块：{final_modules}")
    return final_modules

def extract_libraries_from_build_file(file_content: str) -> List[str]:
    """
    使用 re.match (逐行) 从 build.gradle/kts 文件内容中提取第三方库名。
    
    返回: 提取到的第三方库列表 (group 或 libs_key)。
    """
    extracted_libs = []
    
    # 编译正则表达式：
    # r'\s*'：匹配行首的任意空格
    # CONFIG_TYPES_REGEX：匹配依赖配置类型
    # r'(?:\s+|\()'：匹配空格 (Groovy) 或紧跟左括号 (KTS)
    # r'([^\r\n]*)'：捕获组 (1) 匹配配置后的内容
    dependency_line_pattern = re.compile(
        r'\s*' 
        + CONFIG_TYPES_REGEX 
        + r'(?:\s+|\()' 
        + r'([^\r\n]*)' 
        , re.IGNORECASE
    )

    lines = file_content.splitlines()

    #print("-" * 50)
    #print("--- 调试输出：逐行使用 re.match ---")

    # 1. 遍历每一行，使用 re.match 检查是否匹配依赖模式
    for i, line in enumerate(lines):
        match = dependency_line_pattern.match(line)
        
        if match:
            # full_match_text = match.group(0).strip()
            # 依赖内容从捕获组 (1) 获取
            dependency_content = match.group(1).strip()
            
            #print(f"[Line {i+1}] 匹配: '{full_match_text}'")

            # 针对 KTS 模式：如果内容以 ')' 结尾，则移除 (例如：处理 implementation(libs.foo))
            if dependency_content.endswith(')'):
                dependency_content = dependency_content[:-1].strip()

            # 2. 业务逻辑：提取和过滤
            
            # 2.1. 过滤单独的 '{'
            if dependency_content == '{':
                #print(f"  [跳过] 过滤单独的左花括号")
                continue
                
            # 2.2. 排除不包含第三方库的依赖声明 (项目、平台)
            # ❗ 已移除对 '$' 变量引用的排除，以便处理 "group:artifact:${version}" 格式
            if dependency_content.startswith('project(') or ' project(' in dependency_content:
                #print(f"  [排除] 项目依赖: {dependency_content}")
                continue
            if dependency_content.startswith('platform(') or ' platform(' in dependency_content:
                #print(f"  [排除] 平台依赖: {dependency_content}")
                continue
            # if '$' in dependency_content: # ❌ 原始排除逻辑已注释/删除
            #     #print(f"  [排除] 变量引用: {dependency_content}")
            #     continue

            # 2.3. 提取实际的库标识符
            library_identifier = None
            
            # A. 查找 Groovy/字符串格式 ('group:artifact:version')
            # ❗ 修改了正则表达式：只捕获第一个 ':' 之前的部分 (即 group)
            # r"['\"]([^:]+)(?::[^\"\'\s]*)?['\"]"
            # 原始: r"['\"]([^:]+:[^:]+)(?::[^\"\'\s]*)?['\"]" (捕获 group:artifact)
            quoted_dependency_match = re.search(r"['\"]([^:]+)(?::[^\"\'\s]*)?['\"]", dependency_content)
            if quoted_dependency_match:
                # library_identifier 现在是 group:artifact 或仅 group
                extracted_full = quoted_dependency_match.group(1).strip()
                
                # 进一步处理: 确保只提取 group 部分，如果匹配到 group:artifact 则只取 group
                if ':' in extracted_full:
                    # 如果匹配结果是 "group:artifact"，我们只保留 "group"
                    library_identifier = extracted_full.split(':')[0]
                else:
                    # 如果匹配结果是 "group" (例如，如果依赖只有 group)，则保留它
                    library_identifier = extracted_full
                
                # print(f"  [提取] GAV Group: {library_identifier}")
            
            # B. 查找 KTS libs. accessors 格式 (libs.key)
            elif 'libs.' in dependency_content:
                libs_match = re.search(r'\b(libs\.[\w.]+)\b', dependency_content)
                if libs_match:
                    library_identifier = libs_match.group(1).strip()
                    # print(f"  [提取] KTS 依赖: {library_identifier}")
            
            if library_identifier and ' ' not in library_identifier:
                # 确保不是一个简单的短语，例如，libs. bundles
                extracted_libs.append(library_identifier)

    # --- 3. 过滤系统库并处理 'libs.' 前缀 (完整逻辑) ---
    final_libraries = []
    
    # print("\n" + "-" * 50)
    # print("--- 过滤系统库 ---")
    
    unique_extracted_libs = list(set(extracted_libs))

    for library_full in unique_extracted_libs:
        is_excluded = False
        
        # 确定用于排除检查的字符串
        # 注意：现在 library_full 可能是 group 或 libs.key
        if library_full.startswith('libs.'):
            # 对于 libs.coil.ktor, 检查 coil.ktor
            check_string = library_full[5:]
        else:
            # 对于 group，直接检查 group (无需 : 替换)
            check_string = library_full.replace(':', '.')

        # 执行排除检查
        for prefix in EXCLUDE_PREFIXES:
            # 检查是否完全匹配或以该前缀开头 (后面跟点)
            if check_string == prefix or check_string.startswith(prefix + '.'):
                is_excluded = True
                # print(f"  [排除] 系统库: {library_full} (匹配前缀: {prefix})")
                break
        
        if not is_excluded:
            # 4. 去除 libs. 前缀并添加到最终列表
            if library_full.startswith('libs.'):
                # 最终只保留 key
                final_libraries.append(library_full[5:])
            else:
                # 最终保留 group
                final_libraries.append(library_full)

    # 5. 去重并返回
    result = sorted(list(set(final_libraries)))
    # print("-" * 50)
    #print(f"--- 最终提取结果: {len(result)} 个库 ---")
    #for lib in result:
        #print(f"  - {lib}")
        
    return result

def read_file_content(file_path: str) -> Optional[str]:
    """读取文件内容，处理异常"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  [错误] 读取文件 {file_path} 失败: {e}")
        return None

def main():
    """
    主函数：遍历、解压、提取依赖并保存结果。
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 查找所有 .tar.gz 文件
    tar_files = glob.glob(os.path.join(SOURCE_DIR, '*.tar.gz'))
    if not tar_files:
        print(f"在目录 {SOURCE_DIR} 中未找到 .tar.gz 文件。")
        return

    print(f"在 {SOURCE_DIR} 中找到 {len(tar_files)} 个 .tar.gz 文件。开始处理...")

    for i, tar_file in enumerate(tar_files, 1):
        base_name = os.path.basename(tar_file)
        
        # 提取项目名称 (例如，从 com.app.name_v1.0.tar.gz 中提取 com.app.name)
        project_name_no_ext = re.sub(r"\.tar\.gz$", "", base_name, flags=re.IGNORECASE)
        project_name = project_name_no_ext.split('_')[0] 

        print("-" * 50)
        print(f"[{i}/{len(tar_files)}] 正在处理项目: {project_name}")

        # 第 1 步: 解压到临时目录
        initial_extract_dir = extract_tar_gz(tar_file, TEMP_DIR)
        
        if not initial_extract_dir:
            print(f"  [跳过] {project_name} 解压失败。")
            continue

        # 第 1.1 步: 查找实际的项目根目录 (可能在嵌套子目录中)
        actual_project_root = find_project_root(initial_extract_dir)
        
        # 检查是否找到了有效的项目根目录
        if not (os.path.isfile(os.path.join(actual_project_root, 'settings.gradle')) or 
                os.path.isfile(os.path.join(actual_project_root, 'settings.gradle.kts')) or
                (os.path.isfile(os.path.join(actual_project_root, 'build.gradle')) or os.path.isfile(os.path.join(actual_project_root, 'build.gradle.kts')))):
            print(f"  [跳过] {project_name} 无法找到有效的项目根目录 (缺少 settings/build 文件)。")
            shutil.rmtree(initial_extract_dir, ignore_errors=True)
            print(f"  [清理] 已删除临时项目目录: {initial_extract_dir}")
            continue


        # 第 2 步: 查找所有模块目录 (基于实际的项目根目录)
        module_dirs = find_module_dir(actual_project_root)
        
        # --- 优化点：如果未找到任何模块（针对单模块项目），则尝试将项目根目录作为主模块 ---
        if not module_dirs:
            # 检查项目根目录是否包含 build 文件
            has_root_build_file = (
                os.path.isfile(os.path.join(actual_project_root, 'build.gradle')) or 
                os.path.isfile(os.path.join(actual_project_root, 'build.gradle.kts'))
            )
            
            if has_root_build_file:
                # 将根目录作为唯一的模块加入列表
                module_dirs.append(actual_project_root)
                #print(f"  [修复] 未通过 settings 文件找到模块，但根目录存在 build 文件，将其作为主模块处理。")
            else:
                # 确实没有可处理的模块/build 文件，跳过
                print(f"  [跳过] {project_name} 未能找到任何可用的模块或根目录 build 文件。")
                shutil.rmtree(initial_extract_dir, ignore_errors=True)
                print(f"  [清理] 已删除临时项目目录: {initial_extract_dir}")
                continue


        all_libraries: Set[str] = set()
        
        # 第 3 步: 从所有模块中提取依赖
        for module_dir in module_dirs:
            build_gradle_path = None
            
            # 确定 build.gradle 文件路径
            if os.path.isfile(os.path.join(module_dir, 'build.gradle')):
                build_gradle_path = os.path.join(module_dir, 'build.gradle')
            elif os.path.isfile(os.path.join(module_dir, 'build.gradle.kts')):
                build_gradle_path = os.path.join(module_dir, 'build.gradle.kts')

            if not build_gradle_path:
                print(f"  [警告] 模块 {os.path.basename(module_dir)} 不包含 build.gradle/kts 文件。跳过。")
                continue

            file_content = read_file_content(build_gradle_path)
            
            if not file_content:
                print(f"  [警告] 模块 {os.path.basename(module_dir)}: 文件内容读取失败。")
                continue
            
            # 提取第三方库
            libraries = extract_libraries_from_build_file(file_content)
            all_libraries.update(libraries)
            
            display_name = "根模块" if module_dir == actual_project_root else os.path.basename(module_dir)
            print(f"  [结果] 模块 {display_name} 找到 {len(libraries)} 个独特的库。")


        # 第 4 步: 写入结果文件
        final_libraries = sorted(list(all_libraries))
        print(f"  [最终结果] 为项目 {project_name} 找到了总共 {len(final_libraries)} 个独特的第三方库。")
        
        output_filepath = os.path.join(OUTPUT_DIR, f"{project_name}.txt")
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(final_libraries))
            print(f"  [成功] 依赖列表已保存至: {output_filepath}")
        except Exception as e:
            print(f"  [错误] 写入文件 {output_filepath} 失败: {e}")

        # 第 5 步: 清理临时目录
        shutil.rmtree(initial_extract_dir, ignore_errors=True)
        print(f"  [清理] 已删除临时项目目录: {initial_extract_dir}")

    print("-" * 50)
    print("所有文件处理完毕。")


if __name__ == "__main__":
    main()