# -*- coding: utf-8 -*-

#   Copyright 2017 Zachary Marv (马子昂)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


#   LibRadar
#
#   main function for instant detection.

import sys
import time
import os
from nacl.hash import sha256

from _settings import *
import litedextree
import dex_parser
import hashlib
import zipfile
import json
import csv
from datetime import datetime

class LibRadarLite(object):
    """
    LibRadar
    """

    def __init__(self, apk_path):
        self.total_time_direct_method = 0
        self.total_time_virtual_method = 0
        self.apk_path = apk_path
        self.write_csv_path = r"D:\LibProbe\LibRadar\temp\1.csv"
        self.tree = litedextree.Tree()
        self.dex_names = []
        self.dex_objects = []

        self.k_api_v_permission = dict()
        with open(os.path.join(SCRIPT_PATH, 'Data', 'strict_api.csv'), 'r') as api_and_permission:
            api_id = 0
            for line in api_and_permission:
                api, permission_with_colon = line.split(",")
                permissions = permission_with_colon[:-2].split(":")
                permission_list = [p for p in permissions if p != ""]
                self.k_api_v_permission[api] =  (permission_list, api_id)
                api_id += 1

    def __del__(self):
        if CLEAN_WORKSPACE >= 3:
            for dex_name in self.dex_names:
                os.remove(dex_name)
                os.removedirs(os.path.dirname(dex_name))

    def unzip(self):
        if not os.path.isfile(self.apk_path):
            print("Error: %s is not a valid file." % self.apk_path)
            raise AssertionError
        if len(self.apk_path) <= 4 or self.apk_path[-4:] != ".apk":
            print("Error: %s is not a apk file." % self.apk_path)
            raise AssertionError

        self.hex_sha256 = self.get_sha256()
        
        try:
            zf = zipfile.ZipFile(self.apk_path, mode='r')
        except zipfile.BadZipFile:
            print(f"Warning: {self.apk_path} is not a valid zip file or is corrupted. Skipping this file.")
            return []

        try:
            self.dex_names.append(zf.extract("classes.dex", SCRIPT_PATH + "/Data/Decompiled/%s" % self.hex_sha256))

            basename = "classes%d.dex"
            try:
                x_range = xrange(2, sys.maxint)
            except Exception:
                x_range = range(2, sys.maxsize)
            for i in x_range:
                self.dex_names.append(zf.extract(basename % i, SCRIPT_PATH + "/Data/Decompiled/%s" % self.hex_sha256))
        except KeyError:
            pass

        return self.dex_names

    def get_sha256(self):
        if not os.path.isfile(self.apk_path):
            print("Error: file path %s is not a file" % self.apk_path)
            raise AssertionError
        file_sha256 = hashlib.sha256()
        f = open(self.apk_path, 'rb')
        while True:
            block = f.read(4096)
            if not block:
                break
            file_sha256.update(block)
        f.close()
        file_sha256_value = file_sha256.hexdigest()
        return file_sha256_value

    def get_api_list(self, dex_obj, dex_method, api_list, permission_list):
        if dex_method.dexCode is None:
            return
        offset = 0
        insns_size = dex_method.dexCode.insnsSize * 4

        while offset < insns_size:
            op_code = int(dex_method.dexCode.insns[int(offset):int(offset + 2)], 16)
            decoded_instruction = dex_parser.dexDecodeInstruction(dex_obj, dex_method.dexCode, offset)
            smali_code = decoded_instruction.smaliCode
            offset += decoded_instruction.length
            if smali_code is None:
                continue
            if smali_code == 'nop':
                break
            if 0x6e <= op_code <= 0x72:
                if decoded_instruction.getApi in self.k_api_v_permission:
                    api_list.append(decoded_instruction.getApi)
                    for permission in self.k_api_v_permission[decoded_instruction.getApi][0]:
                        permission_list.add(permission)
        return

    def extract_class(self, dex_obj, dex_class_def_obj):
        class_sha256 = hashlib.sha256()
        api_list = list()
        permission_list = set()

        last_method_index = 0
        start_time = time.time()
        for k in range(len(dex_class_def_obj.directMethods)):
            current_method_index = last_method_index + dex_class_def_obj.directMethods[k].methodIdx
            last_method_index = current_method_index
            self.get_api_list(dex_obj, dex_class_def_obj.directMethods[k], api_list=api_list, permission_list=permission_list)
        end_time = time.time()
        self.total_time_direct_method += end_time - start_time

        start_time = time.time()
        last_method_index = 0
        for k in range(len(dex_class_def_obj.virtualMethods)):
            current_method_index = last_method_index + dex_class_def_obj.virtualMethods[k].methodIdx
            last_method_index = current_method_index
            self.get_api_list(dex_obj, dex_class_def_obj.virtualMethods[k], api_list=api_list, permission_list=permission_list)
        end_time = time.time()
        self.total_time_virtual_method += end_time -start_time

        api_list.sort()
        for api in api_list:
            class_sha256.update(api.encode())
        if not IGNORE_ZERO_API_FILES or len(api_list) != 0:
            pass

        api_id_list = []
        for api in api_list:
            api_id_list.append(self.k_api_v_permission[api][1])
        return len(api_list), class_sha256.hexdigest(), class_sha256.hexdigest(), sorted(list(permission_list)), sorted(list(api_id_list))

    def extract_dex(self):
        print("Start to get csv content...")
        start_time = time.time()
        csv_rows = []
        for dex_name in self.dex_names:
            if not os.path.isfile(dex_name):
                print("Error: %s is not a file" % dex_name)
                return -1
            current_dex = dex_parser.DexFile(dex_name)
            self.dex_objects.append(current_dex)

            print(f"Start to extract info for dex_list len={len(current_dex.dexClassDefList)}...")
            for dex_class_def_obj in current_dex.dexClassDefList:
                weight, raw_sha256, hex_sha256, permission_list, api_id_list = self.extract_class(dex_obj=current_dex, dex_class_def_obj=dex_class_def_obj)
                class_name = current_dex.getDexTypeId(dex_class_def_obj.classIdx)

                if class_name[0] != 'L':
                    l_index = class_name.find('L')
                    if l_index == '-1':
                        continue
                    class_name = class_name[l_index:]

                if IGNORE_ZERO_API_FILES and weight == 0:
                    continue

                package_name = class_name[1:].replace('/', '.')
                package_name = package_name.split('$')[0]
                package_name = '.'.join(package_name.split('.')[:3])
                csv_rows.append([class_name, package_name, weight, permission_list, api_id_list, raw_sha256])

        end_time = time.time()
        print(f"Get csv content done. Time cost: {end_time - start_time} s")

        print("Start to save csv...")
        start_time = time.time()
        fields = ['raw_class_name', 'package_name', 'weight', 'permission_list', 'api_id_list', 'sha256']
        with open(self.write_csv_path, 'w', encoding='utf-8') as f:
            csv_writer = csv.writer(f, lineterminator='\n')
            csv_writer.writerow(fields)
            csv_writer.writerows(csv_rows)
        end_time = time.time()
        print(f"{self.write_csv_path} saved. Time cost : {end_time - start_time} s")
        print(f"total_time_direct_method = {self.total_time_direct_method}, total_time_virtual_method = {self.total_time_virtual_method}.")
        return 0

    def analyse(self):
        print("Start to unzip the apk file...")
        start_time = time.time()
        self.unzip()
        end_time = time.time()
        print(f"unzip done. Time cost = {end_time - start_time} s")
        print("Start to extract dex...")
        start_time = time.time()
        self.extract_dex()
        end_time = time.time()
        print(f"extract done. Time cost = {end_time - start_time} s")

    def compare(self):
        self.analyse()
        self.tree.match()
        res = list()
        self.tree.get_lib(res)
        self.tree.find_untagged(res)
        return res


