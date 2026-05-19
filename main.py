from flask import Flask, render_template, jsonify
import database
import pandas as pd
from datetime import datetime

app = Flask(__name__)


@app.errorhandler(404)
def error_404(e):
    return render_template("404.html")


@app.route("/api/data/six-county")
def api_data_six_county():
    six_county = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
    result = database.get_latest_data()

    avg_pm25 = []
    if result["success"]:
        df = pd.DataFrame(result["rows"], columns=result["columns"])
        for county in six_county:
            avg_pm25.append(
                df.groupby("county").get_group(county)["pm25"].mean().round(2)
            )

    return jsonify(
        {"datetime": datetime.now(), "labels": six_county, "values": avg_pm25}
    )


@app.route("/api/data/<county>")
def api_data_by_county(county):
    rows = database.get_data_by_county(county)["rows"]
    return jsonify(rows)


@app.route("/api/counties")
def api_counties():
    counties = database.get_counties()["rows"]
    counties = [c[0] for c in counties]

    return jsonify(counties)


@app.route("/")
def index():
    result = database.get_latest_data()
    counties = database.get_counties()["rows"]
    counties = [c[0] for c in counties]

    data = {}
    if result["success"]:
        datetime = result["rows"][0][4]
        datas = sorted(result["rows"], key=lambda x: x[3])
        min_values = datas[0]
        max_values = datas[-1]
        print(datetime, min_values, max_values)

        data["datetime"] = datetime
        data["min"] = [min_values[1], min_values[3]]
        data["max"] = [max_values[1], max_values[3]]

    return render_template("index.html", result=result, counties=counties, data=data)


if __name__ == "__main__":
    app.run(debug=True)
