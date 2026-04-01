import subprocess

# 你要运行的带参数的Python程序的文件名
python_program = "literadar-origin.py"

# 你要传递给Python程序的参数
arguments = ["E:\\apk\\com.youku.phone_744.apk"]

# 使用subprocess.run()运行Python程序
subprocess.run(["python", python_program] + arguments)
