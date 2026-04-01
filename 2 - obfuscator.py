import time
import os
import re
import glob
import sys
import tarfile
import shutil
import subprocess
from typing import List, Optional

SOURCE_DIR      = r"D:\LibProbe\whitebox_apk_source"  # 存放 .tar.gz 源码包
TEMP_DIR        = r"D:\LibProbe\temp"                 # 中间工作目录
WHITEBOX_DIR    = r"D:\LibProbe\whitebox_apk"         # 未混淆 APK 输出目录
BLACKBOX_DIR    = r"D:\LibProbe\blackbox_apk"         # 混淆后 APK 输出目录
MAPPING_DIR     = r"D:\LibProbe\mapping"              # mapping.txt 文件输出目录
LOG_FILE = r"D:\LibProbe\build_log.txt"
INFO_FILE       = r"D:\LibProbe\info.txt"     # 记录已处理文件的路径
TIME_LOG_FILE = r"D:\LibProbe\obfuscator-time.txt"
GRADLE_VERSIONS = ["9.0.0", "8.12.1"]
GRADLE_PATH = r"C:\Users\tyler\.gradle\wrapper\dists\gradle-{version}\bin\gradle.bat"  
JDK_PATHS = [
    r"C:\Java\jdk-17.0.16",
    r"C:\Java\jdk-21.0.8",
    r"C:\Java\jdk-11.0.28",
]

PROGUARD_RULES = """
-dontusemixedcaseclassnames
-dontskipnonpubliclibraryclasses
-dontpreverify
-verbose
-optimizations !code/simplification/arithmetic,!code/simplification/cast,!field/*,!class/merging/*
-optimizationpasses 5
-allowaccessmodification
-keepattributes *Annotation*
-keep class android.** { *; }
-keepclassmembers enum * { *; }
-keep class kotlin.** { *; }
-keep public class com.google.vending.licensing.ILicensingService
-keep public class com.android.vending.licensing.ILicensingService
-keepclasseswithmembernames class * { native <methods>; }
-keepclassmembers public class * extends android.view.View { void set*(***); *** get*(); }
-keepclassmembers class * extends android.app.Activity { public void *(android.view.View); }
-keepclassmembers enum * { public static **[] values(); public static ** valueOf(java.lang.String); }
-keepclassmembers class * implements android.os.Parcelable { public static final android.os.Parcelable$Creator CREATOR; }
-keepclassmembers class **.R$* { public static <fields>; }
-keep class lombok.Generated { *; }
-keep class javax.annotation.** { *; }
-keep class javax.el.** { *; }
-keep class org.ietf.** { *; }
-keep @interface lombok.** { *; }
-dontwarn lombok.**
-dontwarn android.support.**
"""

class Tee:
    """
    一个用于将输出同时重定向到多个文件或流的类。
    """
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

def run_cmd(cmd: List[str], cwd: Optional[str] = None, shell: bool = True, env=None):
    """
    执行命令并实时输出到控制台和日志文件。
    """
    # 将命令列表转换为字符串，以便在shell模式下执行
    cmd_str = " ".join(cmd)
    
    # 这个print语句现在会被全局重定向到日志文件中
    print(f">>> 执行命令：{cmd_str} (cwd={cwd})")
    
    try:
        # Popen 的 stdout 和 stderr 需要设置为 PIPE 才能捕获
        # 并将子进程的输出重定向到主脚本的stdout，由Tee类统一处理
        proc = subprocess.Popen(
            cmd_str,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=shell,
            env=env
        )
        
        # 实时读取并输出每一行
        for line in iter(proc.stdout.readline, ''):
            sys.stdout.write(line)
        
        proc.wait()
        
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
    
    except Exception as e:
        # error_msg = f"命令执行失败: {e}"
        # 这个print语句现在会被全局重定向到日志文件中
        # print(error_msg, file=sys.stderr)
        raise

def safe_mkdir(path: str):
    os.makedirs(path, exist_ok=True)
    
