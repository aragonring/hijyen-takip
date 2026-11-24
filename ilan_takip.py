import os
import json
import hashlib
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
KAYIT_DOSYASI = "gorulen_ilanlar.json"

ANAHTAR_KELIMELER = [
    "sivas",
    "koruma ve güvenlik",
    "güvenlik",
    "diyaliz",
    "temizlik görevlisi",
    "temizlik",
    "şoför",
    "işçi",
]

SITELER = [
    {"ad": "Kamu İlan (SBB)", "url": "https://kamuilan.sbb.gov.tr"},
    {"ad": "Kariyer Kapısı", "url": "https://kariyerkapisi.gov.tr/isealim"},
    {"ad": "Yerel Yönetimler (ÇŞB)", "url": "https://yerelyonetimler.csb.gov.tr"},
    {"ad": "ilan.gov.tr", "url": "https://www.ilan.gov.tr/ilan/kategori/9/memur-alim-ilanlari"},
]

def kayitlari_yukle():
    if os.path.exists(KAYIT_DOSYASI):
        with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def kayitlari_kaydet(kayitlar):
    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(list(kayitlar), f, ensure_ascii=False, indent=2)

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj, "disable_web_page_preview": True}
    requests.post(url, data=data, timeout=20)

def kucult(metin):
    return metin.replace("İ", "i").replace("I", "ı").lower()

def siteleri_tara():
    gorulenler = kayitlari_yukle()
    yeni_bulunan = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1. DİĞER 4 KAMU PORTALI (TÜRKİYE GENELİ)
        for site in SITELER:
            try:
                page.goto(site["url"], timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)

                ogeler = page.locator("a, tr").all()
                for oge in ogeler:
                    try:
                        metin = " ".join(oge.inner_text().split())
                        if len(metin) < 12 or len(metin) > 350:
                            continue

                        k_metin = kucult(metin)
                        eslesenler = [k for k in ANAHTAR_KELIMELER if k in k_metin]

                        if eslesenler:
                            ilan_imzasi = hashlib.md5(f"{site['ad']}:{metin}".encode("utf-8")).hexdigest()
                            if ilan_imzasi not in gorulenler:
                                gorulenler.add(ilan_imzasi)
                                yeni_bulunan = True
                                etiketler = ", ".join(k.upper() for k in eslesenler)
                                mesaj = (
                                    f"📢 YENİ İLAN ({site['ad']})\n"
                                    f"🔎 Eşleşme: {etiketler}\n"
                                    f"📄 İlan: {metin}\n"
                                    f"🔗 Link: {site['url']}"
                                )
                                telegram_gonder(mesaj)
                    except Exception:
                        continue
            except Exception as e:
                print(f"{site['ad']} hatası: {e}")

        # 2. İŞKUR KAMU İLANLARI (TÜRKİYE GENELİ)
        try:
            iskur_url = "https://esube.iskur.gov.tr/istihdam/AcikisilanAra.aspx"
            page.goto(iskur_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # İşyeri Türü: Kamu seçimi
            kamu_radio = page.locator("label:has-text('Kamu'), input[value*='Kamu']").first
            if kamu_radio.is_visible(timeout=3000):
                kamu_radio.click()
                page.wait_for_timeout(1500)

            # Ara butonuna bas (İl/İlçe boş bırakılarak Türkiye geneli taranır)
            ara_btn = page.locator("input[type='submit'][value*='Ara'], button:has-text('Ara')").first
            if ara_btn.is_visible(timeout=3000):
                ara_btn.click()
                page.wait_for_timeout(4000)

            satirlar = page.locator("table tr").all()
            for satir in satirlar:
                try:
                    metin = " ".join(satir.inner_text().split())
                    if len(metin) < 15 or "İlan No" in metin or "Kayıt bulunamadı" in metin:
                        continue

                    k_metin = kucult(metin)
                    eslesenler = [k for k in ANAHTAR_KELIMELER if k in k_metin]

                    if eslesenler:
                        ilan_imzasi = hashlib.md5(f"ISKUR:{metin}".encode("utf-8")).hexdigest()
                        if ilan_imzasi not in gorulenler:
                            gorulenler.add(ilan_imzasi)
                            yeni_bulunan = True
                            etiketler = ", ".join(k.upper() for k in eslesenler)
                            mesaj = (
                                f"🏛️ YENİ İŞKUR KAMU İLANI (TÜRKİYE GENELİ)\n"
                                f"🔎 Eşleşme: {etiketler}\n"
                                f"📄 Detay: {metin}\n"
                                f"🔗 Link: {iskur_url}"
                            )
                            telegram_gonder(mesaj)
                except Exception:
                    continue
        except Exception as e:
            print(f"İŞKUR tarama hatası: {e}")

        browser.close()

    if yeni_bulunan:
        kayitlari_kaydet(gorulenler)

if __name__ == "__main__":
    siteleri_tara()
