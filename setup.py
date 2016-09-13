#coding=utf-8
#!/usr/bin/env python
import sys
print("使用命令 python setup.py build")
from cx_Freeze import setup, Executable
setup(
        name = "ClientManager",
        version = "1.1",
        description = "Web ClientManager",
        executables = [Executable("pyClientManager.py",icon = "damotouicon.ico")])
