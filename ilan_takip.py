import os
import re
import json
import hashlib
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ISKUR_TELEGRAM_TOKEN = os.environ["ISKUR_TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
KAYIT_DOSYASI = "gorulen_ilanlar.json"

ANAHTAR_KELIMELER = [
    r"\bsivas\b",
    r"\bkoruma ve güvenlik\b",
    r"\bgüvenlik\b",
    r"\bdiyaliz\b",
    r"\btemizlik görevlisi\b",
    r"\btemizlik\b",
    r"\bşoför\b",
    r"\bişçi\b",
    r"\bbakım\b",
    r"\bonarım\b",
    r"\bpersonel alım\w*\b",
    r"\bmemur alım\w*\b",
]

YASAKLI_KELIMELER = [
    "işçilik",
    "yedek parça",
    "yapım işi",
    "mal alımı",
    "kiralama",
    "ihale",
]

def kayitlari_yukle():
    if os.path.exists(KAYIT_DOSYASI):
        with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def kayitlari_kaydet(kayitlar):
    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(list(kayitlar), f, ensure_ascii=False, indent=2)

def telegram_gonder(mesaj, token=TELEGRAM_TOKEN):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
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

        # 1. İLAN.GOV.TR (MEVCUT BOT)
        try:
            ilan_url = "https://www.ilan.gov.tr/ilan/kategori/9/memur-alim-ilanlari"
            page.goto(ilan_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            govde = page.inner_text("body")
            satirlar = [s.strip() for s in govde.split("\n") if 15 <= len(s.strip()) <= 300]
            for metin in satirlar:
                k_metin = kucult(metin)
                if any(y in k_metin for y in YASAKLI_KELIMELER):
                    continue

                eslesenler = [k.replace(r"\b", "").replace(r"\w*", "") for k in ANAHTAR_KELIMELER if re.search(k, k_metin)]
                if eslesenler:
                    ilan_imzasi = hashlib.md5(f"ILANGOV:{metin}".encode("utf-8")).hexdigest()
                    if ilan_imzasi not in gorulenler:
                        gorulenler.add(ilan_imzasi)
                        yeni_bulunan = True
                        etiketler = ", ".join(dict.fromkeys(k.upper() for k in eslesenler))
                        mesaj = (
                            f"📢 YENİ KAMU İLANI (ilan.gov.tr)\n"
                            f"🔎 Eşleşme: {etiketler}\n"
                            f"📄 İlan: {metin}\n"
                            f"🔗 Link: {ilan_url}"
                        )
                        telegram_gonder(mesaj, token=TELEGRAM_TOKEN)
        except Exception as e:
            print(f"ilan.gov.tr hatası: {e}")

        # 2. İŞKUR KAMU AÇIK İŞ İLANLARI (YENİ AYRI BOT)
        try:
            iskur_url = "