if __name__ == '__main__':
    # 修改路径为您的 APK 所在目录和输出目录
    apk_directory = r"D:\LibProbe\ground_truth_part\GT1\blackbox_apk"
    output_directory = r"D:\LibProbe\LibRadar\temp"

    # 如果输出目录不存在，则创建
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # 获取指定目录下所有以 .apk 结尾的文件
    apk_files = []
    for root, dirs, files in os.walk(apk_directory):
        for file in files:
            if file.endswith(".apk"):
                apk_files.append(os.path.join(root, file))

    total_files = len(apk_files)
    cnt = 0

    # 因为分析可能反复使用同一个 lrd 实例存在问题，所以这里每次创建新实例
    for apk_file in apk_files:
        cnt += 1
        now = datetime.now()
        formatted_date_time = now.strftime("%Y-%m-%d %H:%M")
        print(f"---------> [{formatted_date_time}] Start handle file {cnt}/{total_files}...")

        # 构建输出 csv 的文件名（与 apk 名对应）
        base_name = os.path.basename(apk_file)
        csv_file = os.path.join(output_directory, base_name + ".csv")

        # 如果对应 csv 文件已存在，跳过
        if os.path.exists(csv_file):
            print(f"The file {csv_file} exists. Skip.")
            continue

        print(f'Handle {apk_file}')
        lrd = LibRadarLite(apk_file)
        predicted_result = lrd.compare()
        print(predicted_result)
        lrd.write_csv_path = csv_file
        lrd.analyse()
