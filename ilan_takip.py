import os
import re
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj, "disable_web_page_preview": True}
    requests.post(url, data=data, timeout=20)

def siteleri_tara():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # İŞKUR CANLI TEST
        try:
            iskur_url = "https://esube.iskur.gov.tr/istihdam/AcikisilanAra.aspx"
            page.goto(iskur_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            page.locator("text=Kamu").first.click(force=True)
            page.wait_for_timeout(1500)

            ara_btn = page.locator("input[value='Ara'], #btnAra, a:has-text('Ara')").first
            if ara_btn.is_visible(timeout=3000):
                ara_btn.click(force=True)
                page.wait_for_timeout(6000)

            govde = page.inner_text("body")
            satirlar = [s.strip() for s in govde.split("\n") if len(s.strip()) > 25]
            ornek_satir = satirlar[-1] if satirlar else "Satır okunamadı"
            telegram_gonder(f"🏛️ [TEST] İŞKUR bağlantısı başarılı! Okunan örnek veri:\n{ornek_satir[:250]}\n🔗 {iskur_url}")
        except Exception as e:
            telegram_gonder(f"⚠️ [TEST] İŞKUR hata verdi: {e}")

        browser.close()

if __name__ == "__main__":
    siteleri_tara()
