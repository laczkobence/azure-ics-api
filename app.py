import os
import pymssql
from flask import Flask, jsonify, request

app = Flask(__name__)

def get_connection():
    return pymssql.connect(
        server=os.environ["DB_SERVER"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"]
    )


@app.route("/")
def index():
    return jsonify({
        "service": "ICS Error Lookup API",
        "version": "2.0",
        "endpoints": {
            "GET /errors": "List all known error codes",
            "POST /analyze": "Analyze an error code and get resolution guidance"
        }
    })


@app.route("/errors", methods=["GET"])
def list_errors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT error_code FROM errors")
    codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({"error_codes": codes})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "error_code" not in data:
        return jsonify({"error": "Missing 'error_code' in request body"}), 400

    code = data["error_code"].strip().upper()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, likely_cause, suggested_fix FROM errors WHERE error_code = ?", code)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Unknown error code: {code}"}), 404

    return jsonify({
        "error_code": code,
        "description": row[0],
        "likely_cause": row[1],
        "suggested_fix": row[2]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
