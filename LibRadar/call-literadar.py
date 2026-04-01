import subprocess
import sys
import time

from nacl.hash import sha256

from _settings import *
import litedextree
import dex_parser
import hashlib
import zipfile
import json

import csv
from datetime import datetime
from literadar import LibRadarLite

iron_apk_path = 'E:\\apk\\com.youku.phone_744.apk'

def get_files_in_directory(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

directory = 'E:\\apk\\'
#files = get_files_in_directory(directory)

http_apk_file_list_path = 'E:\\TraceDroid-simple\\capture-success\\apk_lib_list_1026.txt'
with open(http_apk_file_list_path, 'r') as file:
    lines = file.readlines()
http_apk_file_list = [line.strip() for line in lines]

apk_libs = dict()
for lib_info in http_apk_file_list:
    tmp = lib_info.split(', ')
    apkName = tmp[0]
    libName = tmp[1]
    if apkName in apk_libs:
        apk_libs[apkName].add(libName)
    else:
        apk_libs[apkName] = set()
        apk_libs[apkName].add(libName)

print(f"Total apk files to extract: {len(apk_libs)}")
total_files = len(apk_libs)

#lrd = LibRadarLite(iron_apk_path)
cnt = 0
for apk_file, lib_list in apk_libs.items():

    # 获取当前时间
    now = datetime.now()

    # 格式化日期和时间
    formatted_date_time = now.strftime("%Y-%m-%d %H:%M")

    print(f"---------> [{formatted_date_time}]Start handle file {cnt}/{total_files}...")
    cnt += 1
    file_name = apk_file
    apk_file = f"E:\\apk\\{file_name}"
    apk_csv_file = f'E:\\apk-csv\\{file_name}.csv'

    # Check if the file exists
    if os.path.exists(apk_csv_file):
        print(f"The file {apk_csv_file} exists.")
        continue
    print(f'handle {apk_file}')

    # 你要运行的带参数的Python程序的文件名
    python_program = "literadar-based-on-dynamic-single.py"

    # 你要传递给Python程序的参数
    arguments = [apk_file, ]

    # 使用subprocess.run()运行Python程序
    subprocess.run(["python", python_program] + arguments)

    print(f"Start the subprocess: python {python_program} {arguments}")
    print("...")
