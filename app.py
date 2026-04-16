from flask import Flask, render_template, request, session
import pickle
from features import extract_features
from urllib.parse import urlparse
import re
import time

app = Flask(__name__)
app.secret_key = "secret123"

model = pickle.load(open("model.pkl", "rb"))

# ✅ Basic validation
def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and parsed.netloc != ""


# 🧠 Risk scoring
def calculate_risk(url):
    parsed = urlparse(url)
    score = 0
    reasons = []

    if re.search(r'\d+\.\d+\.\d+\.\d+', url):
        score += 3
        reasons.append("Uses IP address")

    if re.search(r'login|secure|bank|verify|update', url.lower()):
        score += 2
        reasons.append("Suspicious keywords")

    special_chars = sum(url.count(c) for c in ['?', '=', '&', '%'])
    if special_chars > 3:
        score += 2
        reasons.append("Too many special characters")

    if len(url) > 120:
        score += 1
        reasons.append("Long URL")

    if parsed.netloc.count('.') > 3:
        score += 2
        reasons.append("Too many subdomains")

    if '#' in url:
        score += 1
        reasons.append("Contains fragment (#)")

    return score, reasons


# 🔐 Lock check
def check_lock():
    lock_time = session.get("lock_time", 0)
    if time.time() < lock_time:
        remaining = int(lock_time - time.time())
        return True, remaining
    return False, 0


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    confidence = None
    reasons = []
    risk_level = None

    # 🔒 Check lock
    locked, remaining = check_lock()
    if locked:
        return render_template(
            "index.html",
            result="System Locked 🔒",
            reasons=[f"Too many attempts. Try again in {remaining}s"],
            risk_level="invalid"
        )

    if request.method == "POST":
        url = request.form["url"]

        attempts = session.get("attempts", 0)

        # ❌ Invalid URL
        if not is_valid_url(url):
            attempts += 1
            session["attempts"] = attempts

            if attempts >= 3:
                session["lock_time"] = time.time() + 30
                session["attempts"] = 0

                return render_template(
                    "index.html",
                    result="System Locked 🔒",
                    reasons=["Too many invalid attempts. Wait 30 seconds"],
                    risk_level="invalid"
                )

            return render_template(
                "index.html",
                result="Invalid URL ❌",
                reasons=[f"Attempt {attempts}/3"],
                risk_level="invalid"
            )

        # ✅ Reset attempts
        session["attempts"] = 0

        # 🔍 Risk + ML
        score, reasons = calculate_risk(url)

        features = extract_features(url)
        prediction = model.predict([features])[0]
        prob = model.predict_proba([features])[0]
        confidence = round(max(prob) * 100, 2)

        if score >= 5 or prediction == 1:
            result = "🚨 High Risk (Phishing)"
            risk_level = "high"
        elif score >= 3:
            result = "⚠️ Suspicious"
            risk_level = "medium"
        else:
            result = "✅ Safe"
            risk_level = "low"

    return render_template(
        "index.html",
        result=result,
        confidence=confidence,
        reasons=reasons,
        risk_level=risk_level
    )


if __name__ == "__main__":
    app.run(debug=True)