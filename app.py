from flask import Flask, request, jsonify

app = Flask(__name__)

ERROR_CODES = {
    "POSTING_FAILED": {
        "description": "Financial posting to SAP ERP failed.",
        "likely_cause": "GL account not found or cost center mapping is missing.",
        "suggested_fix": "Check the GL account configuration in transaction FS00 and verify cost center assignments."
    },
    "AUTH_FAILED": {
        "description": "Authentication between SAP Concur and SAP ERP failed.",
        "likely_cause": "ICS credentials expired or RFC connection is down.",
        "suggested_fix": "Verify RFC destination in SM59 and refresh the ICS credentials in the Concur admin panel."
    },
    "DUPLICATE_ENTRY": {
        "description": "A duplicate document was detected during posting.",
        "likely_cause": "The same expense report was submitted twice or a retry loop occurred.",
        "suggested_fix": "Check document number ranges in FBN1 and review the posting log for duplicate entries."
    },
    "CURRENCY_MISMATCH": {
        "description": "Currency in the expense report does not match the ERP configuration.",
        "likely_cause": "Exchange rate missing or currency not configured in the company code.",
        "suggested_fix": "Update exchange rates in OB08 and verify currency settings in OY03."
    },
    "TIMEOUT": {
        "description": "The ICS integration request timed out.",
        "likely_cause": "SAP ERP system is under heavy load or the RFC connection is unstable.",
        "suggested_fix": "Check system performance in SM50/SM66 and review RFC timeout settings in SM59."
    },
}


@app.route("/")
def index():
    return jsonify({
        "service": "ICS Error Lookup API",
        "version": "1.0",
        "endpoints": {
            "GET /errors": "List all known error codes",
            "POST /analyze": "Analyze an error code and get resolution guidance"
        }
    })


@app.route("/errors", methods=["GET"])
def list_errors():
    return jsonify({"error_codes": list(ERROR_CODES.keys())})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "error_code" not in data:
        return jsonify({"error": "Missing 'error_code' in request body"}), 400

    code = data["error_code"].strip().upper()
    if code not in ERROR_CODES:
        return jsonify({
            "error": f"Unknown error code: {code}",
            "known_codes": list(ERROR_CODES.keys())
        }), 404

    result = ERROR_CODES[code]
    return jsonify({
        "error_code": code,
        "description": result["description"],
        "likely_cause": result["likely_cause"],
        "suggested_fix": result["suggested_fix"]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
