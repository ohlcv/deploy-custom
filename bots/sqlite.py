import sqlite3
import os
from tabulate import tabulate

# ===== 硬编码参数 =====
# 数据库文件路径 - 请修改为你的SQLite文件路径
# DB_PATH = r"C:\Users\Excoldinwarm\Desktop\hummingbot\deploy-custom\bots\archived\hummingbot-test_bot-2025.04.14_12.57\data\\test_bot-2025.sqlite"
# DB_PATH = r"C:\Users\Excoldinwarm\Desktop\hummingbot\deploy-custom\bots\archived\hummingbot-test_bot-2025.04.15_08.12\data\test_bot-2025.sqlite"
# DB_PATH = r"C:\Users\Excoldinwarm\Desktop\hummingbot\deploy-custom\bots\archived\hummingbot-test_bot-2025.04.15_08.12\data\v2_with_controllers.sqlite"
DB_PATH = r"C:\Users\Excoldinwarm\Desktop\hummingbot\deploy-custom\bots\data\\checkpoint_1744707632.sqlite"
# 每个表显示的最大行数
MAX_ROWS = 10
# ===================


def connect_to_db(db_path):
    """连接到SQLite数据库"""
    if not os.path.exists(db_path):
        print(f"错误: 文件 '{db_path}' 不存在")
        return None

    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"连接数据库时出错: {e}")
        return None


def get_tables(conn):
    """获取数据库中的所有表"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]


def get_table_schema(conn, table_name):
    """获取表的结构"""
    cursor = conn.cursor()
    # 使用引号包围表名，避免保留关键字问题
    cursor.execute(f'PRAGMA table_info("{table_name}");')
    schema = cursor.fetchall()
    return schema


def display_table_data(conn, table_name, limit=10):
    """显示表中的数据"""
    cursor = conn.cursor()
    try:
        # 使用引号包围表名，避免保留关键字问题
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT {limit};')
        rows = cursor.fetchall()

        # 获取列名
        column_names = [description[0] for description in cursor.description]

        # 使用tabulate打印表格
        print(f"\n表 '{table_name}' 的数据 (最多 {limit} 行):")
        print(tabulate(rows, headers=column_names, tablefmt="grid"))

        # 获取总行数
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
        total_rows = cursor.fetchone()[0]
        print(f"总计: {total_rows} 行")

        return True
    except sqlite3.Error as e:
        print(f"查询表 '{table_name}' 时出错: {e}")
        return False


def main():
    # 使用硬编码参数
    db_path = DB_PATH
    conn = connect_to_db(db_path)

    if conn is None:
        return

    tables = get_tables(conn)
    if not tables:
        print("数据库中没有表")
        conn.close()
        return

    print(f"数据库路径: {db_path}")
    print(f"数据库中共有 {len(tables)} 个表: {', '.join(tables)}")
    print("=" * 80)

    # 显示所有表的信息
    for table_name in tables:
        print("\n" + "=" * 80)
        print(f"表名: {table_name}")
        print("=" * 80)

        # 显示表结构
        try:
            schema = get_table_schema(conn, table_name)
            print(f"\n表 '{table_name}' 的结构:")
            headers = ["ID", "名称", "类型", "非空", "默认值", "主键"]
            print(tabulate(schema, headers=headers, tablefmt="grid"))

            # 显示表数据
            display_table_data(conn, table_name, MAX_ROWS)
        except sqlite3.Error as e:
            print(f"处理表 '{table_name}' 时出错: {e}")
            continue

    conn.close()
    print("\n" + "=" * 80)
    print("所有表的信息已显示完毕")


if __name__ == "__main__":
    main()
