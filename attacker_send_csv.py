import requests
import sys
import time

TARGET = "http://YOUR_SERVER_IP:5000/predict"  # CHANGE to your ubuntu IP

attack_type = "dos"

if len(sys.argv) > 1:
    attack_type = sys.argv[1]

print("Starting attack simulation:", attack_type)

# -----------------------------
# DoS Sample
# -----------------------------
dos_sample = {
"duration":0,
"protocol_type":"tcp",
"service":"http",
"flag":"SF",
"src_bytes":1000,
"dst_bytes":0,
"land":0,
"wrong_fragment":0,
"urgent":0,
"hot":0,
"num_failed_logins":0,
"logged_in":1,
"num_compromised":0,
"root_shell":0,
"su_attempted":0,
"num_root":0,
"num_file_creations":0,
"num_access_files":0,
"num_outbound_cmds":0,
"is_guest_login":0,
"count":500,
"srv_count":500,
"serror_rate":1,
"srv_serror_rate":1,
"rerror_rate":0,
"srv_rerror_rate":0,
"same_srv_rate":1,
"diff_srv_rate":0,
"srv_diff_host_rate":0,
"dst_host_count":255,
"dst_host_srv_count":255,
"dst_host_same_srv_rate":1,
"dst_host_diff_srv_rate":0,
"dst_host_same_src_port_rate":1,
"dst_host_srv_diff_host_rate":0,
"dst_host_serror_rate":1,
"dst_host_srv_serror_rate":1,
"dst_host_rerror_rate":0,
"dst_host_srv_rerror_rate":0
}

# -----------------------------
# R2L Sample
# -----------------------------
r2l_sample = dos_sample.copy()

r2l_sample.update({
"service":"ftp",
"flag":"REJ",
"num_failed_logins":5,
"logged_in":0,
"count":120,
"srv_count":120
})

# -----------------------------
# U2R Sample
# -----------------------------
u2r_sample = dos_sample.copy()

u2r_sample.update({
"service":"http",
"root_shell":1,
"su_attempted":1,
"num_compromised":5,
"num_root":3,
"num_file_creations":2
})

# -----------------------------
# Choose Sample
# -----------------------------
if attack_type == "dos":
    sample = dos_sample
elif attack_type == "r2l":
    sample = r2l_sample
elif attack_type == "u2r":
    sample = u2r_sample
else:
    sample = dos_sample

# -----------------------------
# Send Requests
# -----------------------------
for i in range(20):

    try:

        r = requests.post(TARGET, json=sample)

        print(
            "Req", i,
            "| Status:", r.status_code,
            "| Response:", r.text
        )

    except Exception as e:
        print("Error:", e)

    time.sleep(0.5)
