#!/usr/bin/env python3
"""
更新所有使用initialize_st_page函数的文件
将title参数更改为page_title参数
"""
import os
import re
import sys


def find_python_files(directory):
    """查找指定目录下的所有Python文件"""
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def update_file(filepath):
    """更新文件中的initialize_st_page调用"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 使用正则表达式查找initialize_st_page函数调用
        pattern = r"initialize_st_page\(title\s*=\s*"

        if re.search(pattern, content):
            # 替换参数名
            updated_content = re.sub(pattern, "initialize_st_page(page_title=", content)

            # 写回文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            print(f"Updated: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """主函数"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取要搜索的目录
    search_dir = os.path.join(script_dir, "frontend")

    if not os.path.exists(search_dir):
        print(f"Directory not found: {search_dir}")
        return 1

    print(f"Searching for Python files in {search_dir}...")

    # 获取所有Python文件
    py_files = find_python_files(search_dir)
    print(f"Found {len(py_files)} Python files")

    # 更新文件
    updated_count = 0
    for filepath in py_files:
        if update_file(filepath):
            updated_count += 1

    print(f"Updated {updated_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
