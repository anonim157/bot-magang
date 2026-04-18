import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

# ================= KONFIGURASI TELEGRAM =================
BOT_TOKEN = "8621758636:AAE_a_ZSCMFkUj4jtbkYmrmyX5ZaeV01zrc"
CHAT_ID = "5492251531"

POSISI_MAGANG = ["Magang Engineer", "Magang Teknik Elektro", "Internship Automation"]
# ========================================================

def cari_magang_duckduckgo(kata_kunci):
    # Menggunakan Mesin Pencari DuckDuckGo yang jauh lebih ramah bot
    query = f'{kata_kunci} (site:linkedin.com/jobs OR site:glints.com/id OR site:instagram.com)'
    url = "https://html.duckduckgo.com/html/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://duckduckgo.com/"
    }
    
    try:
        # DuckDuckGo HTML version menggunakan POST request
        response = requests.post(url, data={'q': query}, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hasil = []
        semua_link = soup.find_all('a', href=True)
        
        # Debugging untuk melihat apakah DDG merespons dengan baik
        print(f"   [Debug] Mesin pencari memberikan {len(semua_link)} mentahan link.")

        for a in semua_link:
            link = a['href']
            
            # Membersihkan format link redirect dari DuckDuckGo
            if "uddg=" in link:
                link = link.split("uddg=")[1].split("&")[0]
                link = urllib.parse.unquote(link)
            
            # Filter hanya link target
            if "linkedin.com/jobs" in link or "glints.com/id" in link or "instagram.com" in link:
                
                # Mengambil judul. Pada DDG, judul biasanya ada di class result__snippet atau teks link itu sendiri
                judul = a.text.strip()
                
                # Jika judul dari link kosong, cari teks dari elemen pembungkusnya
                if not judul or len(judul) < 10:
                    parent = a.find_parent('div')
                    if parent:
                        judul = parent.text.strip()

                judul = " ".join(judul.split())
                
                # Menyingkirkan kata-kata navigasi
                kata_sampah = ["Login", "Sign in", "Instagram", "LinkedIn", "Masuk", "Lupa Kata Sandi"]
                is_sampah = any(sampah.lower() == judul.lower() for sampah in kata_sampah)
                
                if len(judul) > 10 and not any(link in h for h in hasil) and not is_sampah:
                    if "instagram.com" in link:
                        ikon = "📸"
                        sumber = "[Instagram]"
                    else:
                        ikon = "📌"
                        sumber = "[Job Portal]"
                        
                    hasil.append(f"{ikon} {sumber} {judul}\n🔗 {link}")
                    
                    if len(hasil) >= 4: 
                        break
                        
        return "\n\n".join(hasil) if hasil else "🔍 Tidak menemukan struktur link magang hari ini."
    except Exception as e:
        return f"Gagal mengambil data: {e}"

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": pesan,
        "disable_web_page_preview": True 
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Sukses! Notifikasi Telegram berhasil dikirim.")
        else:
            print(f"❌ Gagal mengirim pesan. Error: {response.text}")
    except Exception as e:
        print(f"⚠️ Terjadi kesalahan koneksi saat mengirim ke Telegram: {e}")

if __name__ == "__main__":
    print("Memulai program pencarian magang dengan DuckDuckGo...")
    pesan_akhir = "🚀 *UPDATE INFO MAGANG HARI INI* 🚀\n\n"
    
    for posisi in POSISI_MAGANG:
        print(f"Menganalisis data untuk: {posisi}...")
        data = cari_magang_duckduckgo(posisi)
        pesan_akhir += f"=== *{posisi}* ===\n{data}\n\n"
        time.sleep(random.randint(3, 5)) 
        
    pesan_akhir += "#IIZZZINNNNNNN🤖"
    
    print("Mempersiapkan pengiriman ke HP kamu...")
    kirim_telegram(pesan_akhir)
    print("Program selesai dieksekusi!")
