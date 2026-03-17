from flask import Flask, request, jsonify, send_from_directory
import requests
import base64
import os
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")

labels = []

LABELARY_URL = "http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/"

@app.route("/")
def serve_ui():
    return send_from_directory("static", "index.html")

@app.route("/zpl", methods=["POST"])
def receive_zpl():
    global labels

    data = request.get_json(silent=True)

    if data and "zpl" in data:
        zpl = data["zpl"]
    else:
        zpl = request.data.decode("utf-8")

    if not zpl:
        return jsonify({"error": "Missing ZPL"}), 400

    print("ZPL RECEIVED:")
    print(repr(zpl))

    response = requests.post(
        LABELARY_URL,
        headers={"Accept": "image/png"},
        files={"file": zpl}
    )

    if response.status_code != 200:
        return jsonify({"error": response.text}), 500

    image_base64 = base64.b64encode(response.content).decode("utf-8")

    labels.insert(0, image_base64)
    labels = labels[:10]
    
    import time
    import uuid

    label_data = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": time.strftime("%H:%M:%S"),
        "image": image_base64
    }

    socketio.emit("new_label", label_data)

    return jsonify({"message": "Label processed"}), 200


@app.route("/labels", methods=["GET"])
def get_labels():
    return jsonify(labels)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if __name__ == "__main__": 
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)