import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mesaj})

def kurs_kontrol():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://e-yaygin.meb.gov.tr/pageKurslar.aspx", timeout=60000)
        page.wait_for_timeout(2000)

        # 1. İl Seçimi (SİVAS)
        il_kutusu = page.locator("#cmbKursIlKodu_Input")
        il_kutusu.click()
        il_kutusu.fill("SİVAS")
        page.wait_for_timeout(1500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)

        # 2. İlçe Seçimi (MERKEZ)
        ilce_kutusu = page.locator("#cmbKursIlceKodu_Input")
        ilce_kutusu.click()
        ilce_kutusu.fill("MERKEZ")
        page.wait_for_timeout(1500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)

        # 3. Kurs Adı Yazma ve Arama
        page.fill("#txtKursAdi", "Hijyen")
        page.click("#btnSearch")
        page.wait_for_timeout(4000)

        # 4. Sonuç Tablosunu Kontrol Etme
        tablo_metni = page.inner_text("#rgKurslar")

        if "Gösterilecek kayıt bulunmamaktadır" in tablo_metni and "HİJYEN" in tablo_metni.upper():
            telegram_gonder("🚨 e-Yaygın'da Sivas Merkez için yeni Hijyen Kursu açıldı! Hemen başvur: https://e-yaygin.meb.gov.tr/pageKurslar.aspx")

        browser.close()

if __name__ == "__main__":
    kurs_kontrol()
