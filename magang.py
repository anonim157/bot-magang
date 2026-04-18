import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

# ================= KONFIGURASI TELEGRAM =================
BOT_TOKEN = "8621758636:AAE_a_ZSCMFkUj4jtbkYmrmyX5ZaeV01zrc"
CHAT_ID = "5492251531"

# Kata kunci yang lebih spesifik untuk Automation Engineer Undip/Semarang style
POSISI_MAGANG = ["Magang Automation Engineer", "Magang Electrical Engineer", "Internship Engineering"]
# ========================================================

def cari_magang_duckduckgo(kata_kunci):
    # Filter pencarian lebih tajam
    query = f'{kata_kunci} (site:linkedin.com/jobs OR site:glints.com/id OR site:instagram.com)'
    url = "https://html.duckduckgo.com/html/"
    
    # Gunakan User-Agent yang lebih modern
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://duckduckgo.com/",
        "Origin": "https://duckduckgo.com"
    }
    
    try:
        # Kirim request dengan timeout agar tidak gantung
        response = requests.post(url, data={'q': query}, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hasil = []
        # DuckDuckGo HTML menyimpan hasil dalam div class 'result'
        blocks = soup.find_all('div', class_='result')
        
        print(f"   [Debug] Menemukan {len(blocks)} blok hasil pencarian.")

        for block in blocks:
            tag_a = block.find('a', class_='result__a', href=True)
            if not tag_a:
                continue

            link = tag_a['href']
            
            # Bersihkan Redirect DuckDuckGo
            if "uddg=" in link:
                link = link.split("uddg=")[1].split("&")[0]
                link = urllib.parse.unquote(link)
            
            # Filter Target
            if any(site in link for site in ["linkedin.com/jobs", "glints.com", "instagram.com"]):
                judul = tag_a.get_text().strip()
                
                # Filter sampah navigasi
                kata_sampah = ["Login", "Sign in", "Instagram", "LinkedIn", "Masuk"]
                if any(s.lower() in judul.lower() for s in kata_sampah):
                    continue
                
                if len(judul) > 10:
                    ikon = "📸" if "instagram.com" in link else "📌"
                    sumber = "[Instagram]" if "instagram.com" in link else "[Job Portal]"
                    
                    data_teks = f"{ikon} {sumber} {judul}\n🔗 {link}"
                    
                    if data_teks not in hasil:
                        hasil.append(data_teks)
                    
                    if len(hasil) >= 3: # Ambil 3 terbaik saja per posisi
                        break
                        
        return "\n\n".join(hasil) if hasil else "🔍 Belum ada info baru di sumber ini."
    except Exception as e:
        return f"⚠️ Gangguan koneksi: {str(e)[:50]}"

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": pesan,
        "disable_web_page_preview": True,
        "parse_mode": "Markdown" # Agar teks *bold* berfungsi
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Notifikasi terkirim ke Telegram.")
        else:
            print(f"❌ Telegram Error: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Gagal kirim: {e}")

if __name__ == "__main__":
    print("🤖 Bot Magang Dicky sedang bekerja...")
    pesan_akhir = "🚀 *UPDATE INFO MAGANG HARI INI* 🚀\n\n"
    
    for posisi in POSISI_MAGANG:
        print(f"Mencari: {posisi}...")
        data = cari_magang_duckduckgo(posisi)
        pesan_akhir += f"=== *{posisi}* ===\n{data}\n\n"
        # Delay acak agar tidak dicurigai sebagai bot jahat
        time.sleep(random.randint(4, 7)) 
        
    pesan_akhir += "#IIZZZINNNNNNN🤖"
    
    kirim_telegram(pesan_akhir)
    print("✨ Selesai!")
