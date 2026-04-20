from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# ---------------- INDUSTRY MAP ----------------
INDUSTRY_MAP = {
    "IT & ITES": 25585,
    "Automotive": 25554,
    "Banking and financial services": 25557,
    "Manufacturing": 25591,
    "Others": 25597
}

# ---------------- LOGIN ----------------
def login_session():
    session = requests.Session()

    try:
        session.post(
            "https://www.taxsutra.com/user/login",
            data={
                "name": os.getenv("TAXSUTRA_EMAIL"),
                "pass": os.getenv("TAXSUTRA_PASSWORD"),
                "form_id": "user_login_form"
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
    except Exception as e:
        print("Login failed:", e)

    return session


# ---------------- URL BUILDER ----------------
def build_url(keyword, start_date, end_date, industries):
    base_url = "https://www.taxsutra.com/tp/alert-rulings?"
    params = {}

    if keyword:
        params["tp_ruling_search_api_fulltext"] = keyword
    if start_date:
        params["field_date_of_ruling_value"] = start_date
    if end_date:
        params["field_date_of_ruling_value_1"] = end_date

    url = base_url + urllib.parse.urlencode(params)

    if industries:
        for ind in industries:
            if ind in INDUSTRY_MAP:
                val = INDUSTRY_MAP[ind]
                url += f"&field_industry_target_id%5B{val}%5D={val}"

    return url


# ---------------- PROCESS EACH CASE ----------------
def process_case(session, card, headers):
    try:
        case = card.select_one("h3 a")
        link = "https://www.taxsutra.com" + case["href"]

        li_items = card.select("ul li")

        citation = li_items[1].text.strip() if len(li_items) > 1 else "NA"
        taxpayer = li_items[2].text.replace("Tax Payer :", "").strip() if len(li_items) > 2 else "NA"

        # 🔥 Open case page
        res = session.get(link, headers=headers, timeout=15)
        html = res.text

        # 🔥 Extract PDF LINK
        match = re.findall(r'/download/attachment/\d+/\d+', html)
        pdf_link = "https://www.taxsutra.com" + match[0] if match else ""

        # 🔥 Extract DATE
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', html)
        date = date_match.group() if date_match else "NA"

        return {
            "taxpayer": taxpayer,
            "citation": citation,
            "date": date,
            "case_link": link,
            "pdf_link": pdf_link
        }

    except Exception as e:
        print("Error in case:", e)
        return None


# ---------------- MAIN ----------------
def run_rpa(keyword, start_date, end_date, industries):
    headers = {"User-Agent": "Mozilla/5.0"}

    session = login_session()

    url = build_url(keyword, start_date, end_date, industries)

    res = session.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    cards = soup.select("div.views-row")

    limit = 15 if len(cards) > 15 else len(cards)
    cards = cards[:limit]

    results = []

    # 🚀 MULTITHREADING (FAST FIX)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_case, session, c, headers) for c in cards]

        for f in as_completed(futures):
            result = f.result()
            if result:
                results.append(result)

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "Backend Running 🚀"


@app.route("/run", methods=["POST"])
def run():
    try:
        data = request.get_json(silent=True) or request.form

        keyword = data.get("keyword", "")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        industries = data.get("industries", [])

        if isinstance(industries, str):
            industries = [industries]

        result = run_rpa(keyword, start_date, end_date, industries)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)