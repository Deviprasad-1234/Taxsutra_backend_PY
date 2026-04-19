from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# ---------------- INDUSTRY MAP ----------------
INDUSTRY_MAP = {
    "Adhesives": 71768,
    "Advisory / Consultancy": 50188,
    "Agriculture, Agro Products and allied activities": 53163,
    "Alcohol": 96297,
    "Apparel, Garments, Fashion industry": 54200,
    "Assembling": 89836,
    "Automotive": 25554,
    "Aviation": 25555,
    "Banking and financial services": 25557,
    "Boarding, Lodging and Hospitality": 25576,
    "Books, Periodicals and Publications": 53519,
    "BPO services": 88219,
    "Business support services": 25559,
    "Canteen services": 88283,
    "Cement": 52893,
    "Chartered Accountants": 76010,
    "Chemicals": 50312,
    "Clubs": 52890,
    "Co-operative Society": 53792,
    "Cosmetics": 54266,
    "Dairy": 49819,
    "Database": 52985,
    "Defence equipments": 55588,
    "Design and development": 71721,
    "DTH": 89210,
    "E-Commerce": 25566,
    "Education and Training": 52337,
    "Electronic and Electrical items": 52340,
    "Engineering": 52468,
    "Event management": 55689,
    "FMCG": 52829,
    "Food and Beverage": 49916,
    "Forest and Plantation": 52949,
    "Gaming": 25572,
    "Gems & Jewellery": 25573,
    "Glass": 52646,
    "Government": 53592,
    "Imports and Exports": 52195,
    "Industrial Supplies": 52723,
    "Infrastructure": 25579,
    "Insurance": 25580,
    "Investment": 44618,
    "Irrigation": 52282,
    "IT & ITES": 25585,
    "Job work": 52885,
    "Liquor": 53587,
    "LLP/Partnership firm": 44715,
    "Lottery": 52386,
    "Manpower and Human resource": 52943,
    "Manufacturing": 25591,
    "Marketing support services": 25592,
    "Media and Entertainment": 25593,
    "Mining, Metals and Minerals": 49946,
    "NBFC": 57183,
    "Oil and gas": 52539,
    "Others": 25597,
    "Packaging": 53722,
    "Paint": 52900,
    "Paper": 52326,
    "Pharma, Healthcare and Medical supplies": 57864,
    "Plastic": 52285,
    "Plywood": 55098,
    "Ports": 56115,
    "Poultry, Animal Husbandry, Fisheries": 53618,
    "Power and energy": 52598,
    "Printing": 93057,
    "R&D": 94219,
    "Railways": 52318,
    "Real estate and construction": 52229,
    "Religious institutions, Trusts, NGOs, Non-profit organisations, Charitable trusts": 52260,
    "Renewable energy": 52434,
    "Restaurant": 49951,
    "Retail": 25604,
    "Rubber": 56170,
    "Sales": 92541,
    "Scrap": 53893,
    "Security": 54736,
    "Service": 25606,
    "Shipping": 25607,
    "Space and Communications": 44487,
    "Sports": 50358,
    "Stationery": 56161,
    "Steel": 56806,
    "Telecom services": 25609,
    "Textile": 25613,
    "Tiles": 52402,
    "Tobacco": 25614,
    "Trading & Distribution": 25616,
    "Transportation": 52923,
    "Travel and Tourism": 25615,
    "Warehousing, Logistics and Storage facilities": 25588,
    "Waterway": 52585
}

# ---------------- BUILD URL ----------------
def build_url(keyword, start_date, end_date, industries):
    base_url = "https://www.taxsutra.com/tp/alert-rulings?"

    params = {}

    # Optional keyword
    if keyword:
        params["tp_ruling_search_api_fulltext"] = keyword

    # Optional dates
    if start_date:
        params["field_date_of_ruling_value"] = start_date
    if end_date:
        params["field_date_of_ruling_value_1"] = end_date

    url = base_url + urllib.parse.urlencode(params)

    # Optional industries (single/multiple)
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

                citation = li_items[1].text.strip() if len(li_items) > 1 else "NA"
                taxpayer = li_items[2].text.strip() if len(li_items) > 2 else "NA"

                date = card.select_one("div").text.strip()

                results.append({
                    "taxpayer": taxpayer,
                    "citation": citation,
                    "date": date,
                    "link": link
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

        # Handle all cases: none / single / multiple
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
    app.run(host="0.0.0.0", port=5000)