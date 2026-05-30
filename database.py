import os
from datetime import datetime
from dotenv import load_dotenv
import pymysql

load_dotenv()


def open_db():
    try:
        conn = pymysql.connect(
            host=os.environ.get("HOST"),
            port=int(os.environ.get("PORT")),
            user=os.environ.get("USER"),
            password=os.environ.get("PASSWORD"),
            database=os.environ.get("NAME"),
            ssl={"ca": None},
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"資料庫連線失敗: {e}")
    return None, None


# 1. 根據縣市取得最新一筆觀測資料
def get_data_by_county(county):
    conn, cursor = open_db()
    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗"
        return result

    # 【修正】全面更名為 pm25_records，並修正子查詢
    sql = """
    SELECT * FROM pm25_records 
    WHERE county = %s 
      AND datacreationdate = (SELECT MAX(datacreationdate) FROM pm25_records);
    """

    try:
        cursor.execute(sql, (county,))
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        result["success"] = True
        result["columns"] = columns
        result["rows"] = rows
        return result
    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗: {e}"
        return result
    finally:
        conn.close()


# 2. 取得不重複縣市
def get_counties():
    conn, cursor = open_db()
    result = {"success": True, "message": None, "rows": []}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗"
        return result

    sql = "SELECT DISTINCT county FROM pm25_records ORDER BY county DESC;"
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        result["success"] = True
        result["rows"] = rows
        return result
    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗: {e}"
        return result
    finally:
        conn.close()


# 3. 取得全台最新觀測資料
def get_latest_data():
    conn, cursor = open_db()
    result = {"success": True, "message": None, "columns": None, "rows": None}

    if not conn:
        result["success"] = False
        result["message"] = "資料庫開啟失敗"
        return result

    sql = """
    SELECT * FROM pm25_records 
    WHERE datacreationdate = (SELECT MAX(datacreationdate) FROM pm25_records);
    """
    try:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        result["success"] = True
        result["columns"] = columns
        result["rows"] = rows
        return result
    except Exception as e:
        result["success"] = False
        result["message"] = f"資料庫查詢失敗: {e}"
        return result
    finally:
        conn.close()


if __name__ == "__main__":
    print("--- 測試查詢新北市最新 PM2.5 資料 ---")
    print(get_data_by_county("新北市"))
