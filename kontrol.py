import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj}
    requests.post(url, data=data, timeout=20)

def kurs_kontrol():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://e-yaygin.meb.gov.tr/pageKurslar.aspx", timeout=60000)
        page.wait_for_timeout(2000)

        il_kutusu = page.locator("#cmbKursIlKodu_Input")
        il_kutusu.click()
        il_kutusu.fill("")
        il_kutusu.press_sequentially("Sivas", delay=150)
        page.wait_for_timeout(2000)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)

        ilce_kutusu = page.locator("#cmbKursIlceKodu_Input")
        ilce_kutusu.click()
        ilce_kutusu.fill("")
        ilce_kutusu.press_sequentially("Merkez", delay=150)
        page.wait_for_timeout(2000)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

        page.fill("#txtKursAdi", "Hijyen")
        page.click("#btnSearch")
        page.wait_for_timeout(4000)

        tablo_metni = page.inner_text("#rgKurslar")

        if "Gösterilecek kayıt bulunmamaktadır" not in tablo_metni and "Sivas" in tablo_metni and "Hijyen" in tablo_metni:
            telegram_gonder("🚨 [TEST] e-Yaygın'da Sivas Merkez için Hijyen Kursu açık görünüyor! Link: https://e-yaygin.meb.gov.tr/pageKurslar.aspx")

        browser.close()

if __name__ == "__main__":
    kurs_kontrol()
