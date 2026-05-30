import os
from datetime import datetime
import io
import pandas as pd
import pymysql
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_data():
    print("取得PM2.5資料中...")
    try:
        # 【關鍵修正】移除了會引發伺服器逾時的 sort 參數，並保留必要的欄位檢查
        api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_02?api_key=846e44e1-8cc5-4893-ad87-c79d2d383706&limit=1000&format=JSON"
        resp = requests.get(api_url, verify=False)

        res_json = resp.json()

        # 如果 API 真的出錯，直接印出它的錯誤回應，方便 debug
        if "records" not in res_json:
            print(f"API 未回傳標準資料。收到內容: {res_json}")
            return None

        df = pd.DataFrame(res_json["records"])
        if df.empty:
            print("API 回傳的 records 清單為空")
            return None

        # 轉換欄位名稱為小寫，防止環境部突改大小寫
        df.columns = df.columns.str.lower()
        if "pm2.5" in df.columns:
            df = df.rename(columns={"pm2.5": "pm25"})

        # 確保 pm25 轉為數字型態
        df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")

        # 只保留需要的 5 個欄位，並過濾掉重複與缺失值
        target_cols = ["site", "county", "pm25", "datacreationdate", "itemunit"]

        # 檢查欄位是否齊全
        missing_cols = [col for col in target_cols if col not in df.columns]
        if missing_cols:
            print(
                f"API 缺少必要欄位: {missing_cols}，當前擁有的欄位: {list(df.columns)}"
            )
            return None

        df1 = (
            df[target_cols]
            .drop_duplicates(subset=["site", "datacreationdate"])
            .dropna()
        )

        # 轉換成 list of tuples 方便 executemany 寫入
        data = [tuple(x) for x in df1.values]
        return data
    except Exception as e:
        print(f"抓取資料發生錯誤: {e}")
    return None


def insert_data(pm25_data):
    try:
        # 【修正】資料表名稱由 data 改為 pm25_records
        sqlstr = """
        INSERT IGNORE INTO pm25_records (site, county, pm25, datacreationdate, itemunit) 
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(sqlstr, pm25_data)
        conn.commit()

        if cursor.rowcount <= 0:
            print("目前無更新資料（資料皆已存在於 pm25_records 中）")
        else:
            print(f"成功更新 {cursor.rowcount} 筆資料至 pm25_records")
    except Exception as e:
        print(f"寫入資料庫發生錯誤: {e}")


def open_db():
    try:
        conn = pymysql.connect(
            host=os.environ.get("HOST"),
            port=int(os.environ.get("PORT", 3306)),
            user=os.environ.get("USER"),
            password=os.environ.get("PASSWORD"),
            database=os.environ.get("NAME"),
            ssl={"ca": None},
            autocommit=False,
        )
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"資料庫連線失敗: {e}")
    return None, None


def create_table():
    try:
        # 【修正】資料表名稱由 data 改為 pm25_records
        sqlstr = """
        CREATE TABLE IF NOT EXISTS pm25_records (
            id INT PRIMARY KEY AUTO_INCREMENT,
            site VARCHAR(50),
            county VARCHAR(20),
            pm25 INT,
            datacreationdate DATETIME,
            itemunit VARCHAR(20),
            UNIQUE KEY uq_site_datacreationdate (site, datacreationdate)
        );
        """
        cursor.execute(sqlstr)
        conn.commit()
        print("資料表 pm25_records 檢查/建立完成")
    except Exception as e:
        print(f"建立資料表失敗: {e}")


print("-----------------------------------------")
print(f"運行時間: {datetime.now()}")

conn, cursor = open_db()
if conn:
    print("開啟資料庫成功")
    create_table()
    pm25_list = get_data()
    if pm25_list:
        insert_data(pm25_list)
    else:
        print("目前無新資料可供寫入")
    conn.close()
else:
    print("資料庫開啟失敗！")
