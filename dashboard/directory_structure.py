import os
import argparse
from pathlib import Path


def print_directory_structure(
    directory_path,
    prefix="",
    exclude_dirs=None,
    exclude_files=None,
    max_depth=None,
    current_depth=0,
):
    """
    递归打印目录结构

    参数:
        directory_path: 要显示的目录路径
        prefix: 用于格式化输出的前缀字符串
        exclude_dirs: 要排除的目录名列表
        exclude_files: 要排除的文件扩展名列表
        max_depth: 最大递归深度 (None 表示无限制)
        current_depth: 当前递归深度
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []

    # 检查最大深度
    if max_depth is not None and current_depth > max_depth:
        return

    # 获取目录内容并排序
    path = Path(directory_path)
    try:
        items = sorted(
            list(path.iterdir()), key=lambda x: (x.is_file(), x.name.lower())
        )
    except PermissionError:
        print(f"{prefix}├── {path.name}/ [权限被拒绝]")
        return

    # 遍历目录内容
    for i, item in enumerate(items):
        is_last = i == len(items) - 1

        # 检查是否应该排除此项
        if item.is_dir() and (item.name in exclude_dirs or item.name.startswith(".")):
            continue
        if item.is_file() and (
            any(item.name.endswith(ext) for ext in exclude_files)
            or item.name.startswith(".")
        ):
            continue

        # 确定显示的连接线类型
        connector = "└── " if is_last else "├── "

        # 打印当前项
        print(f"{prefix}{connector}{item.name}")

        # 如果是目录则递归
        if item.is_dir():
            # 确定下一级的前缀
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_directory_structure(
                item,
                next_prefix,
                exclude_dirs,
                exclude_files,
                max_depth,
                current_depth + 1,
            )


def main():
    parser = argparse.ArgumentParser(description="显示项目目录结构")
    parser.add_argument(
        "-p", "--path", default=".", help="要显示的目录路径 (默认为当前目录)"
    )
    parser.add_argument("-d", "--depth", type=int, help="最大递归深度")
    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        default=["__pycache__", "venv", "node_modules", ".git", ".idea", ".vscode"],
        help="要排除的目录名 (默认排除常见虚拟环境和配置目录)",
    )
    parser.add_argument(
        "--exclude-files",
        nargs="+",
        default=[".pyc", ".pyo", ".pyd"],
        help="要排除的文件扩展名 (默认排除Python编译文件)",
    )
    parser.add_argument("--show-hidden", action="store_true", help="显示隐藏文件和目录")

    args = parser.parse_args()

    # 获取绝对路径
    directory_path = os.path.abspath(args.path)

    # 确定排除列表
    exclude_dirs = [] if args.show_hidden else args.exclude_dirs
    exclude_files = [] if args.show_hidden else args.exclude_files

    # 打印标题
    print(f"项目目录结构: {directory_path}")
    print("=" * 50)

    # 打印目录的根名称
    print(os.path.basename(directory_path))

    # 打印目录结构
    print_directory_structure(
        directory_path, "  ", exclude_dirs, exclude_files, args.depth
    )


if __name__ == "__main__":
    main()
