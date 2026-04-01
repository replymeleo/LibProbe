# LibProbe: 基于双层代码结构特征的安卓第三方库识别系统

LibProbe 是一个旨在解决 **R8 编译器全量混淆**（死代码消除、方法内联、类合并等）环境下安卓第三方库识别难题的自动化工具链与算法框架。

本项目包含完整的自动化流水线：从 F-Droid 开源应用爬取与自动编译、R8 混淆与真值（Ground Truth）构建、白盒特征提取，直到最终基于双层投票机制的第三方库识别算法。

## 目录结构

```text
LibProbe/
├── 1 - fdroidapkspider.py  # F-Droid 开源代码爬虫与自动化构建脚本
├── 2 - obfuscator.py       # 自动化 R8 混淆注入与黑白盒双版本编译脚本
├── 3 - lib_extract.py      # 基于白盒 APK 的真实第三方库提取脚本
├── 4 - mapping.py          # 混淆映射解析与特征数据库 (SQLite) 构建脚本
├── move_apk.py             # 文件重定向与归档辅助脚本
├── LibProbe-V5.py          # LibProbe 核心识别算法（双层匹配+双层投票）
├── spider.txt              # 爬虫目标应用包名/URL 配置文件
├── ground_truth/           # 实验数据集与特征数据库存储目录
│   ├── db/                 # 存储生成的 SQLite 白盒特征数据库
│   ├── GT1/                # 基础数据集（白盒/黑盒APK/mapping文件/提取的库名）
│   └── GT2/                # 对照数据集（用于极端情况测试等）
├── LibScan/                # 依赖的分析工具模块（内含定制版 Androguard 等）
└── LibRadar/               # 辅助反编译与缓存目录
```

## 环境依赖与安装

本项目主要基于 Python 开发，并依赖 Android 官方构建工具集。

### 1. 系统依赖

本项目的自动化流水线涉及源码编译、二进制文件解析等重度 I/O 与计算任务，请确保您的运行环境满足以下条件，并正确配置了全局环境变量。

* **操作系统:**
  * 支持 Windows 10/11, Linux (推荐 Ubuntu 20.04+), 或 macOS。
  * **硬件建议:** 由于 F-Droid 源码包（`.tar.gz`）及生成的黑白盒 APK 数量庞大，建议预留至少 **100GB** 以上的可用磁盘空间，并推荐使用 SSD 以加速读写。

