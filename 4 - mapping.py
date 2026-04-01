import os
import re
from pathlib import Path
import sqlite3
from typing import Iterator, List, Dict, Any, Set, Tuple, Optional

MAPPING_DB_PATH = Path("D:/LibProbe/ground_truth_part/db/mapping.db")
MAPPING_ROOT_DIR = Path("D:/LibProbe/ground_truth_part/GT1/mapping")

class MappingParser:
    """
    解析 R8/ProGuard 的 mapping.txt 文件，并将混淆关系存入 SQLite 数据库。
    本版本将文件解析与数据库写入分离，以解决数据库锁定问题。
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. 类名映射的正则表达式
        # 匹配格式: OriginalClass -> ObfuscatedClass:
        # (?P<original_class>[^ ]+): 捕获混淆前的完整类名。
        # \s+->\s+: 匹配一个或多个空格、箭头、一个或多个空格。
        # (?P<obfuscated_class>[^:]+): 捕获混淆后的类名，直到遇到行尾的冒号。
        self.class_pattern = re.compile(r"^(?P<original_class>[^ ]+)\s+->\s+(?P<obfuscated_class>[^:]+):$")
        
        # 2. 字段映射的正则表达式
        # 匹配格式: OriginalType OriginalField -> ObfuscatedField
        # [^ :()]+: 确保不匹配方法行（方法行包含冒号或圆括号），收紧字段匹配。
        # (?P<original_type>[^ :()]+): 捕获字段的原始数据类型。
        # (?P<original_field>[^ :()]+): 捕获字段的原始名称。
        # (?P<obfuscated_field>[^ ]+): 捕获混淆后的字段名。
        self.field_pattern = re.compile(r"^(?P<original_type>[^ :()]+)\s+(?P<original_field>[^ :()]+)\s+->\s+(?P<obfuscated_field>[^ ]+)$")
        
        # 3. 方法映射的正则表达式
        # 匹配格式: [line_range:] ReturnType [ClassFQN.]MethodName(Arguments) [line_range] -> ObfuscatedName
        self.method_pattern = re.compile(
            r"^(?P<line_range_full>(?:\d+:\d+:)*)?"  # 捕获可选的起始行号范围 (e.g., 1:1:)
            r"(?P<return_type>[^ ]+)\s+"             # 捕获返回类型 (e.g., void, int)
            r"(?P<original_fqn_method>[^ ]+)"        # 捕获原始方法名，可能包含类路径 (e.g., com.pkg.Class.method 或 method)
            r"\((?P<arguments>[^)]*)\)"              # 捕获参数列表 (e.g., java.lang.String,int)
            r"(?P<line_range_optional>(?:\:\d+)+)?"  # 捕获可选的结束行号范围 (e.g., :0:0)
            r"\s+->\s+"                              # 分隔符
            r"(?P<obfuscated_method>[^ ]+)$"         # 捕获混淆后的方法名
        )

    def connect(self):
        """建立数据库连接，设置超时时间防止数据库被锁定"""
        # 设置超时时间为 10.0 秒。如果数据库被锁定，SQLite 会等待，而不是立即抛出异常。
        return sqlite3.connect(self.db_path, timeout=10.0)

    def create_table(self, conn: sqlite3.Connection, table_name: str):
        """为指定的 APK 创建映射表，使用双引号支持表名中的点号(.)。"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,        -- 自增主键
            
            -- 【核心字段】混淆前的完整签名，用于唯一标识一个元素 (类、字段或方法)
            -- 格式: ClassFQN[.MemberName[:Type|Signature]]
            original_signature TEXT NOT NULL, 
            
            -- 【核心字段】混淆后的名称 (例如：a, b, a.a, onClick 等)
            obfuscated_name TEXT NOT NULL,
            
            -- 【核心字段】元素类型: CLASS, FIELD, 或 METHOD
            type TEXT NOT NULL,
            
            -- 【方法/字段归属】方法或字段所属的类或接口的全限定名。
            -- 字段: 通常为空。方法: 存储方法真正的所属类（用于处理接口实现和继承）。
            original_fqn TEXT,
            
            -- 【方法详情】方法执行后的返回类型 (仅用于 METHOD)
            original_return_type TEXT,
            
            -- 【方法详情】方法接受的参数列表 (仅用于 METHOD)
            original_args TEXT,
            
            -- 确保签名唯一，防止重复插入
            UNIQUE(original_signature)
        );
        """
        conn.execute(sql)
        conn.commit()

    def _extract_package_name(self, filename: str) -> str:
        """从文件名中提取包名作为 SQLite 表名。"""
        name_without_suffix = filename.replace('_mapping.txt', '')
        
        if '_' in name_without_suffix:
            # 只取第一个下划线前面的部分
            return name_without_suffix.split('_', 1)[0]
        else:
            return name_without_suffix

    def _read_and_parse_data(self, mapping_file_path: Path) -> Tuple[List[Tuple], Optional[str]]:
        """
        仅负责读取文件和解析数据到内存中。此函数不涉及数据库操作，因此不会持有数据库锁。
        """
        insert_data: List[Tuple] = []
        original_class = None # 存储当前作用域下的类名
        line_number = 0

        with open(mapping_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 1. 匹配类名映射 (Class Pattern)
                class_match = self.class_pattern.match(line)
                if class_match:
                    # 更新当前作用域的类名
                    original_class = class_match.group('original_class')
                    obfuscated_class = class_match.group('obfuscated_class')
                    
                    # 存储 CLASS 类型记录
                    insert_data.append((original_class, obfuscated_class, 'CLASS', None, None, None))
                    continue
                
                # 只有当成功匹配到类名后，才开始匹配字段和方法
                if not original_class:
                    continue
                
                # 2. 匹配方法映射 (Method Pattern) - 优先级最高
                method_match = self.method_pattern.match(line)
                if method_match:
                    return_type = method_match.group('return_type')
                    original_fqn_method = method_match.group('original_fqn_method')
                    arguments = method_match.group('arguments')
                    obfuscated_method = method_match.group('obfuscated_method')
                    
                    # === 【核心逻辑】提取方法所属类名 (original_fqn) 和纯方法名 ===
                    # rsplit('.', 1) 从右侧分割，最多分割一次，用于分离 ClassFQN 和 MethodName
                    parts = original_fqn_method.rsplit('.', 1)
                    if len(parts) == 2:
                        # 格式: ClassFQN.MethodName (方法行中包含类路径)
                        original_fqn = parts[0]          # 方法的实际所属类名 (e.g., ademar.textlauncher.Adapter)
                        original_method_name = parts[1]  # 纯方法名 (e.g., filter)
                    else:
                        # 格式: MethodName (方法行中省略了类路径)
                        original_fqn = original_class          # 假定方法属于当前作用域的类
                        original_method_name = original_fqn_method
                    
                    # 构造最终签名 (OriginalClass.MethodName(Args):ReturnType)
                    # 签名中始终使用当前作用域的类名，确保唯一性。
                    original_sig = f"{original_class}.{original_method_name}({arguments}):{return_type}"
                    
                    # 存储 METHOD 类型记录
                    insert_data.append((
                        original_sig, 
                        obfuscated_method, 
                        'METHOD', 
                        original_fqn,       # 方法的实际归属类
                        return_type, 
                        arguments
                    ))
                    continue

                # 3. 匹配字段映射 (Field Pattern) - 仅当不是方法时才尝试匹配
                field_match = self.field_pattern.match(line)
                if field_match:
                    original_type = field_match.group('original_type')
                    original_field = field_match.group('original_field')
                    obfuscated_field = field_match.group('obfuscated_field')
                    
                    # 构造字段签名 (OriginalClass.FieldName:FieldType)
                    original_sig = f"{original_class}.{original_field}:{original_type}"
                    
                    # 存储 FIELD 类型记录
                    insert_data.append((original_sig, obfuscated_field, 'FIELD', None, None, None))
                    continue
                    
        return insert_data, original_class

    def parse_file(self, mapping_file_path: Path, current_index: int, total_count: int):
        """解析单个 mapping 文件并存储到数据库中。"""
        
        table_name = self._extract_package_name(mapping_file_path.name)
        
        print(f"\n[{current_index}/{total_count}] [解析开始] 文件: {mapping_file_path.name} -> 表名: {table_name}")
        
        # 步骤 1: 读取文件并解析数据到内存 (长时间操作 - 不锁定数据库)
        try:
            insert_data, _ = self._read_and_parse_data(mapping_file_path)
            
        except Exception as e:
            print(f"[错误] 读取和解析文件 {mapping_file_path.name} 失败: {e}")
            return
            
        # 步骤 2: 连接数据库并写入 (短时间操作 - 最小化锁定时间)
        conn = None
        try:
            conn = self.connect()
            self.create_table(conn, table_name) # 创建表

            # 批量插入数据
            cursor = conn.cursor()
            sql_insert = f"""
            INSERT OR IGNORE INTO "{table_name}" 
            (original_signature, obfuscated_name, type, original_fqn, original_return_type, original_args) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.executemany(sql_insert, insert_data)
            conn.commit() # 事务提交，释放写锁
            print(f"  [DB] 成功插入/忽略 {cursor.rowcount} 条映射记录到表 {table_name}。")

        except sqlite3.OperationalError as e:
            # 捕获数据库已锁定等错误
            print(f"[错误] 写入数据库失败 ({table_name}): {e}。可能数据库被其他进程锁定。")
        except Exception as e:
            print(f"[错误] 写入数据库失败 ({table_name}): {e}")
            
        finally:
            # 立即关闭连接，释放数据库锁
            if conn:
                conn.close()

    def run(self, root_dir: Path):
        """遍历根目录下的所有 mapping.txt 文件并进行解析。"""
        mapping_files = []
                
        # 2. 查找用户指定的根目录下的所有 mapping 文件
        if root_dir.is_dir():
            mapping_files.extend(list(root_dir.rglob('*_mapping.txt')))
        
        unique_files = sorted(list(set(mapping_files)), key=lambda x: x.name)
        
        if not unique_files:
            print(f"[警告] 未找到任何 *_mapping.txt 文件。请检查 MAPPING_ROOT_DIR 配置。")
            return
            
        total_count = len(unique_files)
        print(f"[信息] 找到 {total_count} 个 mapping 文件，准备开始解析和存储...")

        for i, file_path in enumerate(unique_files, 1):
            self.parse_file(file_path, i, total_count)

if __name__ == "__main__":   
    mapping_parser = MappingParser(MAPPING_DB_PATH)

    MAX_SIZE_BYTES = 1048576 
    
    # 解析mapping文件任务
    if MAPPING_DB_PATH.exists() and os.path.getsize(MAPPING_DB_PATH) > MAX_SIZE_BYTES:
        print(">>> 跳过解析任务: mapping_parser.run(MAPPING_ROOT_DIR)")
    else:
        print(f"======== 开始解析映射文件并保存到 {MAPPING_DB_PATH.name} ========")
        mapping_parser.run(MAPPING_ROOT_DIR)
        print(f"[操作完成] 映射数据已保存到数据库：{MAPPING_DB_PATH}")
