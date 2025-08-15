from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import os
import re

app = Flask(__name__)
# Configure CORS
cors = CORS()
cors.init_app(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


def clean_output(log_text):
    # Extract all tool names
    tools = re.findall(r"Calling tools:\s*([a-zA-Z0-9_]+)", log_text)

    # Extract the final workflow result (last match)
    workflow_results = re.findall(r"Workflow Result:\s*\[(.*?)\]", log_text, re.DOTALL)
    final_result = workflow_results[-1] if workflow_results else None


    # Remove back to back tool uses
    result = []
    prev = object()  
    for item in tools:
        if item != prev:
            result.append(item)
        prev = item

    # Make output string make sense
    string = "\n Used Tool: ".join(result)
    string = string[3:]
    string = string + "\n" + final_result

    return final_result



def run_nat(prompt):
    cmd = [
        "nat",
        "run",
        "--config_file", "examples/datadog_rca/workflow.yaml",
        "--input", prompt
    ]
    print(cmd)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stderr)

        return {
            "success": True,
            "stdout": clean_output(result.stderr),
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        print("Exception: ", e)
        return {
            "success": False,
            "error": str(e)
        }

@app.route("/", methods=["GET", "POST", "OPTIONS"])
def handle_requests():
    if request.method == "OPTIONS":
        return "", 200
        
    if request.method == "GET":
        return "Server is running. Send POST requests to this endpoint with a JSON body containing a 'prompt' field."
    
    # Handle POST request
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "No prompt provided"}), 400
    
    result = run_nat(data["prompt"])
    if result["success"]:
        return jsonify({
            "status": "success",
            "output": result["stdout"],
            "error": result["stderr"]
        })
    else:
        return jsonify({
            "status": "error",
            "error": result["error"]
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)