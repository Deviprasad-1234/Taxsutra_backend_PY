from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import os
import json

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

# ---------------- GOOGLE SHEET ----------------
def setup_google_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

    client = gspread.authorize(creds)

    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1umYaxUBQawVIBemC7KT1LrM3RrbJ66aEqLnn0GhqF5I"
    ).sheet1

    return sheet

# ---------------- CHROME DRIVER ----------------
def get_driver():
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)

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

# ---------------- MAIN RPA ----------------
def run_rpa(keyword, start_date, end_date, industries):

    driver = get_driver()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.taxsutra.com/user/login")

        wait.until(EC.presence_of_element_located((By.ID, "edit-name"))).send_keys("abhijeet.mane@pwandaffiliates.com")
        driver.find_element(By.ID, "edit-pass").send_keys("Tax@1234")
        driver.find_element(By.ID, "edit-submit").click()

        time.sleep(5)

        try:
            driver.find_element(By.ID, "edit-reset").click()
            time.sleep(3)
        except:
            pass

        url = build_url(keyword, start_date, end_date, industries)
        driver.get(url)
        time.sleep(5)

        while True:
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="block-taxsutra-digital-content"]//ul/li/a')
                ))
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
            except:
                break

        cards = driver.find_elements(
            By.XPATH,
            '//*[@id="block-taxsutra-digital-content"]//div[contains(@class,"views-row")]'
        )

        sheet = setup_google_sheet()

        count = 0

        for card in cards:
            if count >= 15:
                break

            try:
                case_el = card.find_element(By.XPATH, './/h3/a')
                link = case_el.get_attribute("href")

                citation = card.find_element(By.XPATH, './/ul/li[2]').text.strip()
                taxpayer = card.find_element(By.XPATH, './/ul/li[3]').text.strip()
                date = card.find_element(By.XPATH, './/div').text.strip()

                sheet.append_row([taxpayer, citation, date, link])

                count += 1

            except:
                continue

        return {"status": "success", "rows_added": count}

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run", methods=["GET", "POST"])
def run():
    if request.method == "GET":
        return "Use POST request"

    # 🔥 FIX FOR FORM + JSON
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    keyword = data.get("keyword")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    industries = data.get("industries")

    if isinstance(industries, str):
        industries = [industries]

    result = run_rpa(keyword, start_date, end_date, industries)

    return jsonify(result)

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)