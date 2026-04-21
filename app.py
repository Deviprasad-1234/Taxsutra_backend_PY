import time
import urllib.parse
import os

from fastapi import FastAPI, Query

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


app = FastAPI()

# ---------------- ENV ----------------
USERNAME = os.getenv("TAXSUTRA_EMAIL")
PASSWORD = os.getenv("TAXSUTRA_PASSWORD")

BASE_URL = "https://www.taxsutra.com"

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
def build_url(keyword, start_date=None, end_date=None, industries=None):

    base = "https://www.taxsutra.com/tp/alert-rulings?"

    params = {
        "tp_ruling_search_api_fulltext": keyword,
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

    url = base + urllib.parse.urlencode(params)

    if industries:
        for ind in industries:
            ind_id = INDUSTRY_MAP.get(ind)
            if ind_id:
                url += f"&field_industry_target_id%5B{ind_id}%5D={ind_id}"

    return url


# ---------------- MAIN RPA ----------------
def run_rpa(keyword, start_date=None, end_date=None, industries=None):

    url = build_url(keyword, start_date, end_date, industries)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 20)
    data = []

    try:
        # LOGIN
        driver.get("https://www.taxsutra.com/user/login")

        wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(USERNAME)
        wait.until(EC.presence_of_element_located((By.NAME, "pass"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.ID, "edit-submit"))).click()

        try:
            wait.until(EC.element_to_be_clickable((By.ID, "edit-reset"))).click()
        except:
            pass

        time.sleep(5)

        # OPEN PAGE
        driver.get(url)
        time.sleep(5)

        # LOAD MORE
        while True:
            try:
                load_more = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="block-taxsutra-digital-content"]/div/div/div/ul/li/a')
                ))
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
            except:
                break

        # GET CARDS
        cards = driver.find_elements(By.XPATH, '//div[contains(@class,"views-row")]')

        # LIMIT 15
        cards = cards[:15]

        for card in cards:
            try:
                case_link = card.find_element(By.XPATH, './/h3/a').get_attribute("href")

                li_items = card.find_elements(By.XPATH, './/ul/li')
                citation = li_items[1].text if len(li_items) > 1 else "NA"
                taxpayer = li_items[2].text if len(li_items) > 2 else "NA"

                date = card.find_element(By.XPATH, './/div').text

                driver.get(case_link)
                time.sleep(2)

                try:
                    pdf_link = driver.find_element(
                        By.XPATH, '//a[contains(@href,"/download/attachment")]'
                    ).get_attribute("href")
                except:
                    pdf_link = "Not Available"

                data.append({
                    "taxpayer": taxpayer,
                    "citation": citation,
                    "date": date,
                    "case_link": case_link,
                    "pdf_link": pdf_link
                })

                driver.back()
                time.sleep(2)

            except:
                continue

    finally:
        driver.quit()

    return data


# ---------------- API ----------------
@app.get("/")
def home():
    return {"status": "Running 🚀"}


@app.get("/run")
def run(
    keyword: str,
    start_date: str = None,
    end_date: str = None,
    industries: list[str] = Query(default=[])
):
    result = run_rpa(keyword, start_date, end_date, industries)
    return {"count": len(result), "data": result}