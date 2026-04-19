from flask import Flask, request, jsonify, render_template
import bs4
import requests
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import os
import json

app = Flask(__name__)
print("🚀 APP STARTED")

# ---------------- INDUSTRY MAP ----------------
INDUSTRY_MAP = {
    "IT & ITES": 25585,
    "Banking and financial services": 25557,
    "Automotive": 25554,
    "Manufacturing": 25591,
    "E-Commerce": 25566
}

# ---------------- GOOGLE SHEET ----------------
def setup_google_sheet():
    try:
        print("🔍 Checking GOOGLE_CREDS...")

        raw = os.environ.get("GOOGLE_CREDS")

        if not raw:
            print("❌ GOOGLE_CREDS not found")
            return None

        print("✅ GOOGLE_CREDS found")

        creds_dict = json.loads(raw)

        print("✅ JSON loaded")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        print("✅ Credentials created")

        client = gspread.authorize(creds)

        print("✅ gspread authorized")

        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1umYaxUBQawVIBemC7KT1LrM3RrbJ66aEqLnn0GhqF5I"
        ).sheet1

        print("✅ SHEET CONNECTED SUCCESSFULLY")

        return sheet

    except Exception as e:
        print("❌ GOOGLE SHEET ERROR:", str(e))
        return None
# ---------------- BUILD URL ----------------
def build_url(keyword, start_date, end_date, industries):

    base_url = "https://www.taxsutra.com/tp/alert-rulings?"

    params = {
        "tp_ruling_search_api_fulltext": keyword,
        "field_date_of_ruling_value": start_date,
        "field_date_of_ruling_value_1": end_date
    }

    url = base_url + urllib.parse.urlencode(params)

    for ind in industries:
        ind_id = INDUSTRY_MAP.get(ind)
        if ind_id:
            url += f"&field_industry_target_id%5B{ind_id}%5D={ind_id}"

    return url

# ---------------- MAIN SCRAPER ----------------
def run_rpa(keyword, start_date, end_date, industries):

    try:
        url = build_url(keyword, start_date, end_date, industries)
        print("Fetching URL:", url)

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("div.views-row")

        sheet = setup_google_sheet()

        if not sheet:
            return {"error": "Google Sheet not connected"}

        count = 0

        for card in cards[:15]:
            try:
                case = card.select_one("h3 a")
                link = "https://www.taxsutra.com" + case["href"]

                li_items = card.select("ul li")

                citation = li_items[1].text.strip() if len(li_items) > 1 else "NA"
                taxpayer = li_items[2].text.strip() if len(li_items) > 2 else "NA"

                date = card.select_one("div").text.strip()

                sheet.append_row([taxpayer, citation, date, link])

                count += 1

            except Exception as e:
                print("Row error:", e)

        return {"status": "success", "rows_added": count}

    except Exception as e:
        print("Main error:", e)
        return {"error": str(e)}

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run", methods=["GET", "POST"])
def run():
    try:
        if request.method == "GET":
            return "Use POST request"

        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        keyword = data.get("keyword", "")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        industries = data.get("industries", [])

        if isinstance(industries, str):
            industries = [industries]

        result = run_rpa(keyword, start_date, end_date, industries)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)