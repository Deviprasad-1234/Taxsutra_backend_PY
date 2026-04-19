from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
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

# ---------------- GOOGLE SHEET ----------------
def setup_google_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        client = gspread.authorize(creds)

        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1umYaxUBQawVIBemC7KT1LrM3RrbJ66aEqLnn0GhqF5I"
        ).sheet1

        return sheet

    except Exception as e:
        print("Google Sheet Error:", e)
        return None

# ---------------- CHROME DRIVER ----------------
def get_driver():
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")

    options.binary_location = "/usr/bin/chromium"

    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

    except Exception as e:
        print("Driver Error:", e)
        raise e

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
    wait = WebDriverWait(driver, 30)

    try:
        print("Starting login...")

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

        print("Login successful")

        url = build_url(keyword, start_date, end_date, industries)
        print("Opening URL:", url)

        driver.get(url)
        time.sleep(5)

        # LOAD MORE
        while True:
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="block-taxsutra-digital-content"]//ul/li/a')
                ))
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
            except:
                break

        print("Loaded all results")

        cards = driver.find_elements(
            By.XPATH,
            '//*[@id="block-taxsutra-digital-content"]//div[contains(@class,"views-row")]'
        )

        sheet = setup_google_sheet()

        if not sheet:
            return {"error": "Google Sheet not connected"}

        count = 0

        for card in cards:
            if count >= 15:
                break

            try:
                case_el = card.find_element(By.XPATH, './/h3/a')
                link = case_el.get_attribute("href")

                try:
                    citation = card.find_element(By.XPATH, './/ul/li[2]').text.strip()
                except:
                    citation = "NA"

                try:
                    taxpayer = card.find_element(By.XPATH, './/ul/li[3]').text.strip()
                except:
                    taxpayer = "NA"

                try:
                    date = card.find_element(By.XPATH, './/div').text.strip()
                except:
                    date = "NA"

                sheet.append_row([taxpayer, citation, date, link])

                count += 1

            except Exception as e:
                print("Row Error:", e)

        return {"status": "success", "rows_added": count}

    except Exception as e:
        print("RPA Error:", e)
        return {"error": str(e)}

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run", methods=["GET", "POST"])
def run():
    try:
        if request.method == "GET":
            return "Use POST request"

        # Handle JSON + FORM
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        print("Received:", data)

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