def safe_rmtree(path: str, retries: int = 5, delay: int = 1):
    """
    尝试多次删除目录，以解决进程占用问题。
    """
    for i in range(retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                print(f"[清理完成] 已成功删除 {path}。")
            return
        except OSError as e:
            print(f"[清理警告] 尝试删除 {path} 失败 (第 {i+1} 次): {e}")
            time.sleep(delay)  # 等待一段时间后重试
    
    print(f"[清理失败] 无法删除目录 {path}，请手动检查是否有进程占用。")
    
def extract_tar_gz(tar_path, extract_to_dir):    
    # 清理旧的解压目录
    if os.path.exists(extract_to_dir):
        shutil.rmtree(extract_to_dir)
    os.makedirs(extract_to_dir, exist_ok=True)
    
    # 解压文件
    with tarfile.open(tar_path, "r:*") as tar:
        tar.extractall(path=extract_to_dir)
    print(f"[解压完成] {tar_path} -> {extract_to_dir}")
    
    # 智能处理解压后多余的顶层目录
    extracted_contents = os.listdir(extract_to_dir)
    if len(extracted_contents) == 1:
        nested_dir = os.path.join(extract_to_dir, extracted_contents[0])
        if os.path.isdir(nested_dir):
            print(f"[INFO] 发现嵌套目录，将内容移动到 {extract_to_dir}。")
            # 将嵌套目录下的所有内容移动到顶层目录
            for item in os.listdir(nested_dir):
                shutil.move(os.path.join(nested_dir, item), extract_to_dir)
            shutil.rmtree(nested_dir)

# 查找项目根目录
def find_project_root(extracted_dir: str) -> str:
    """
    递归查找真正的 Android 项目根目录
    """
    for root, dirs, files in os.walk(extracted_dir):
        files_set = set(files)
        # 优先查找包含 settings.gradle 的目录
        if "settings.gradle" in files_set or "settings.gradle.kts" in files_set:
            # 找到根目录，直接返回
            print(f"[项目根] {root} (via settings.gradle)")
            return root
        # 退而求其次，查找包含 build.gradle 的目录，但确保不是临时子目录
        if ("build.gradle" in files_set or "build.gradle.kts" in files_set) and "app" in dirs:
            print(f"[项目根] {root} (via build.gradle)")
            return root
    
    print(f"[WARN] 未找到 settings/build.gradle，使用解压根：{extracted_dir}")
    return extracted_dir

# 选取gradle版本
def generate_wrapper(project_dir: str, version: str, env):
    """
    在项目目录中生成 Gradle wrapper 文件
    """
    gradlew_bat_path = os.path.join(project_dir, "gradlew.bat")
    
    if os.path.exists(gradlew_bat_path):
        print(f"在 {project_dir} 中已找到 gradlew.bat，跳过。")
        return

    print(f"在 {project_dir} 中未找到 gradlew.bat，正在尝试生成...")
    local_gradle_path = GRADLE_PATH.format(version=version)

    if os.path.exists(local_gradle_path):
        try:
            print(f"正在使用本地 Gradle {version} 生成 wrapper...")
            run_cmd([local_gradle_path, "wrapper", "--gradle-version", version],
                            cwd=project_dir,
                            env=env)
            print(f"成功生成 {version} 版本的 wrapper。")
        except subprocess.CalledProcessError as e:
            print(f"生成 Gradle wrapper 失败：{e}")
            raise
    else:
        print(f"错误：未找到本地 gradle.bat，请检查路径：{local_gradle_path}")
        raise FileNotFoundError(f"未找到本地 Gradle 可执行文件: {local_gradle_path}")

def ensure_wrapper_with_version(project_root: str, version: str, env) -> bool:
    """
    用指定 Gradle 版本在 project_root 生成/刷新 wrapper。
    """
    local_gradle_path = GRADLE_PATH.format(version=version)
    
    try:
        generate_wrapper(project_root, version, env)
        print(f"[INFO] 正在尝试使用本地 Gradle {version} 的可执行文件...")
        run_cmd([local_gradle_path, "wrapper"], cwd=project_root, env=env)
        print("[INFO] 成功使用本地 'gradle.bat' 命令生成 wrapper。")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[警告] 使用本地 Gradle {version} 失败：{e}")
        return False

# 构建 APK
def build_apk(source_root: str, gradle_path: str, env) -> str:
    build_cmd = [gradle_path, "clean", "assembleRelease"]
    extra_args = ["--no-daemon", "--stacktrace"]
    build_cmd.extend(extra_args)
    
    run_cmd(build_cmd, cwd=source_root, env=env)
    
    print("[INFO] 正在递归查找 release APK 文件...")
    # 查找所有子目录下的 "release" 文件夹中的 "*.apk" 文件
    apk_path_glob = os.path.join(source_root, "**", "release", "*.apk")
    candidates = glob.glob(apk_path_glob, recursive=True)
    
    if not candidates:
        print("--- 正在清理旧的 Gradle 进程... ---")
        try:
            run_cmd(["taskkill", "/f", "/im", "java.exe"], shell=True)
            run_cmd(["taskkill", "/f", "/im", "gradlew.bat"], shell=True)
        except Exception as e:
            pass
        safe_rmtree(source_root)
        print(f"[清理完成] 已删除 {source_root}。")
        raise FileNotFoundError("未找到混淆后的 release APK。")
    
    candidates.sort(key=os.path.getmtime, reverse=True)
    obf_apk_path = candidates[0]
    return obf_apk_path

# 搜寻模块目录的路径
def find_module_dir(project_root: str) -> List[str]:
    """
    通过解析 settings.gradle 文件来查找所有 Android 模块目录。
    返回一个包含所有模块目录路径的列表。
    """
    # print("[INFO] 正在通过解析 settings.gradle 文件来查找所有应用模块目录...")
    
    settings_file_path = None
    # 递归查找 settings.gradle 或 settings.gradle.kts
    for root, _, files in os.walk(project_root):
        if 'settings.gradle' in files:
            settings_file_path = os.path.join(root, 'settings.gradle')
            break
        if 'settings.gradle.kts' in files:
            settings_file_path = os.path.join(root, 'settings.gradle.kts')
            break
    
    found_modules = []
    
    if settings_file_path:
        with open(settings_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找所有被 include 的模块名
            module_names = re.findall(r"include\s*\(?[':\"](.+?)[':\"]\)?", content)
            
            for name in module_names:
                # 将 Gradle 路径（如 ':my-module'）转换为文件系统路径
                parts = name.split(':')
                module_folder_name = parts[-1]  # 获取最后一级目录名
                
                # 在项目根目录中递归搜索对应的文件夹
                search_path = os.path.join(project_root, "**", module_folder_name)
                # glob.glob 返回一个列表，我们遍历所有匹配项
                found_dirs = glob.glob(search_path, recursive=True)
                
                for found_dir in found_dirs:
                    if os.path.isdir(found_dir) and (any(f.endswith('.gradle') for f in os.listdir(found_dir))
                                                    or any(f.endswith('.gradle.kts') for f in os.listdir(found_dir)) 
                                                    or any(f.endswith('.properties') for f in os.listdir(found_dir)) 
                                                    or any(f.endswith('.pro') for f in os.listdir(found_dir)) 
                                                     ):
                        # print(f"[INFO] 找到模块目录：{found_dir}")
                        found_modules.append(found_dir)
    
    return found_modules

# 1、修改 gradle.properties
def edit_gradle_properties(project_root, is_obfuscate):
    minify_value = "true" if is_obfuscate else "false"

    app_dirs = find_module_dir(project_root)
    for app_dir in app_dirs:
        gradle_properties_path = os.path.join(app_dir, 'gradle.properties')

        if os.path.exists(gradle_properties_path):
            with open(gradle_properties_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            found_r8_line = False
            new_lines = []
            for line in lines:
                if line.strip().startswith('android.enableR8'):
                    new_lines.append(f'android.enableR8.fullMode={minify_value.lower()}\n')
                    found_r8_line = True
                else:
                    new_lines.append(line)
            
            if not found_r8_line:
                new_lines.append(f'# Enabled R8 full mode for obfuscation\n')
                new_lines.append(f'android.enableR8.fullMode={minify_value.lower()}\n')
                
            with open(gradle_properties_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            print(f"[INFO] 已在 {os.path.basename(gradle_properties_path)} 中 {'启用' if is_obfuscate else '关闭'} android.enableR8.fullMode。")

        else:
            # 文件不存在，创建新文件
            try:
                with open(gradle_properties_path, 'w', encoding='utf-8') as f:
                    f.write(f'# Enabled R8 full mode for obfuscation\n')
                    f.write(f'android.enableR8.fullMode={minify_value.lower()}\n')
                print(f"[INFO] 未找到 gradle.properties，已在项目根目录创建新文件并 {'启用' if is_obfuscate else '关闭'} android.enableR8.fullMode。")
            except IOError as e:
                print(f"[错误] 无法创建 gradle.properties 文件：{e}")

# 修改 gradle.properties 以设置 Java home
def set_gradle_java_home(project_root: str, java_home_path: str):
    """
    修改项目的 gradle.properties 文件，以确保 Gradle 使用指定的 Java home。
    """
    sanitized_path = java_home_path.replace('\\', '/')
    app_dirs = find_module_dir(project_root)
    for app_dir in app_dirs:
        gradle_properties_path = os.path.join(app_dir, 'gradle.properties')
        if not os.path.exists(gradle_properties_path):
            with open(gradle_properties_path, 'w', encoding='utf-8') as f:
                f.write(f'# Created by script to set a specific Java home\n')
                f.write(f'org.gradle.java.home={sanitized_path}\n')
            print(f"[INFO] 未找到 gradle.properties，已创建新文件并设置 org.gradle.java.home。")
            return

        lines = []
        found_java_home = False
        with open(gradle_properties_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated_lines = []
        for line in lines:
            if line.strip().startswith('org.gradle.java.home'):
                updated_lines.append(f'org.gradle.java.home={sanitized_path}\n')
                found_java_home = True
            else:
                updated_lines.append(line)

        if not found_java_home:
            updated_lines.append(f'\n# Added by script to set a specific Java home\n')
            updated_lines.append(f'org.gradle.java.home={sanitized_path}\n')
        
        with open(gradle_properties_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"[INFO] 已在 gradle.properties 中设置 org.gradle.java.home={sanitized_path}。")

# 2、修改 build.gradle 或 build.gradle.kts    
def find_block_content(text, start_pattern):
    """
    通过括号计数法查找并返回一个闭包的完整内容及其内部内容的字符串。
    这是一个更健壮的方法，可以处理嵌套的闭包。
    返回: (完整匹配文本, 闭包内部文本)
    """
    start_match = re.search(start_pattern, text, re.DOTALL)
    if not start_match:
        return None, None
    
    start_index = start_match.start()
    content_start_index = start_match.end()
    
    open_braces = 1
    end_index = -1
    for i in range(content_start_index, len(text)):
        if text[i] == '{':
            open_braces += 1
        elif text[i] == '}':
            open_braces -= 1
            if open_braces == 0:
                end_index = i
                break
    
    if end_index == -1:
        return None, None

    # 完整匹配从开始模式到结束括号
    full_match = text[start_index:end_index + 1]
    # 内部内容从开始括号之后到结束括号之前
    inner_content = text[content_start_index:end_index]
    return full_match, inner_content

def edit_build_gradle(project_root, is_obfuscate):
    """
        A = android
        B = build_types
        R = release
    """
    file_path = ""
    app_dirs = find_module_dir(project_root)
    for app_dir in app_dirs:
        if app_dir:
            paths_to_check = [
                os.path.join(app_dir, 'build.gradle'),
                os.path.join(app_dir, 'build.gradle.kts')
            ]
            for p in paths_to_check:
                if os.path.exists(p):
                    file_path = p
                    break
        
        if not file_path:
            print(f"[WARN] 在项目 {os.path.basename(project_root)} 中未找到 build.gradle 或 build.gradle.kts 文件，跳过。")
            return

        minify_value = "true" if is_obfuscate else "false"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"[错误] 文件未找到：{file_path}")
            return

        is_kotlin = file_path.endswith('.kts')
        
        if is_kotlin:
            minify_text = f'isMinifyEnabled = {minify_value}'
            shrink_text = f'isShrinkResources = {minify_value}'
            proguard_text = 'proguardFiles(\n            getDefaultProguardFile("proguard-android-optimize.txt"),\n            "proguard-rules.pro"\n        )'
            R_template = f'''
            release {{
                {minify_text}
                {shrink_text}
                {proguard_text}
            }}'''
            B_template = f'''
        buildTypes {{
            {R_template}
        }}'''
        else:  # Groovy
            minify_text = f'minifyEnabled {minify_value}'
            shrink_text = f'shrinkResources {minify_value}'
            proguard_text = "proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'"
            R_template = f'''
            release {{
                {minify_text}
                {shrink_text}
                {proguard_text}
            }}'''
            B_template = f'''
        buildTypes {{
            {R_template}
        }}'''

        # 1. 精确查找 android {} 闭包
        A_full, A_content = find_block_content(content, r'android\s*\{')

        if not A_full:
            print(f"[WARN] 未找到 android 闭包，无法修改 {os.path.basename(file_path)}。")
            return

        # 2. 在 android 闭包内部查找 buildTypes {} 闭包
        B_full, B_content = find_block_content(A_content, r'buildTypes\s*\{')

        final_content = content
        if B_full:
            # 3. 在 buildTypes 闭包内部查找 release {} 闭包
            R_full, R_content = find_block_content(B_content, r'(?:release|getByName\("release"\)|all)\s*\{')

            if R_full:
                # 替换 minifyEnabled 和 shrinkResources
                new_R_content = re.sub(r'(?:isMinifyEnabled|minifyEnabled)\s*=\s*(?:true|false)|(?:isMinifyEnabled|minifyEnabled)\s*(?:true|false)', minify_text, R_content, flags=re.IGNORECASE)
                new_R_content = re.sub(r'(?:isShrinkResources|shrinkResources)\s*=\s*(?:true|false)|(?:isShrinkResources|shrinkResources)\s*(?:true|false)', shrink_text, new_R_content, flags=re.IGNORECASE)
                
                # 替换所有 proguardFiles 配置行
                proguard_pattern = re.compile(r'^\s*proguardFiles.*', re.MULTILINE | re.DOTALL)
                if re.search(proguard_pattern, new_R_content):
                    new_R_content = re.sub(proguard_pattern, f'            {proguard_text}', new_R_content)
                else:
                    new_R_content += f'\n            {proguard_text}'
                
                # 从内向外进行替换
                new_R_full = R_full.replace(R_content, new_R_content)
                new_B_full = B_full.replace(R_full, new_R_full)
                final_A_full = A_full.replace(B_full, new_B_full)
                final_content = content.replace(A_full, final_A_full)

            else:
                # 未找到 release，在 buildTypes 闭包末尾添加
                # 找到 buildTypes 闭包内容的结束点，然后在其前插入
                end_brace_index = B_full.rfind('}')
                new_B_full = B_full[:end_brace_index] + R_template + '\n' + B_full[end_brace_index:]
                final_A_full = A_full.replace(B_full, new_B_full)
                final_content = content.replace(A_full, final_A_full)
        else:
            # 未找到 buildTypes，在 android 闭包末尾添加
            end_brace_index = A_full.rfind('}')
            new_A_full = A_full[:end_brace_index] + B_template + '\n' + A_full[end_brace_index:]
            final_content = content.replace(A_full, new_A_full)

        if final_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"[INFO] 已修改 {os.path.basename(file_path)}，为 release 构建{'启用' if is_obfuscate else '关闭'}混淆。")
        else:
            print(f"[INFO] {os.path.basename(file_path)} 内容未发生变化，无需修改。")

# 3、处理混淆规则文件
def edit_proguard_rules(project_root, is_obfuscate, is_append_missing_rules = False):
    """
    根据项目根目录和混淆状态，修改或清空混淆规则文件。
    该函数会自动查找 build.gradle 文件并确定规则文件的路径。
    """
    file_path = ""
    proguard_rules_paths = []
    app_dirs = find_module_dir(project_root)
    for app_dir in app_dirs:
        if app_dir:
            paths_to_check = [
                os.path.join(app_dir, 'build.gradle'),
                os.path.join(app_dir, 'build.gradle.kts')
            ]
            for p in paths_to_check:
                if os.path.exists(p):
                    file_path = p
                    break
        
        if not file_path:
            print(f"[WARN] 在项目 {os.path.basename(project_root)} 中未找到 build.gradle 或 build.gradle.kts 文件，跳过。")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"[错误] 文件未找到：{file_path}")
            return
        
        # 1. 查找所有包含 'proguardFiles' 的行
        proguard_lines = re.findall(r"^\s*proguard(?:Files|File)\s*.*$", content, re.MULTILINE)
        
        proguard_rules_name = 'proguard-rules.pro'  # 默认值
        
        if proguard_lines:
            # 2. 从最后一个配置行中提取混淆规则文件名
            last_line = proguard_lines[-1]
            quoted_files = re.findall(r"['\"]([^'\"]+)['\"]", last_line)
            
            if quoted_files:
                # 找到最后一个非默认的规则文件作为目标
                custom_files = [f for f in quoted_files if 'proguard-android' not in f]
                if custom_files:
                    proguard_rules_name = custom_files[-1]
                else:
                    # 如果没有自定义规则文件，则选择最后一个
                    proguard_rules_name = quoted_files[-1]

        # 确定混淆规则文件的绝对路径
        proguard_rules_path = os.path.join(os.path.dirname(file_path), proguard_rules_name)
        os.makedirs(os.path.dirname(proguard_rules_path), exist_ok=True)

        proguard_rules_paths.append(proguard_rules_path)
        
        if is_obfuscate:
            # 开启混淆，覆盖文件
            with open(proguard_rules_path, 'w', encoding='utf-8') as f:
                f.write(PROGUARD_RULES)
            print(f"[INFO] 开启混淆，已将混淆规则写入 {os.path.basename(proguard_rules_path)} 文件。")
        else:
            # 关闭混淆，清空文件
            if os.path.exists(proguard_rules_path):
                with open(proguard_rules_path, 'w', encoding='utf-8') as f:
                    f.write("")
                print(f"[INFO] 关闭混淆，已清空 {os.path.basename(proguard_rules_path)} 文件。")
            else:
                print(f"[警告] 未找到混淆规则文件 {proguard_rules_name}，无需清空。")
    
    if is_append_missing_rules:
        return proguard_rules_paths

# 开启或关闭混淆
def update_build_gradle(project_root: str, is_obfuscate: bool):
    edit_gradle_properties(project_root, is_obfuscate)
    edit_build_gradle(project_root, is_obfuscate)
    edit_proguard_rules(project_root, is_obfuscate)

def append_missing_rules(project_root: str):
    """
    在构建失败后，查找并追加 R8 生成的 missing_rules.txt 到项目的混淆规则文件中。
    """
    print("--- 正在查找并追加缺失的混淆规则... ---")
    
    # R8 通常会在这个路径下生成文件，但我们用 glob 确保找到
    # 这里也许有多个missing_rules.txt，暂不解决
    missing_rules_glob = os.path.join(project_root, "**", "missing_rules.txt")
    candidates = glob.glob(missing_rules_glob, recursive=True)

    if not candidates:
        print("[警告] 未找到任何 missing_rules.txt 文件。")
        return False
        
    # 选择最新的一个
    candidates.sort(key=os.path.getmtime, reverse=True)
    missing_rules_path = candidates[0]
    
    # 找到项目的混淆规则文件
    proguard_rules_paths = edit_proguard_rules(project_root, is_append_missing_rules = True)
    for proguard_rules_path in proguard_rules_paths:
        if not os.path.exists(proguard_rules_path):
            print("[警告] 目标混淆规则文件不存在，无法追加规则。")
            return False

        with open(missing_rules_path, 'r', encoding='utf-8') as f_missing:
            missing_rules_content = f_missing.read()
        
        # 将缺失的规则追加到混淆规则文件中
        with open(proguard_rules_path, 'a', encoding='utf-8') as f_proguard:
            f_proguard.write("\n# AUTO-GENERATED MISSING RULES\n")
            f_proguard.write(missing_rules_content)
        
        print(f"[成功] 已将 {os.path.basename(missing_rules_path)} 的规则追加到 {os.path.basename(proguard_rules_path)}。")
    
    return True

# 尝试使用多个本地 JDK 和 Gradle 版本来构建 APK，直到成功为止
def build_with_jdks(source_root: str, project_name: str, is_obfuscate: bool, gradle_versions: List[str], jdk_paths: List[str]) -> bool:
    safe_mkdir(BLACKBOX_DIR if is_obfuscate else WHITEBOX_DIR)

    for jdk_path in jdk_paths:
        env = os.environ.copy()
        env['PATH'] = os.path.join(jdk_path, 'bin') + os.pathsep + env['PATH']
        env['JAVA_HOME'] = jdk_path
        
        print(f"\n--- 正在尝试使用 JDK: {os.path.basename(jdk_path)} ---")

        try:
            set_gradle_java_home(source_root, jdk_path)
            update_build_gradle(source_root, is_obfuscate)
        except Exception as e:
            print(f"[警告] 配置构建文件失败，跳过此 JDK: {e}")
            continue

        apk_built = False
        for version in gradle_versions:
            retries = 2 # 为每个版本设置重试次数

            while retries > 0:
                retries -= 1

                try:
                    print("--- 正在清理旧的 Gradle 进程... ---")
                    try:
                        run_cmd(["taskkill", "/f", "/im", "java.exe"], shell=True)
                        run_cmd(["taskkill", "/f", "/im", "gradlew.bat"], shell=True)
                    except Exception as e:
                        pass

                    # safe_rmtree(r"C:\Users\tyler\.gradle\daemon")
                    # safe_rmtree(r"C:\Users\tyler\.gradle\caches")
                    print(f"[尝试] 使用 Gradle {version} 和 JDK {os.path.basename(jdk_path)} 构建...")

                    if not ensure_wrapper_with_version(source_root, version, env):
                        print(f"[警告] 无法为 {source_root} 生成 {version} 版本的 wrapper。")
                        continue

                    local_gradle_path = GRADLE_PATH.format(version=version)

                    raw_apk = build_apk(source_root, local_gradle_path, env)

                    output_dir = BLACKBOX_DIR if is_obfuscate else WHITEBOX_DIR
                    output_file = os.path.join(output_dir, f"{project_name}_{'blackbox' if is_obfuscate else 'whitebox'}.apk")
                    shutil.copy(raw_apk, output_file)
                    print(f"[成功保存] {output_file}")
                    
                    apk_built = True
                    break
                except subprocess.CalledProcessError as e:
                    print(f"[失败] 构建失败，尝试下一个 Gradle 版本...")
                    try:
                        # 重新运行命令，但这次只捕获输出用于分析
                        analysis_process = subprocess.run(
                            [local_gradle_path, "assembleRelease", "--stacktrace"], 
                            cwd=source_root, 
                            env=env, 
                            capture_output=True, 
                            text=True,
                            shell=True,
                            timeout=900 # 设置一个合理的超时，避免卡住
                        )
                        # 分析捕获的输出
                        log_output = analysis_process.stdout + analysis_process.stderr
                        
                        # 只有在混淆构建失败时，并且错误信息包含 R8 混淆相关的关键字时，才自动追加规则
                        if is_obfuscate and ("Missing classes detected while running R8" in log_output or "proguard" in log_output):
                            print("--- 发现 R8 混淆错误，正在尝试自动修复... ---")
                            if append_missing_rules(source_root):
                                print("--- 已追加新规则，正在重新尝试相同版本的构建... ---")
                                continue
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        print("--- 无法捕获日志进行分析，继续下一个版本... ---")
                        continue
                    
                    # 如果不是混淆错误，或自动修复失败，则继续下一个 Gradle 版本
                    continue

        if apk_built:
            return True

    print(f"\n[严重失败] 该项目无法在任何可用 JDK 上构建。")
    record_processed_file(f"{project_name}\n")
    return False

# 处理单个压缩文件
def process_tar_gz(tar_gz_path: str):
    start_time = time.time()  # 记录开始时间
    base = os.path.basename(tar_gz_path)
    project_name = re.sub(r"\.tar\.gz$", "", base, flags=re.IGNORECASE).split('_')[0]
    proj_dir = os.path.join(TEMP_DIR, project_name)

    print("\n" + "=" * 80)
    print(f"开始处理：{project_name}")
    print("=" * 80)

    # 1) 清理环境
    print("--- 正在清理旧的 Gradle 进程... ---")
    try:
        run_cmd(["taskkill", "/f", "/im", "java.exe"], shell=True)
        run_cmd(["taskkill", "/f", "/im", "gradlew.bat"], shell=True)
    except Exception as e:
        pass
    
    print("[清理] 正在清空临时目录...")
    safe_rmtree(TEMP_DIR)
    safe_mkdir(TEMP_DIR)
    safe_mkdir(WHITEBOX_DIR)
    safe_mkdir(BLACKBOX_DIR)
    safe_mkdir(MAPPING_DIR)

    # 2) 解压源码包
    extract_tar_gz(tar_gz_path, proj_dir)

    # 3) 识别项目根目录
    source_root = find_project_root(proj_dir)
    print(f"[DEBUG] 使用的项目根目录：{source_root}")

    # 4) 构建未混淆的 APK
    print("--- 正在配置未混淆构建 ---")
    is_whitebox_success = build_with_jdks(source_root, project_name, is_obfuscate=False, gradle_versions=GRADLE_VERSIONS, jdk_paths=JDK_PATHS)
    
    is_blackbox_success = False
    if is_whitebox_success:
        # 5) 构建混淆后的 APK
        print("\n" + "--- 正在配置混淆构建 ---")
        is_blackbox_success = build_with_jdks(source_root, project_name, is_obfuscate=True, gradle_versions=GRADLE_VERSIONS, jdk_paths=JDK_PATHS)

    # 6) 复制 mapping.txt 文件
    if is_blackbox_success:
        print("--- 正在复制 mapping.txt ---")
        mapping_path_glob = os.path.join(source_root, "**", "mapping.txt")
        candidates = glob.glob(mapping_path_glob, recursive=True)
        
        if not candidates:
            print("[警告] 未找到任何 mapping.txt 文件。")
            mapping_source_path = None
        else:
            candidates.sort(key=os.path.getmtime, reverse=True)
            mapping_source_path = candidates[0]
        
        if mapping_source_path:
            mapping_dest_path = os.path.join(MAPPING_DIR, f"{project_name}_mapping.txt")
            try:
                shutil.copy(mapping_source_path, mapping_dest_path)
                print(f"[成功] mapping.txt 已复制到 {mapping_dest_path}")
            except Exception as e:
                print(f"[警告] 复制 mapping.txt 失败：{e}")
        else:
            print(f"[警告] 在 {source_root} 中未找到 mapping.txt 文件。")

    # 7) 清理临时目录
    print("--- 正在清理旧的 Gradle 进程... ---")
    try:
        run_cmd(["taskkill", "/f", "/im", "java.exe"], shell=True)
        run_cmd(["taskkill", "/f", "/im", "gradlew.bat"], shell=True)
    except Exception as e:
        pass
    safe_rmtree(proj_dir)
    print(f"[清理完成] 已删除 {proj_dir}。")

    # 记录处理结果
    result_status = "成功" if is_whitebox_success and is_blackbox_success else "失败"
    if not is_whitebox_success and is_blackbox_success:
        result_status = "白盒失败"
    if not is_blackbox_success and is_whitebox_success:
        result_status = "黑盒失败"
    if is_whitebox_success and is_blackbox_success:
        print(f"[完成] {project_name} - 白盒和黑盒APK均已成功构建。")
    elif not is_whitebox_success:
        print(f"[失败] {project_name} - 白盒构建失败。")
    elif is_whitebox_success and not is_blackbox_success:
        print(f"[失败] {project_name} - 黑盒构建失败。")

    end_time = time.time()  # 记录结束时间
    duration = end_time - start_time

    # 记录到新的时间日志文件
    with open(TIME_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"项目: {project_name}, 总时长: {duration:.2f} 秒, 结果: {result_status}\n")

def record_processed_file(file_name: str):
    """
    将处理过的文件名写入 info.txt，避免下次重复处理。
    """
    try:
        with open(INFO_FILE, 'a+', encoding='utf-8') as f:
            f.seek(0)
            content = f.read().splitlines()
            if file_name not in content:
                f.write(file_name + '\n')
                print(f"[记录] 已将 {file_name} 写入 info.txt。")
            else:
                print(f"[跳过记录] {file_name} 已存在于 info.txt。")
    except Exception as e:
        print(f"[错误] 写入 info.txt 失败: {e}")

# 批量处理压缩文件
def process_all_tar_gz():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
        
        safe_mkdir(SOURCE_DIR)
        tar_files = glob.glob(os.path.join(SOURCE_DIR, "*.tar.gz"))
        print(f"在 {SOURCE_DIR} 发现 {len(tar_files)} 个 .tar.gz")

        processed_files = set()
        if os.path.exists(INFO_FILE):
            with open(INFO_FILE, 'r', encoding='utf-8') as f:
                processed_files = {line.strip() for line in f}

        for i, tar_file in enumerate(tar_files, 1):
            base_name = os.path.basename(tar_file)
            project_name = re.sub(r"\.tar\.gz$", "", base_name, flags=re.IGNORECASE).split('_')[0]

            if project_name in processed_files:
                print(f"[跳过] 项目 {project_name} 已处理过，跳过。")
                continue

            whitebox_apk_path = os.path.join(WHITEBOX_DIR, f"{project_name}_whitebox.apk")
            blackbox_apk_path = os.path.join(BLACKBOX_DIR, f"{project_name}_blackbox.apk")

            if os.path.exists(whitebox_apk_path) and os.path.exists(blackbox_apk_path):
                print(f"[跳过] 项目 {project_name} 的白盒和黑盒 APK 文件已存在，跳过处理。")
                continue # 跳过当前循环，进入下一个文件

            print(f"\n[{i}/{len(tar_files)}] 处理：{tar_file}")
            try:
                process_tar_gz(tar_file)
                record_processed_file(project_name)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR][子进程失败] {tar_file} ：{e}")
            except Exception as e:
                print(f"[ERROR] {tar_file} ：{e}")
    
    sys.stdout = original_stdout
    sys.stderr = original_stderr

if __name__ == "__main__":
    process_all_tar_gz()
