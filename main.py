from flask import Flask, render_template
import database

app = Flask(__name__)


@app.route("/")
def index():

    result = database.get_latest_data()
    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
