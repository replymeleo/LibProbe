# -*- coding: utf-8 -*-
# pip install androguard==3.4.0a1 -i https://pypi.tuna.tsinghua.edu.cn/simple
# Androguard 3.4.0a1 is recommended for Python 3.8+

import ast
import hashlib
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import time
import numpy as np
import pandas as pd
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from androguard.core.analysis.analysis import MethodAnalysis
import traceback
import sqlite3
import zlib
from typing import Iterator, List, Dict, Any, Set, Tuple, Optional
import os
from collections import Counter

# --- 配置路径常量 ---
BLACKBOX_DB_PATH = Path("D:/LibProbe/ground_truth_part/db/blackbox.db")
MAPPING_DB_PATH = Path("D:/LibProbe/ground_truth_part/db/mapping.db")
WHITEBOX_DB_PATH = Path("D:/LibProbe/ground_truth_part/db/whitebox.db")
LOG_FILE = r"D:\LibProbe\ground_truth_part\libprobe_log\log.txt"
ACCURACY_CSV_PATH = Path("D:/LibProbe/ground_truth_part/libprobe_log/accuracy.csv")
ACCURACY_LOG_PATH = Path("D:/LibProbe/ground_truth_part/libprobe_log/accuracy.log")
MAPPING_ROOT_DIR = Path("D:/LibProbe/ground_truth_part/GT1/mapping")
WHITEBOX_ROOT = r"D:\LibProbe\ground_truth_part\GT1\whitebox_apk"
BLACKBOX_ROOT = r"D:\LibProbe\ground_truth_part\GT1\blackbox_apk"
WHITEBOX_TABLE_NAME = "whitebox_all"

# --- 核心控制开关 ---
# 【重要】表结构已改变（移除了 String），必须设为 True 以重建数据库
DELETE_OLD_WHITEBOX_DB = True  

# --- 核心阈值配置 ---
MIN_OPCODE_COUNT = 3  
MIN_MATCH_SCORE = 5   

def safe_decode(value: Any) -> Any:
    if isinstance(value, bytes):
        try: return value.decode('utf-8')
        except UnicodeDecodeError: return value.decode('latin-1') 
    return value

def make_full_name(cls_name: str, name: str) -> str:
    if not cls_name or not name: return ""
    cls_name = str(cls_name).strip('L').strip(';').replace('/', '.')
    return f"{cls_name}.{name}"

def extract_method_name(signature: str) -> str:
    if not signature: return ""
    match = re.search(r"\.([^\.^\(]+)\(", signature)
    if match: return match.group(1).strip()
    match = re.match(r"([^\(]+)\(", signature)
    if match: return match.group(1).strip()
    return signature.strip()

class Tee(object):
    def __init__(self, name, mode):
        os.makedirs(os.path.dirname(name), exist_ok=True)
        self.file = open(name, mode, encoding='utf-8')
        self.stdout = sys.stdout
    def __del__(self):
        if self.file: self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()

