from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

app = Flask(__name__)

# ---------------- INDUSTRY MAP ----------------
INDUSTRY_MAP = {
    "IT & ITES": 25585,
    "Automotive": 25554,
    "Banking and financial services": 25557,
    "Manufacturing": 25591,
    "Others": 25597
}

# ---------------- BUILD URL ----------------
def build_url(keyword, start_date, end_date, industries):
    base_url = "https://www.taxsutra.com/tp/alert-rulings?"

    params = {
        "tp_ruling_search_api_fulltext": keyword or "",
        "field_tax_payer_name_tp_target_id": "",
        "field_judge_profile_tp_target_id": "",
        "field_counsel_for_department_target_id": "",
        "field_counsel_of_taxpayer_tp_target_id": "",
        "field_date_of_ruling_value": start_date or "",
        "field_date_of_ruling_value_1": end_date or "",
        "field_section_no_under_income_target_id": "All",
        "field_tp_citation_value": "",
        "field_serial_value": "_none",
        "field_applevel_value": "_none",
        "field_year_value": "_none"
    }

    url = base_url + urllib.parse.urlencode(params)

    # Industries (optional)
    if industries:
        for ind in industries:
            ind_id = INDUSTRY_MAP.get(ind)
            if ind_id:
                url += f"&field_industry_target_id%5B{ind_id}%5D={ind_id}"

    return url

# ---------------- MAIN SCRAPER ----------------
def run_rpa(keyword, start_date, end_date, industries):
    try:
        url = build_url(keyword, start_date, end_date, industries)

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("div.views-row")

        results = []

        for card in cards[:15]:
            try:
                case = card.select_one("h3 a")
                link = "https://www.taxsutra.com" + case["href"]

                li_items = card.select("ul li")

                # -------- STATUS EXTRACTION --------
                status_text = li_items[0].text.strip() if len(li_items) > 0 else ""

                if "Assessee" in status_text:
                    ruling_status = "In Favour of Assessee"
                elif "Revenue" in status_text:
                    ruling_status = "In Favour of Revenue"
                elif "Partly" in status_text or "Partial" in status_text:
                    ruling_status = "Partly in favour of both"
                else:
                    ruling_status = "None/NA"

                # -------- OTHER FIELDS --------
                citation = li_items[1].text.strip() if len(li_items) > 1 else "NA"
                taxpayer = li_items[2].text.strip() if len(li_items) > 2 else "NA"

                # Clean text
                citation = citation.replace("Citation Number :", "").strip()
                taxpayer = taxpayer.replace("Tax Payer :", "").strip()

                # -------- CLEAN DATE --------
                full_text = card.get_text(separator="\n")
                date = "NA"

                for line in full_text.split("\n"):
                    line = line.strip()
                    if any(month in line for month in ["Jan","Feb","Mar","Apr","May","Jun",
                                                      "Jul","Aug","Sep","Oct","Nov","Dec"]):
                        date = line

                results.append({
                    "taxpayer": taxpayer,
                    "citation": citation,
                    "date": date,
                    "link": link,
                    "ruling_status": ruling_status
                })

            except:
                continue

        return {
            "status": "success",
            "count": len(results),
            "data": results
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "TaxSutra Backend Running 🚀"

@app.route("/run", methods=["POST"])
def run():
    try:
        data = request.get_json(silent=True) or request.form

        keyword = data.get("keyword", "").strip()
        start_date = data.get("start_date", "").strip()
        end_date = data.get("end_date", "").strip()

        industries = data.get("industries", [])

        if isinstance(industries, str):
            industries = [industries]
        elif not industries:
            industries = []

        result = run_rpa(keyword, start_date, end_date, industries)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)