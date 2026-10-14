import os
import pymssql
from flask import Flask, jsonify, request
from openai import AzureOpenAI

app = Flask(__name__)

ai_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_AI_KEY"),
    azure_endpoint=os.environ.get("AZURE_AI_ENDPOINT"),
    api_version="2025-01-01-preview"
)

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
        "version": "3.0",
        "endpoints": {
            "GET /errors": "List all known error codes",
            "POST /analyze": "Analyze an error code and get resolution guidance",
            "POST /ask": "Ask a free-text question about an ICS error"
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


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Missing 'question' in request body"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT error_code, description, likely_cause, suggested_fix FROM errors")
    rows = cursor.fetchall()
    conn.close()

    context = "\n".join([
        f"{row[0]}: {row[1]} Cause: {row[2]} Fix: {row[3]}"
        for row in rows
    ])

    response = ai_client.chat.completions.create(
        model=os.environ.get("AZURE_AI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": f"You are an ICS integration support assistant. Use this error knowledge base to answer questions:\n\n{context}"},
            {"role": "user", "content": data["question"]}
        ],
        max_tokens=500
    )

    return jsonify({"answer": response.choices[0].message.content})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
