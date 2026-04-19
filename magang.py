import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import logging
import json
import os
from datetime import datetime

# ===================== KONFIGURASI =====================
BOT_TOKEN = "8621758636:AAE_a_ZSCMFkUj4jtbkYmrmyX5ZaeV01zrc"
CHAT_ID = "5492251531"

POSISI_MAGANG = [
    "Magang Automation Engineer",
    "Magang Electrical Engineer",
    "Internship Engineering",
]

SUMBER_FILTER = ["linkedin.com/jobs", "glints.com", "instagram.com"]
KATA_SAMPAH   = ["login", "sign in", "masuk", "daftar", "register"]
MAX_HASIL_PER_POSISI = 3

FILE_RIWAYAT = "riwayat_lowongan.json"
# =======================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_magang.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ─────────────────── Riwayat (duplikat checker) ───────────────────

def muat_riwayat() -> set:
    """Muat URL yang sudah pernah dikirim agar tidak duplikat."""
    if not os.path.exists(FILE_RIWAYAT):
        return set()
    try:
        with open(FILE_RIWAYAT, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, IOError):
        return set()


def simpan_riwayat(riwayat: set) -> None:
    with open(FILE_RIWAYAT, "w", encoding="utf-8") as f:
        json.dump(list(riwayat), f, ensure_ascii=False, indent=2)


# ─────────────────── Scraper DuckDuckGo ───────────────────

HEADERS_POOL = [
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Referer": "https://duckduckgo.com/",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Safari/605.1.15"
        ),
        "Referer": "https://duckduckgo.com/",
        "Accept-Language": "id-ID,id;q=0.9",
    },
]


def bersihkan_link(raw: str) -> str:
    """Ekstrak URL bersih dari redirect DuckDuckGo."""
    if "uddg=" in raw:
        raw = raw.split("uddg=")[1].split("&")[0]
    return urllib.parse.unquote(raw)


def cari_magang_duckduckgo(kata_kunci: str, riwayat: set) -> list[dict]:
    """
    Cari lowongan di DuckDuckGo dan kembalikan list dict
    {judul, link, sumber, ikon} yang belum ada di riwayat.
    """
    query = (
        f'{kata_kunci} (site:linkedin.com/jobs OR site:glints.com/id OR site:instagram.com)'
        " magang 2024 OR 2025"
    )
    url = "https://html.duckduckgo.com/html/"
    headers = random.choice(HEADERS_POOL)

    try:
        resp = requests.post(
            url,
            data={"q": query},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning(f"Gagal fetch DuckDuckGo: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    blocks = soup.find_all("div", class_="result")
    log.debug(f"  [{kata_kunci}] Ditemukan {len(blocks)} blok hasil.")

    hasil = []
    for block in blocks:
        tag_a = block.find("a", class_="result__a", href=True)
        if not tag_a:
            continue

        link = bersihkan_link(tag_a["href"])

        # Hanya sumber yang relevan
        if not any(s in link for s in SUMBER_FILTER):
            continue

        judul = tag_a.get_text(separator=" ").strip()

        # Buang navigasi / sampah
        if any(s in judul.lower() for s in KATA_SAMPAH) or len(judul) <= 10:
            continue

        # Skip duplikat
        if link in riwayat:
            log.debug(f"  Skip duplikat: {link}")
            continue

        is_ig = "instagram.com" in link
        entry = {
            "judul": judul,
            "link": link,
            "sumber": "Instagram" if is_ig else "Job Portal",
            "ikon": "📸" if is_ig else "📌",
        }

        hasil.append(entry)
        if len(hasil) >= MAX_HASIL_PER_POSISI:
            break

    return hasil


# ─────────────────── Formatter Pesan ───────────────────

def format_pesan(semua_hasil: dict[str, list[dict]]) -> str:
    tanggal = datetime.now().strftime("%d %b %Y %H:%M")
    baris = [f"🤖 *UPDATE MAGANG — {tanggal}*\n"]

    ada_hasil = False
    for posisi, items in semua_hasil.items():
        baris.append(f"━━━ *{posisi}* ━━━")
        if not items:
            baris.append("🔍 Belum ada lowongan baru saat ini.\n")
            continue

        ada_hasil = True
        for item in items:
            baris.append(
                f"{item['ikon']} [{item['sumber']}] {item['judul']}\n"
                f"🔗 {item['link']}"
            )
        baris.append("")  # spasi antar posisi

    if not ada_hasil:
        baris.append("Semua lowongan sudah pernah dikirim sebelumnya.")

    baris.append("#MagangDicky 🤖")
    return "\n".join(baris)


# ─────────────────── Pengirim Telegram ───────────────────

def kirim_telegram(pesan: str) -> bool:
    """Kirim pesan ke Telegram; kembalikan True jika sukses."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": pesan,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    # Telegram batasi panjang pesan 4096 karakter
    if len(pesan) > 4000:
        pesan = pesan[:3990] + "\n…(terpotong)"
        payload["text"] = pesan

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            log.info("✅ Notifikasi terkirim ke Telegram.")
            return True
        else:
            log.error(f"Telegram API error: {data}")
            return False
    except requests.RequestException as e:
        log.error(f"Gagal kirim ke Telegram: {e}")
        return False


# ─────────────────── Main ───────────────────

def main() -> None:
    log.info("🤖 Bot Magang Dicky mulai bekerja...")

    riwayat = muat_riwayat()
    log.info(f"Riwayat dimuat: {len(riwayat)} URL tersimpan.")

    semua_hasil: dict[str, list[dict]] = {}
    link_baru: list[str] = []

    for posisi in POSISI_MAGANG:
        log.info(f"Mencari: {posisi}...")
        hasil = cari_magang_duckduckgo(posisi, riwayat)
        semua_hasil[posisi] = hasil

        for item in hasil:
            link_baru.append(item["link"])
            log.info(f"  ✔ {item['judul'][:60]}")

        delay = random.uniform(4.0, 8.0)
        log.debug(f"  Menunggu {delay:.1f}s sebelum query berikutnya...")
        time.sleep(delay)

    pesan = format_pesan(semua_hasil)
    sukses = kirim_telegram(pesan)

    if sukses and link_baru:
        riwayat.update(link_baru)
        simpan_riwayat(riwayat)
        log.info(f"Riwayat diperbarui: +{len(link_baru)} URL baru.")

    log.info("✨ Selesai!")


if __name__ == "__main__":
    main()
