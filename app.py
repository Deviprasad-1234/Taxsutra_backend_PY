from flask import Flask, request, jsonify
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
    "IT & ITES": 25585,
    "Banking and financial services": 25557,
    "Automotive": 25554,
    "Manufacturing": 25591,
    "E-Commerce": 25566
}

# ---------------- GOOGLE SHEETS ----------------
def setup_google_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # 🔥 Load from ENV (Railway)
    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

    client = gspread.authorize(creds)

    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1umYaxUBQawVIBemC7KT1LrM3RrbJ66aEqLnn0GhqF5I"
    ).sheet1

    return sheet

# ---------------- CHROME DRIVER (RAILWAY FIX) ----------------
def get_driver():
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Railway auto-detects chrome
    return webdriver.Chrome(options=chrome_options)

# ---------------- BUILD URL ----------------
def build_url(keyword, start_date, end_date, industries):

    base_url = "https://www.taxsutra.com/tp/alert-rulings?"

    params = {
        "tp_ruling_search_api_fulltext": keyword,
        "field_tax_payer_name_tp_target_id": "",
        "field_judge_profile_tp_target_id": "",
        "field_counsel_for_department_target_id": "",
        "field_counsel_of_taxpayer_tp_target_id": "",
        "field_section_no_under_income_target_id": "All",
        "field_tp_citation_value": "",
        "field_serial_value": "_none",
        "field_applevel_value": "_none",
        "field_year_value": "_none",
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
        # ---------------- LOGIN ----------------
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

        print("✅ Login successful")

        # ---------------- FILTER URL ----------------
        url = build_url(keyword, start_date, end_date, industries)
        driver.get(url)
        time.sleep(5)

        # ---------------- LOAD MORE ----------------
        while True:
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="block-taxsutra-digital-content"]//ul/li/a')
                ))
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
            except:
                break

        print("📄 All results loaded")

        # ---------------- EXTRACT ----------------
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
                case_name = case_el.text.strip()
                link = case_el.get_attribute("href")

                try:
                    citation = card.find_element(By.XPATH, './/ul/li[2]').text.strip()
                except:
                    citation = "NA"

                try:
                    taxpayer = card.find_element(By.XPATH, './/ul/li[3]').text.strip()
                except:
                    taxpayer = case_name

                try:
                    date = card.find_element(By.XPATH, './/div').text.strip()
                except:
                    date = "NA"

                sheet.append_row([
                    taxpayer,
                    citation,
                    date,
                    link
                ])

                count += 1

            except Exception as e:
                print("Error:", e)

        return {"status": "success", "rows_added": count}

    finally:
        driver.quit()

# ---------------- API ----------------
@app.route("/")
def home():
    return "✅ Railway backend running"

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()

    result = run_rpa(
        data["keyword"],
        data["start_date"],
        data["end_date"],
        data["industries"]
    )

    return jsonify(result)

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)