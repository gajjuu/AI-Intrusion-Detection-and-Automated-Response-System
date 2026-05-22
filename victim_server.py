from flask import Flask, request, jsonify
import pandas as pd
import time
from collections import defaultdict, deque
from autogluon.tabular import TabularPredictor
import numpy as np
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ================= CONFIG =================
MODEL_FOLDER = "./AutoGluon_IDS_Model_4Class"
DOS_WINDOW_S = 10
DOS_THRESHOLD = 8
BLOCK_DURATION = 60  # seconds

# ============ REQUIRED NSL-KDD FEATURES ============
REQUIRED_FEATURES = [
    'duration','protocol_type','service','flag','src_bytes','dst_bytes',
    'land','wrong_fragment','urgent','hot','num_failed_logins','logged_in',
    'num_compromised','root_shell','su_attempted','num_root',
    'num_file_creations','num_access_files','num_outbound_cmds',
    'is_guest_login','count','srv_count','serror_rate','srv_serror_rate',
    'rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate',
    'srv_diff_host_rate','dst_host_count','dst_host_srv_count',
    'dst_host_same_srv_rate','dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate','dst_host_srv_diff_host_rate',
    'dst_host_serror_rate','dst_host_srv_serror_rate',
    'dst_host_rerror_rate','dst_host_srv_rerror_rate'
]

app = Flask(__name__)
predictor = TabularPredictor.load(MODEL_FOLDER)

ip_timestamps = defaultdict(lambda: deque())
blocked_ips = {}
r2l_alerts = {}

print("Hybrid AI IDS + Response System Started")

# ================= HELPER FUNCTIONS =================
def to_python_scalar(x):
    if isinstance(x, (np.floating, np.float32, np.float64)):
        return float(x)
    if isinstance(x, (np.integer, np.int32, np.int64)):
        return int(x)
    return x

def send_email(attack, ip):
    try:
        sender = "your_email@gmail.com"
        password = "your_app_password"
        receiver = "receiver_email@gmail.com"

        msg = MIMEText(f"""
Intrusion Alert

Attack Type: {attack}
Source IP: {ip}
Time: {datetime.now()}

Automated mitigation executed.
""")

        msg["Subject"] = f"[IDS ALERT] {attack}"
        msg["From"] = sender
        msg["To"] = receiver

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)

    except Exception as e:
        print("Email Error:", e)



# ================= ROUTE =================
@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json(force=True)
    current_time = time.time()

    # Accept single sample OR batch
    if isinstance(data, list):
        samples = data
    else:
        samples = [data]

    results = []

    for sample in samples:

        src_ip = request.remote_addr

        # ---------- TEMP BLOCK CHECK ----------
        if src_ip in blocked_ips:
            if current_time - blocked_ips[src_ip] < BLOCK_DURATION:
                return jsonify({
                    "status": "blocked",
                    "message": "IP temporarily blocked due to malicious activity"
                }), 403
            else:
                del blocked_ips[src_ip]

        # ---------- DOS BEHAVIOR TRACK ----------
        dq = ip_timestamps[src_ip]
        dq.append(current_time)

        while dq and current_time - dq[0] > DOS_WINDOW_S:
            dq.popleft()

        dos_behavior = len(dq) >= DOS_THRESHOLD

        # ---------- BUILD FULL FEATURE SET ----------
        full_sample = {feat: 0 for feat in REQUIRED_FEATURES}
        for k, v in sample.items():
            if k in full_sample:
                full_sample[k] = v

        df = pd.DataFrame([full_sample])

        # ---------- ML PREDICTION ----------
        prediction = predictor.predict(df)[0]
        prediction = to_python_scalar(prediction)

        final_attack = prediction

        # ----------HYBRID RULE CORECTIONS----------
        if sample.get("num_failed_logins", 0) >= 3:
            final_attack = "R2L"

        elif sample.get("root_shell", 0) == 1 and sample.get("su_attempted", 0) == 1:
            final_attack = "U2R"


        # override using behaviour
        if dos_behavior:
            final_attack = "DoS"
  
  
        # ---------- RESPONSE LOGIC ----------
        action = "Allowed"

        if final_attack == "DoS":
            blocked_ips[src_ip] = current_time
            action = "Blocked 60s"
            send_email("DoS", src_ip)

        elif final_attack == "U2R":
            blocked_ips[src_ip] = current_time
            action = "Blocked 60s (Critical)"
            send_email("U2R", src_ip)

        elif final_attack == "R2L":
            action = "Alert Only"
            send_email("R2L", src_ip)

        print(f"[{time.strftime('%H:%M:%S')}] {src_ip} -> {final_attack} | {action}")

        results.append({
            "predicted_class": final_attack,
            "src_ip": src_ip,
            "action": action
        })

    return jsonify({
        "received": len(results),
        "results": results
    })

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
