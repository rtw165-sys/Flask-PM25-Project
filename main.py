from datetime import datetime
from flask import Flask, jsonify, render_template
import pandas as pd
import database  # 確保你的 database.py 裡面已經將資料表改為 pm25_records

app = Flask(__name__)


@app.errorhandler(404)
def error_404(e):
    return render_template("404.html")


@app.route("/api/data/six-county")
def api_data_six_county():
    six_county = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
    result = database.get_latest_data()

    avg_pm25 = []
    if result["success"] and result["rows"]:
        # 將資料轉成 DataFrame 並塞入正確的欄位名稱
        df = pd.DataFrame(result["rows"], columns=result["columns"])

        for county in six_county:
            # 安全篩選：避免 groupby 找不到縣市噴 KeyError
            county_df = df[df["county"] == county]
            if not county_df.empty:
                avg_val = county_df["pm25"].mean()
                # 檢查平均值是否為有效數字 (避免 NaN)
                avg_pm25.append(round(avg_val, 2) if pd.notna(avg_val) else 0)
            else:
                avg_pm25.append(0)  # 若該縣市暫時無資料，預設給 0
    else:
        avg_pm25 = [0] * len(six_county)

    return jsonify(
        {
            "datetime": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # 【修正】轉為字串以利 jsonify
            "labels": six_county,
            "values": avg_pm25,
        }
    )


@app.route("/api/data/<county>")
def api_data_by_county(county):
    # 建議回傳格式標準化，讓前端好拿資料
    res = database.get_data_by_county(county)
    if res["success"]:
        return jsonify({"columns": res["columns"], "rows": res["rows"]})
    return jsonify({"success": False, "message": res["message"]}), 500


@app.route("/api/counties")
def api_counties():
    counties_res = database.get_counties()
    if counties_res["success"]:
        counties = [c[0] for c in counties_res["rows"]]
        return jsonify(counties)
    return jsonify([]), 500


@app.route("/")
def index():
    result = database.get_latest_data()
    counties_res = database.get_counties()
    counties = [c[0] for c in counties_res["rows"]] if counties_res["success"] else []

    data = {}
    if result["success"] and result["rows"]:
        # 【優化】使用 DataFrame 處理全台極值，避免硬編碼 [1][3] 欄位索引錯位
        df = pd.DataFrame(result["rows"], columns=result["columns"])

        # 找出 pm25 最小與最大的那一行資料
        min_row = df.loc[df["pm25"].idxmin()]
        max_row = df.loc[df["pm25"].idxmax()]

        # 取出資料時間 (轉成字串丟給前端)
        data_datetime = df["datacreationdate"].iloc[0]
        if isinstance(data_datetime, datetime):
            data_datetime = data_datetime.strftime("%Y-%m-%d %H:%M:%S")

        data["datetime"] = data_datetime
        data["min"] = [min_row["site"], int(min_row["pm25"])]
        data["max"] = [max_row["site"], int(max_row["pm25"])]

    return render_template("index.html", result=result, counties=counties, data=data)


if __name__ == "__main__":
    # debug=True 適合開發環境，會自動重載程式碼
    app.run(debug=True)