* **Java 环境 (JDK 11 或 JDK 17):**
  * **用途:** 支撑 Gradle 编译 Android 源码以及运行 Apktool。
  * **下载与安装:** 前往 Oracle 官网下载: [https://www.oracle.com/java/technologies/downloads/](https://www.oracle.com/java/technologies/downloads/)
  * **配置要求:** 安装后，请务必新建系统环境变量 `JAVA_HOME` 指向您的 JDK 安装目录，并将 `%JAVA_HOME%\bin` (Windows) 或 `$JAVA_HOME/bin` (Linux/Mac) 添加到系统的 `PATH` 环境变量中。在终端输入 `java -version` 确认安装成功。

* **Android SDK:**
  * **用途:** 提供 Android 应用构建与打包的核心工具，本项目尤其依赖 `build-tools` 中的 `apksigner`（签名）和 `zipalign`（对齐）工具。
  * **下载与安装:** * **最简方式:** 直接下载并安装 [Android Studio](https://developer.android.google.cn/studio)。安装向导会自动为您下载最新的 SDK。
    * **仅命令行方式:** 在上述页面的底部找到 "Command line tools only" 下载配置。
  * **配置要求:** 1. 新建系统环境变量 `ANDROID_HOME`，指向您的 SDK 根目录（例如 Windows 下通常为 `C:\Users\用户名\AppData\Local\Android\Sdk`）。
    2. 将 `build-tools` 目录路径（例如 `%ANDROID_HOME%\build-tools\34.0.0`）添加到系统的 `PATH` 变量中，确保在终端中可以直接运行 `apksigner` 和 `zipalign` 命令。

* **Git:**
  * **用途:** 用于在自动化脚本中克隆或拉取 F-Droid 相关的开源仓库代码。
  * **下载与安装:**
    * 前往 Git 官方网站下载对应系统的安装包: [https://git-scm.com/downloads](https://git-scm.com/downloads)
    * Ubuntu/Debian 用户可直接通过终端运行：`sudo apt update && sudo apt install git`
  * **配置要求:** 安装完成后，将 Git 的 `bin` 目录添加到系统 `PATH` 中。在终端输入 `git --version` 确认安装成功。

* **Apktool:**
  * **用途:** 逆向工程工具，用于解包（解码资源/反编译 DEX）和重新打包 APK 文件。
  * **下载与安装:** * 官方安装指南与下载地址: [https://apktool.org/](https://apktool.org/)
    * **Windows 配置步骤:**
      1. 下载官方提供的 `apktool.bat` 包装脚本。
      2. 下载最新的 Apktool `.jar` 文件（如 `apktool_2.9.3.jar`），并将其重命名为 `apktool.jar`。
      3. 将这两个文件（`apktool.bat` 和 `apktool.jar`）放在同一个文件夹中（例如 `C:\Windows` 或您自定义的、已加入 `PATH` 的工具目录）。
    * **Linux/macOS 配置步骤:** 下载包装脚本（`apktool`）和 `.jar` 文件（重命名为 `apktool.jar`），移动到 `/usr/local/bin` 目录下，并赋予这两个文件可执行权限（`chmod +x`）。
  * **配置要求:** 确保在终端的任意目录下输入 `apktool` 均能正确输出版本及帮助信息。

### 2. Python 环境安装
推荐使用 Python 3.8。在项目根目录下，执行以下命令安装依赖：

```bash
pip install requests beautifulsoup4 lxml urllib re glob tarfile shutil subprocess sqlite3 typing pathlib  random androguard==3.4.0a1 traceback collections zlib numpy panda logging hashlib tempfile

```

## 运行指南

本项目的运行分为“数据集与特征库构建阶段”（脚本 1-4）与“核心算法识别阶段”（LibProbe-V5）。请严格按照以下顺序执行：

### 阶段一：自动构建“白盒-黑盒”真值数据集

#### Step 1: 源码爬取与初始编译
配置 `spider.txt`，逐行填入需要爬取的 F-Droid 应用包名或链接。
```bash
python "1 - fdroidapkspider.py"
```
* **功能:** 爬取源码，自动识别 Gradle 环境，尝试完成初始的 `assembleDebug` 或 `assembleRelease` 构建。

#### Step 2: R8 混淆自动注入与对照编译
```bash
python "2 - obfuscator.py"
```
* **功能:** 对 Step 1 成功拉取的项目进行自动运维。向 `build.gradle` 注入开启 R8 混淆的指令，并编译出未混淆版本（Whitebox）与开启 R8 混淆的版本（Blackbox），同时生成极其重要的 `mapping.txt` 文件。

#### Step 3: 数据归档
```bash
python move_apk.py
```
* **功能:** 将生成的白盒 APK、黑盒 APK 以及 `mapping.txt` 自动化地移动并重命名至 `ground_truth/GT1/` 下的对应子目录中。

#### Step 4: 提取白盒第三方库真值
```bash
python "3 - lib_extract.py"
```
* **功能:** 对 `ground_truth/GT1/whitebox_apk/` 中的未混淆 APK 进行扫描，基于包结构和先验规则，提取应用实际集成的第三方库清单，输出至 `ground_truth/GT1/libnames/`。这构成了后续实验的 Ground Truth。

#### Step 5: 构建白盒特征数据库 (核心)
```bash
python "4 - mapping.py"
```
* **功能:** 读取白盒 APK 与 `mapping.txt`。使用 Androguard 解析 DEX，提取类拓扑、归一化的 Opcode 序列和 API 调用图谱，建立映射关系，并将这些高维特征持久化存储至 `ground_truth/db/` 目录下的 SQLite 数据库中。同时建立 Method Hash 主聚集索引。

---

### 阶段二：LibProbe 核心算法识别

#### Step 6: 执行双层特征识别算法
当 SQLite 特征数据库构建完毕后，即可对未知的或黑盒混淆的 APK 进行库成分分析。

```bash
python LibProbe-V5.py
```
* **功能:** 
  1. 解析输入的待测 APK（黑盒）。
  2. **第一层（初筛）：** 提取哈希特征，在 SQLite 中通过 B-Tree 索引进行 $O(\log N)$ 级的快速检索，圈定候选方法。
  3. **第二层（精判）：** 对候选集进行基于 Opcode 和系统 API 的模糊逻辑比对（计算 Jaccard/SimHash 相似度），对抗 R8 的内联变异。
  4. **清洗聚合：** 启动“基于类上下文的双层投票机制”，输出最终存活的第三方库清单。
* **输出:** 识别日志将打印在控制台，最终的检测报告（包括检出的库名、版本、保留率等置信度信息）会生成在设定的输出目录或日志中。

## 实验与日志

* **日志查看:** 系统运行期间的构建错误日志、自动回滚日志以及算法匹配得分日志，分别存储在 `ground_truth/obfuscator_log/` 和 `ground_truth/libprobe_log/` 中。
* **评估指标:** `LibProbe-V5.py` 运行结束后，通过与 `GT1/libnames` 中的真值进行比对，可自动计算 Precision、Recall 以及 Exclusion Rate (ER) 等性能评估指标。

## 注意事项
* 若在 Step 1/2 遇到 Gradle 编译失败（常因网络或依赖环境问题），系统设计有故障自愈与回滚机制，但不排除极个别远古项目无法修复，这属于正常现象，算法会自动跳过并处理下一个样本。
* 确保分析前清理上一轮残留的 `temp` 缓存文件，以防 Androguard 解析时发生内存或指纹冲突。