class SQLiteManager:    
    def __init__(self, whitebox_db_path: str, blackbox_db_path: str, mapping_db_path: str):
        self.whitebox_db_path = whitebox_db_path
        self.blackbox_db_path = blackbox_db_path
        self.mapping_db_path = mapping_db_path
        self.conn_timeout = 10
        self.truth_map: Dict[str, str] = {} 
        self.blackbox_data: List[Dict[str, Any]] = []
        self.is_new_experiment = False

    def _get_normalized_table_name(self, filename: str) -> str:
        name = Path(filename).stem
        for suffix in ['_blackbox', '_whitebox', '_mapping']:
            if name.endswith(suffix):
                name = name.replace(suffix, '')
        if '_' in name:
            name = name.split('_')[0]
        return name

    def table_exists(self, table_name: str) -> bool:
        if table_name == "whitebox_all": db_path = self.whitebox_db_path
        else: db_path = self.blackbox_db_path
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception: return False

    def query_candidates(self, method_hash: str) -> List[List[Any]]:
        conn = None
        try:
            conn = sqlite3.connect(self.whitebox_db_path)
            
            # 移除了 method_string_set
            query = f"""
            SELECT lib_name, class_name, method_name, method_descriptor, method_sig_str, 
                   method_opcode_seq, method_opcode_hash, 
                   method_api_call_set
            FROM whitebox_all WHERE method_hash = ?
            """
            cursor = conn.execute(query, (method_hash,))
            return [list(row) for row in cursor.fetchall()]
        except Exception: return []
        finally: 
            if conn: conn.close()

    def query_whitebox_by_hash(self, method_hash: str) -> Set[str]:
        conn = sqlite3.connect(self.whitebox_db_path)
        if not conn: return set()
        conn.row_factory = sqlite3.Row
        whitebox_methods = set()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT class_name, method_name FROM \"{WHITEBOX_TABLE_NAME}\" WHERE method_hash = ?", (method_hash,))
            for row in cursor.fetchall():
                c_name = safe_decode(row['class_name']).replace('/', '.')
                if c_name.startswith('L') and c_name.endswith(';'): c_name = c_name[1:-1].replace('/', '.')
                m_name = safe_decode(row['method_name'])
                whitebox_methods.add(make_full_name(c_name, m_name))
            return whitebox_methods
        except Exception: return set()
        finally: 
            if conn: conn.close()

    def create_whitebox_table(self):
        conn = sqlite3.connect(self.whitebox_db_path)
        cursor = conn.cursor()
        TABLE_NAME = "whitebox_all"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,))
        if cursor.fetchone(): conn.close(); return
        
        logging.info(f"[SQLite] 创建表 '{TABLE_NAME}'...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT, 
                method_name TEXT,
                method_hash TEXT,        -- L1 Index: Signature Hash
                method_descriptor TEXT,
                method_sig_str TEXT,
                method_opcode_seq TEXT,     
                method_opcode_hash INTEGER, -- L2 Feature: Logic Hash
                method_api_call_set TEXT,   
                method_api_hash INTEGER,    -- L2 Feature: Behavior Hash
                lib_name TEXT
            )
        """)
        # 移除了 idx_str_hash
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_m_hash ON {TABLE_NAME} (method_hash)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_op_hash ON {TABLE_NAME} (method_opcode_hash)")
        conn.commit(); conn.close()

    def save_whitebox_data(self, data_list: List[Dict[str, Any]], table_name: str = 'whitebox_all'):
        if not data_list: return
        df = pd.DataFrame(data_list)
        try:
            conn = sqlite3.connect(self.whitebox_db_path)
            df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.close()
            print(f"[SQLite] 成功保存 {len(data_list)} 条白盒数据。")
        except Exception as e: print(f"[错误] 写入白盒失败: {e}"); raise
    
    # 【修改点 1】增加 metric_status 列
    def save_blackbox_data(self, apk_name: str, data_list: List[List[Any]]):
        if not data_list: return
        table_name = self._get_normalized_table_name(apk_name)
        
        columns = [
            'class_name', 'method_name', 'method_sig_str', 'matched_type', 'matched_ratio', 'matched_confidence', 'method_hash',
            'opcode_sim', 'api_sim', 'max_score',
            'matched_lib_name', 'matched_class_name', 'matched_method_name', 'matched_method_descriptor', 
            'matched_method_sig_str', 'matched_opcode_seq', 'matched_opcode_hash', 'matched_api_call_set',
            'metric_status'  # <--- 新增列：用于存储 TP/FP/TN/FN
        ]
        try:
            df = pd.DataFrame(data_list, columns=columns)
            conn = sqlite3.connect(self.blackbox_db_path)
            # 使用 dtype 确保新列为 TEXT 类型
            df.to_sql(table_name, conn, if_exists='replace', index=False, dtype={'metric_status': 'TEXT'})
            conn.close()
        except Exception as e: print(f"[错误] 写入黑盒失败: {e}"); raise

    def get_apk_names(self) -> List[str]:
        conn = sqlite3.connect(self.blackbox_db_path)
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            return sorted([row[0] for row in cursor.fetchall()])
        except Exception: return []
        finally: 
            conn.close()

    def load_mapping_truth(self, table_name: str) -> Dict[str, str]:
        conn = sqlite3.connect(self.mapping_db_path)
        if not conn: return {}
        conn.row_factory = sqlite3.Row
        class_map, truth_map = {}, {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"[警告] Mapping数据库中未找到表: {table_name}。可能导致 FN=0。")
                return {}

            cursor.execute(f"SELECT * FROM \"{table_name}\"")
            rows = cursor.fetchall()
            for row in rows:
                if row['type'] == 'CLASS':
                    orig = safe_decode(row['original_signature'])
                    obf = safe_decode(row['obfuscated_name'])
                    if orig and obf: class_map[orig] = obf
            for row in rows:
                if row['type'] != 'METHOD': continue
                orig_sig = safe_decode(row['original_signature'])
                obf_name = safe_decode(row['obfuscated_name'])
                orig_fqn = safe_decode(row['original_fqn'])
                if not all([obf_name, orig_sig, orig_fqn]): continue
                orig_m = extract_method_name(orig_sig)
                orig_full = make_full_name(orig_fqn, orig_m)
                obf_cls = class_map.get(orig_fqn)
                if obf_cls:
                    truth_map[make_full_name(obf_cls, obf_name)] = orig_full
            
            return truth_map
        except Exception as e: 
            print(f"[错误] 读取Mapping失败: {e}")
            return {}
        finally: 
            conn.close()

    def load_blackbox(self, table_name: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.blackbox_db_path)
        if not conn: return []
        conn.row_factory = sqlite3.Row
        self.truth_map = self.load_mapping_truth(table_name)
        self.blackbox_data = []
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM \"{table_name}\"")
            for row in cursor.fetchall():
                matched_hash = safe_decode(row['method_hash'])
                wb_sets = self.query_whitebox_by_hash(matched_hash) if matched_hash and matched_hash != "NULL" else set()
                c_name = safe_decode(row['class_name'])
                if c_name.startswith('L') and c_name.endswith(';'):
                    c_name = c_name[1:-1].replace('/', '.')
                else:
                    c_name = c_name.replace('/', '.')
                m_name = safe_decode(row['method_name'])
                obf_full = make_full_name(c_name, m_name)

                self.blackbox_data.append({
                    "obfuscated_full_name": obf_full, 
                    "matched_type": safe_decode(row['matched_type']),
                    "matched_method_hash": matched_hash,
                    "whitebox_full_name_sets": wb_sets,
                    # 需要保存额外的字段用于后续 SQL UPDATE 定位
                    "class_name": safe_decode(row['class_name']),
                    "method_name": safe_decode(row['method_name']),
                    "method_sig_str": safe_decode(row['method_sig_str'])
                })
            return self.blackbox_data
        except Exception: return []
        finally: 
            conn.close()

    def save_metrics_to_files(self, metrics: Dict[str, Any]):
        apk_name = metrics['apk_name']
        sim = metrics.get('sim_thresholds', {})
        score_t = metrics.get('score_threshold', 0)
        total_time = metrics.get('total_time', 0.0)
        
        log_line = (
            f"[{apk_name}] (OpcSim>={sim.get('opcode',0):.2f}, ApiSim>={sim.get('api',0):.2f}, MaxScore>={score_t})\n"
            f"  TP: {metrics['TP']}, FP: {metrics['FP']}, TN: {metrics['TN']}, FN: {metrics['FN']}\n"
            f"  P: {metrics['Precision']:.4f}, R: {metrics['Recall']:.4f}, F1: {metrics['F1_score']:.4f}\n"
            f"  Total Time: {total_time:.4f}s\n"
            f"----------------------------------------\n"
        )
        with open(ACCURACY_LOG_PATH, 'a', encoding='utf-8') as f: f.write(log_line)
        csv_line = f"{apk_name},OpcSim:{sim.get('opcode',0):.2f}_ApiSim:{sim.get('api',0):.2f}_MaxScore:{score_t},{metrics['TP']},{metrics['FP']},{metrics['TN']},{metrics['FN']},{metrics['Precision']:.4f},{metrics['Recall']:.4f},{metrics['F1_score']:.4f},{total_time:.4f}\n"
        is_new = not ACCURACY_CSV_PATH.exists() or os.path.getsize(ACCURACY_CSV_PATH) == 0
        with open(ACCURACY_CSV_PATH, 'a', encoding='utf-8') as f:
            if is_new or self.is_new_experiment: 
                f.write("apk_name,metrics_type,TP,FP,TN,FN,Precision,Recall,F1_score,Time\n")
                self.is_new_experiment = False 
            f.write(csv_line)

    # 【修改点 3】计算指标后，将结果 (TP/FP/...) 回写数据库
    def calculate_metrics(self, table_name: str, total_time: float, sim_thresholds: Dict[str, float], score_threshold: int):
        if not self.blackbox_data: return {} 
        TP, FP, FN, TN = 0, 0, 0, 0
        
        # 准备批量更新列表
        update_list = []      # method_sig_str 不为空的情况
        update_list_null = [] # method_sig_str 为空的情况 (例如 ignored)

        for record in self.blackbox_data:
            obf_full = record['obfuscated_full_name']
            truth_orig = self.truth_map.get(obf_full)
            predicted_sets = record['whitebox_full_name_sets']
            
            has_truth = (truth_orig is not None)
            is_pred_pos = (record['matched_type'] == "Matched")
            is_correct = has_truth and is_pred_pos and (truth_orig in predicted_sets)
            
            status = "TN" # 默认值
            
            if is_pred_pos:
                if is_correct: 
                    TP += 1
                    status = "TP"
                else: 
                    FP += 1
                    status = "FP"
            else:
                if has_truth:
                    FN += 1
                    status = "FN"
                else:
                    TN += 1
                    status = "TN"
            
            # 收集用于 SQL Update 的数据
            m_sig = record['method_sig_str']
            if m_sig:
                update_list.append((status, record['class_name'], record['method_name'], m_sig))
            else:
                update_list_null.append((status, record['class_name'], record['method_name']))

        # 执行数据库回写更新
        try:
            conn = sqlite3.connect(self.blackbox_db_path)
            cursor = conn.cursor()
            
            # 1. 更新有签名的行
            if update_list:
                cursor.executemany(f"""
                    UPDATE "{table_name}" 
                    SET metric_status = ? 
                    WHERE class_name = ? AND method_name = ? AND method_sig_str = ?
                """, update_list)
            
            # 2. 更新无签名的行
            if update_list_null:
                cursor.executemany(f"""
                    UPDATE "{table_name}" 
                    SET metric_status = ? 
                    WHERE class_name = ? AND method_name = ? AND method_sig_str IS NULL
                """, update_list_null)
            
            conn.commit()
            conn.close()
            # print(f"[Info] 已将 {len(update_list) + len(update_list_null)} 条 metric_status 更新至表 {table_name}")
        except Exception as e:
            print(f"[警告] 更新 metric_status 失败: {e}")

        P = TP / (TP + FP) if (TP + FP) > 0 else 0
        R = TP / (TP + FN) if (TP + FN) > 0 else 0
        F1 = 2 * P * R / (P + R) if (P + R) > 0 else 0
        metrics = {'apk_name': table_name, 'TP': TP, 'FP': FP, 'TN': TN, 'FN': FN, 'Precision': P, 'Recall': R, 'F1_score': F1, "total_time": total_time, "sim_thresholds": sim_thresholds, "score_threshold": score_threshold}
        self.save_metrics_to_files(metrics)
        return metrics

class APKAnalyzer:
    def __init__(self, db_manager: SQLiteManager):
        self.class_cache, self.method_cache, self.file_cache = {}, {}, {}
        self.db_manager = db_manager 
        self.min_match_score = 5
        self.opcode_sim_threshold = 0.7
        self.api_sim_threshold = 0.7

    def set_thresholds(self, op_sim, api_sim, min_score):
        self.opcode_sim_threshold = op_sim
        self.api_sim_threshold = api_sim
        self.min_match_score = min_score

    def get_deterministic_hash(self, content_str: str) -> int:
        if not content_str: return 0
        return zlib.adler32(content_str.encode('utf-8')) & 0xffffffff

    def parse_method_descriptor(self, descriptor):
        if isinstance(descriptor, bytes): descriptor = descriptor.decode('utf-8', errors='replace')
        match = re.match(r'^\((.*?)\)(.*)$', descriptor)
        if not match: return [], ''
        params_str, return_type = match.groups()
        params = []
        i, length = 0, len(params_str)
        while i < length:
            if params_str[i] in ' ,': i += 1; continue
            array_dim = 0
            while i < length and params_str[i] == '[': array_dim += 1; i += 1
            if i >= length: break
            if params_str[i] == 'L':
                end = params_str.find(';', i)
                type_str = params_str[i:] if end == -1 else params_str[i:end+1]
                params.append('['*array_dim + type_str)
                i = length if end == -1 else end + 1
            else:
                params.append('['*array_dim + params_str[i])
                i += 1
        return params, return_type

    def convert_to_dex(self, input_path):
        cache_key = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
        if cache_key in self.file_cache: return self.file_cache[cache_key]
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(['d8', '--release', input_path, '--output', tmpdir], check=True, capture_output=True)
                dex_files = [open(f, 'rb').read() for f in Path(tmpdir).glob('*.dex')]
                self.file_cache[cache_key] = dex_files
                return dex_files
            except Exception: return []

    def load_dexes(self, file_path):
        if file_path.lower().endswith('.apk'): return APK(file_path).get_all_dex()
        elif file_path.lower().endswith(('.jar', '.aar')): return self.convert_to_dex(file_path)
        return []

    def is_android_api(self, dx, class_name):
        system_prefixes = ("Landroid/", "Lcom/android/internal/util", "Ldalvik/", "Ljava/", "Ljavax/", 
                           "Lorg/apache/", "Lorg/json/", "Lorg/w3c/dom/", "Lorg/xml/sax", "Lorg/xmlpull/v1/", 
                           "Ljunit/", "Lcom/android/okhttp/", "Lorg/apache/http/", "Lokio/", "Lokhttp3/", 
                           "Lcom/android/org", "Lcom/android/volley/", "L_COROUTINE/", "Landroidx/", "Lkotlin/", "Lkotlinx/")
        return any(class_name.startswith(p) for p in system_prefixes) or class_name not in dx.classes

    def calculate_class_signature(self, dx, class_name):
        if self.is_android_api(dx, class_name) or dx.classes[class_name].is_external(): return class_name
        if not isinstance(class_name, str): class_name = str(class_name)
        if class_name in self.class_cache: return self.class_cache[class_name]
        cls = dx.classes[class_name].get_vm_class()
        flags = cls.get_access_flags()
        access_flags = sorted([f for f, v in [("static",0x8), ("interface",0x200), ("abstract",0x400), ("annotation",0x2000), ("enum",0x4000)] if flags & v])
        if not access_flags: access_flags.append("class")
        p2 = self.calculate_class_signature(dx, cls.get_superclassname()) if cls.get_superclassname() else ""
        signature = f"{'|'.join(access_flags)}-parent[{p2}]"
        self.class_cache[class_name] = signature
        return signature

    def calculate_method_signature(self, dx, method):
        if isinstance(method, MethodAnalysis): method = method.get_method()
        method_id = f"{method.get_class_name()}->{method.get_name()}{method.get_descriptor()}"
        if method_id in self.method_cache: return self.method_cache[method_id]
        tmp = dx.get_method_analysis(method)
        is_ext = tmp is None or tmp.is_external()
        if is_ext:
            cur_class_sig, method_access_flags = '', method.get_name()
        else:
            cur_class_sig = self.calculate_class_signature(dx, method.get_class_name())
            flags = method.get_access_flags()
            access = sorted([f for f, v in [("static",0x8), ("varargs",0x80), ("native",0x100), ("abstract",0x400)] if flags & v])
            if method.get_name() == '<init>': access.append("constructor")
            method_access_flags = '|'.join(access)
        
        params, ret = self.parse_method_descriptor(method.get_descriptor())
        p_strs = [self.calculate_class_signature(dx, t) if t.startswith('L') else t+';' for t in params]
        r_str = self.calculate_class_signature(dx, ret) if ret.startswith('L') else ret
        signature = f"({cur_class_sig})({method_access_flags})({''.join(p_strs)})({r_str})"
        self.method_cache[method_id] = signature
        return signature

    def calculate_method_signature_hash(self, sig_str): return hashlib.sha256(sig_str.encode()).hexdigest()
    def get_libname(self, class_name): return '.'.join(str(class_name)[1:-1].replace('/', '.').split('$')[0].split('.')[:3])
    
    def get_opcode_seq_str(self, method):
        if not hasattr(method, "get_instructions"): return "", 0
        instructions = list(method.get_instructions())
        count = len(instructions)
        if count < MIN_OPCODE_COUNT: return "", count
        seq_str = "-".join([str(op.get_op_value()) for op in instructions])
        return seq_str, count

    def get_opcode_seq_hash(self, seq_str: str):
        return self.get_deterministic_hash(seq_str)
    
    # --- 核心修改：移除字符串提取逻辑 ---
    def get_method_strings(self, method):
        return set() # 直接返回空集合，不做任何操作

    def get_api_call_set(self, dx, method, depth, max_depth=3):
        if depth > max_depth: return set()
        res = dx.get_method_analysis(method)
        if res is None: return set()
        api_set = set()
        for c, m, _ in res.get_xref_to():
            if self.is_android_api(dx, c.get_vm_class().get_name()): api_set.add(m.full_name)
            else: api_set.update(self.get_api_call_set(dx, m, depth+1))
        return api_set
    
    def get_set_hash(self, data_set: Set[str]):
        if not data_set: return 0
        sorted_str = str(sorted(list(data_set)))
        return self.get_deterministic_hash(sorted_str)

    def get_similarity(self, s1, s2):
        if not s1 and not s2: return 1.0
        if not s1 or not s2: return 0.0
        return len(s1.intersection(s2)) / len(s1.union(s2))

    def parse_set_string(self, s):
        if not s or not isinstance(s, str): return set()
        s = s.strip()
        if s.startswith('{') and s.endswith('}'):
            try: 
                parsed = eval(s)
                return parsed if isinstance(parsed, set) else set()
            except: 
                content = s[1:-1].strip()
                return {x.strip().strip("'").strip('"') for x in content.split(', ') if x.strip()} if content else set()
        return set()

    def batch_process_whiteboxes(self, whitebox_paths: List[str], batch_size: int = 1):        
        for i in range(0, len(whitebox_paths), batch_size):
            print(f"处理文件批次 {i//batch_size + 1}/{(len(whitebox_paths) // batch_size) + 1}")
            batch_files = whitebox_paths[i:i + batch_size]
            self.class_cache.clear(); self.method_cache.clear()
            db_data = []
            for path in batch_files:
                print(f"处理白盒文件 {path}")
                infos = self.process_whitebox(path)
                db_data.extend(infos)
            
            if db_data: self.db_manager.save_whitebox_data(db_data)
        print("所有白盒批次处理完毕。")

    def process_whitebox(self, file_path):
        dex_list = self.load_dexes(file_path)
        if not dex_list: return []
        dx = Analysis()
        for dex in dex_list: dx.add(DalvikVMFormat(dex))
        dx.create_xref()
        
        all_data = []
        for cls in dx.classes.values():
            if cls.is_external(): continue
            c_name = str(cls.get_vm_class().get_name())
            
            for method in cls.get_vm_class().get_methods():
                try:
                    if isinstance(method, MethodAnalysis): method = method.get_method()
                    
                    op_seq, op_count = self.get_opcode_seq_str(method)
                    if op_count < MIN_OPCODE_COUNT: continue

                    m_sig = self.calculate_method_signature(dx, method)
                    m_hash = self.calculate_method_signature_hash(m_sig)
                    m_desc = method.get_descriptor()
                    op_hash = self.get_opcode_seq_hash(op_seq)
                    
                    apis = self.get_api_call_set(dx, method, 0)
                    api_hash = self.get_set_hash(apis) if len(apis) >= 2 else 0
                    
                    # 彻底移除 String 特征
                    # strs = self.get_method_strings(method)
                    # str_hash = self.get_set_hash(strs) if strs else 0

                    all_data.append({
                        'class_name': c_name,
                        'method_name': method.get_name(), 'method_hash': m_hash,
                        'method_descriptor': m_desc, 'method_sig_str': m_sig,
                        'method_opcode_seq': op_seq, 'method_opcode_hash': op_hash,
                        'method_api_call_set': str(apis), 'method_api_hash': api_hash,
                        # 'method_string_set': str(strs), 'method_string_hash': str_hash, # 移除
                        'lib_name': self.get_libname(c_name)
                    })
                except: pass
        return all_data

    def apply_class_context_filtering(self, results: List[List[Any]]) -> List[List[Any]]:
        class_groups = {}
        for row in results:
            bb_cls = row[0]
            if bb_cls not in class_groups: class_groups[bb_cls] = []
            class_groups[bb_cls].append(row)
            
        final_results = []
        for bb_cls, rows in class_groups.items():
            lib_votes = []
            for row in rows:
                if row[3] == "Matched":
                    matched_lib = row[10]
                    if matched_lib: lib_votes.append(matched_lib)
            
            if not lib_votes:
                final_results.extend(rows)
                continue
                
            most_common = Counter(lib_votes).most_common(1)
            top_lib, count = most_common[0]
            
            for row in rows:
                if row[3] == "Matched":
                    current_lib = row[10]
                    if current_lib != top_lib:
                        row[3] = "Filtered_Context"
                final_results.append(row)
                
        return final_results

    def analyze_blackbox(self, path: str):
        print(f"正在分析黑盒 APK: {Path(path).name} ...")
        self.class_cache.clear(); self.method_cache.clear()
        try:
            dex_list = self.load_dexes(path)
            if not dex_list: return
            dx = Analysis()
            for dex in dex_list: dx.add(DalvikVMFormat(dex))
            dx.create_xref()
            
            raw_results = []
            for c in dx.classes.values(): 
                if c.is_external(): continue
                for m in c.get_vm_class().get_methods():
                    raw_results.append(self.analyze_method(dx, c, m))
            
            filtered_results = self.apply_class_context_filtering(raw_results)
            self.db_manager.save_blackbox_data(Path(path).name, filtered_results)
        except Exception as e: 
            print(f"Err {path}: {e}")
            traceback.print_exc()

    # --- 核心修改：分析阶段移除 String 比对 ---
    # 【修改点 2】: 返回的列表末尾增加 None，对应 metric_status 列
    def analyze_method(self, dx, cls, method):
        c_name = cls.get_vm_class().get_name()
        m_name = method.get_name()
        
        try:
            if hasattr(method, 'get_method'): method = method.get_method()
            
            bb_op_seq, bb_op_count = self.get_opcode_seq_str(method)
            if bb_op_count < MIN_OPCODE_COUNT:
                return [c_name, m_name, None, "Ignored_Short", 0.0, 0.0, "NULL", 0, 0, 0, None, None, None, None, None, None, None, None, None]

            # 1. 计算签名哈希 (L1 索引)
            m_sig = self.calculate_method_signature(dx, method)
            m_hash = self.calculate_method_signature_hash(m_sig) 

            # 2. 计算特征 (L2 校验)
            bb_op_hash = self.get_opcode_seq_hash(bb_op_seq)
            
            bb_apis = self.get_api_call_set(dx, method, 0)
            
            # [L1 查询]：只查询签名结构一致的方法
            candidates = self.db_manager.query_candidates(m_hash)
            
            best_match = None
            best_score = -1

            for cand in candidates:
                # cand结构: [0:lib, 1:cls, 2:nm, 3:dsc, 4:sig, 5:opseq, 6:oph, 7:apis]
                score = 0
                
                # --- [L2] 代码逻辑 (Opcode) ---
                if cand[6] == bb_op_hash:
                    score += 5 
                
                # --- [L2] 行为 (API) ---
                wb_apis = self.parse_set_string(cand[7])
                if bb_apis or wb_apis:
                    if bb_apis and wb_apis:
                        sim = self.get_similarity(bb_apis, wb_apis)
                        if sim >= self.api_sim_threshold:
                            score += 3 + (sim * 2) 

                # --- 原始签名 (额外加分) ---
                score += 5

                if score > best_score:
                    best_score = score
                    best_match = cand
            
            if best_score >= self.min_match_score and best_match:
                match_type = "Matched"
                conf = 1.0
                matched_hash = self.calculate_method_signature_hash(best_match[4])
                
                return [
                    c_name, m_name, m_sig, match_type, 0.0, conf, matched_hash,
                    1.0, 0, best_score, 
                    best_match[0], best_match[1], best_match[2], best_match[3], best_match[4], 
                    best_match[5], best_match[6], best_match[7],
                    None # metric_status
                ]
            
        except Exception: pass
        
        return [
            c_name, m_name, None, "Unknown", 0.0, 0.0, "NULL",
            0, 0, 0, 
            None, None, None, None, None, None, None, None,
            None # metric_status
        ]

class Accuracy:
    def __init__(self, mgr, sim, score, total_time):
        self.mgr = mgr
        self.sim = sim
        self.score = score
        self.total_time = total_time 

    def run_for_single_apk(self, apk_path_str: str):
        table_name = self.mgr._get_normalized_table_name(apk_path_str)
        print(f"正在计算准确率: {Path(apk_path_str).name} -> 表名: {table_name}")
        
        try:
            self.mgr.load_blackbox(table_name)
        except Exception as e:
            print(f"[Error] 无法加载表 {table_name}: {e}")
            return

        if not self.mgr.blackbox_data:
            print(f"[Warning] 表 {table_name} 无数据")
            return

        metrics = self.mgr.calculate_metrics(table_name, self.total_time, self.sim, self.score)
        print(f"  Result -> P: {metrics['Precision']:.4f}, R: {metrics['Recall']:.4f}, F1: {metrics['F1_score']:.4f}, Time: {self.total_time:.2f}s")

def cleanup_blackbox_db(path):
    if path.exists():
        try: os.remove(path)
        except: pass
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path); conn.close()

if __name__ == "__main__":   
    sys.stdout = Tee(LOG_FILE, 'w')
    whitebox_files = [str(p) for p in Path(WHITEBOX_ROOT).rglob('*.apk')]
    blackbox_files = [str(p) for p in Path(BLACKBOX_ROOT).rglob('*.apk')]
    
    sqlite_manager = SQLiteManager(WHITEBOX_DB_PATH, BLACKBOX_DB_PATH, MAPPING_DB_PATH)
    apk_analyzer = APKAnalyzer(db_manager=sqlite_manager)
    sqlite_manager.is_new_experiment = True 

    print(f"======== 检查白盒数据库 ========")
    
    should_process_whitebox = True
    if WHITEBOX_DB_PATH.exists():
        if DELETE_OLD_WHITEBOX_DB:
            try: os.remove(WHITEBOX_DB_PATH); print("[配置] 已强制删除旧白盒数据库")
            except: pass
        else:
            print(f"[配置] 检测到白盒数据库 {WHITEBOX_DB_PATH.name} 已存在，且配置为保留 (DELETE_OLD_WHITEBOX_DB=False)。")
            print("[配置] 将直接使用现有数据，跳过白盒分析步骤。")
            should_process_whitebox = False

    sqlite_manager.create_whitebox_table()
    
    if should_process_whitebox:
        print("开始白盒分析 (Feature: Opcode Seq + API)...")
        apk_analyzer.batch_process_whiteboxes(whitebox_files)
        print(f"======== 白盒 APK 分析完成 ========")
    else:
        print(f"======== 跳过白盒 APK 分析 ========")

    print("======== 开始网格搜索 (Multi-Index Recall + Context Voting) ========")
    sim_range = [0.2] 
    score_range = [5] 

    total_iters = len(sim_range) * len(sim_range) * len(score_range)
    curr = 0
    for op_th in sim_range: 
        for api_th in sim_range:
            for score_th in score_range:
                curr += 1
                print(f"\n--- [{curr}/{total_iters}] Config: Api>{api_th}, MinScore>{score_th} ---")
                
                apk_analyzer.set_thresholds(op_th, api_th, score_th)
                cleanup_blackbox_db(BLACKBOX_DB_PATH)
                
                for bb_file in blackbox_files:
                    loop_start = time.time()
                    apk_analyzer.analyze_blackbox(bb_file)
                    duration = time.time() - loop_start
                    
                    acc = Accuracy(sqlite_manager, {'opcode': op_th, 'api': api_th}, score_th, duration)
                    acc.run_for_single_apk(bb_file)
    
    print("======== 所有任务完成 ========")
    sys.stdout = sys.stdout.stdout