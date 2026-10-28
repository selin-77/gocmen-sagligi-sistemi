import time
import psycopg2

print("Baseline (Güvenliksiz/Klasik) Performans Testi Başlatılıyor...")


print("Python dosyası çalışıyor!")

try:
    # 1. PostgreSQL Veritabanı Bağlantısı 
    # (Kendi veritabanı adını ve şifreni buraya yazmalısın)
    connection = psycopg2.connect(
        host="localhost",
        database="gocmen_sagligi_db", # Kendi açtığın veritabanı adı
        user="postgres",             # PostgreSQL kullanıcı adın
        password="seliN2004",         # PostgreSQL şifren
        port="5432"
    )
    cursor = connection.cursor()

    # 2. Başlangıç zamanını kaydet
    baslangic_zamani = time.time()

    # 3. patients tablosu üzerinden güvenlik filtresi olmaksızın test sorgusu
    cursor.execute("SELECT COUNT(*), AVG(EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM birth_date)) FROM patients;")
    sonuc = cursor.fetchone()

    # 4. Bitiş zamanını kaydet
    bitis_zamani = time.time()
    gecen_sure = (bitis_zamani - baslangic_zamani) * 1000 # Milisaniyeye çevir

    print(f"\n--- BASELINE TEST SONUÇLARI ---")
    print(f"Toplam Hasta Kayıt Sayısı: {sonuc[0]}")
    print(f"Hesaplanan Ortalama Yaş: {round(sonuc[1] if sonuc[1] else 0, 2)}")
    print(f"Sorgu Yanıt Süresi (Baseline): {gecen_sure:.2f} ms")

except Exception as error:
    print(f"Test sırasında hata oluştu: {error}")

finally:
    if 'connection' in locals() and connection:
        cursor.close()
        connection.close()
        print("Veritabanı bağlantısı kapatıldı.")