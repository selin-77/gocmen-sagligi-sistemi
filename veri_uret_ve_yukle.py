import random
from datetime import datetime, timedelta
import psycopg2

print("Sentetik veri üretimi ve veritabanına aktarımı başlatılıyor...")

try:
    # 1. Veritabanı bağlantısı
    connection = psycopg2.connect(
        host="localhost",
        database="gocmen_sagligi_db",
        user="postgres",
        password="",
        port="5432"
    )
    connection.autocommit = True
    cursor = connection.cursor()

    # Eski verileri temizleyelim
    cursor.execute("TRUNCATE TABLE health_records, locations, patients RESTART IDENTITY CASCADE;")
    print("Eski veriler temizlendi, yeni sentetik veriler üretiliyor...")

    toplam_kayit = 20000

    patients_data = []
    locations_data = []
    health_records_data = []

    # Balıkesir civarı örnek koordinat sınırları
    base_lat = 39.6484
    base_lon = 27.8826

    isimler = ["Ali", "Fatma", "Mehmet", "Aisha", "Omar", "Zainab", "Youssef", "Leyla", "Ahmed", "Meryem"]
    soyisimler = ["Yılmaz", "Demir", "Al-Hassan", "Kaya", "Chechen", "Çelik", "El-Amin", "Şahin"]
    cinsiyetler = ["E", "K"]
    uyruklar = ["Suriye", "Afganistan", "Irak", "Filistin", "Ukrayna"]
    hastaliklar = ["Hipertansiyon", "Diyabet", "Astım", "Grip", "Sağlıklı", "Bronşit"]
    as_durumlari = ["Tam Aşılı", "Eksik Aşılı", "Aşısız"]
    sinirlere_gore_kapilar = ["Kapıkule", "Hamzabeyli", "Öncüpınar", "Yayladağı", "Derecik"]

    # 1. Hastalar (Patients) Verisi Üretimi
    for i in range(1, toplam_kayit + 1):
        ad = random.choice(isimler)
        soyad = random.choice(soyisimler)
        passport = f"U{random.randint(1000000, 9999999)}"
        uyruk = random.choice(uyruklar)
        dogum_tarihi = datetime(1960, 1, 1) + timedelta(days=random.randint(0, 18000))
        cinsiyet = random.choice(cinsiyetler)
        telefon = f"05{random.randint(100, 999)}{random.randint(1000000, 9999999)}"

        patients_data.append((ad, soyad, passport, uyruk, dogum_tarihi.date(), cinsiyet, telefon))

    print("Hastalar veritabanına yazılıyor...")
    args_str = ",".join(cursor.mogrify("(%s, %s, %s, %s, %s, %s, %s)", x).decode('utf-8') for x in patients_data)
    cursor.execute("INSERT INTO patients (first_name, last_name, passport_number, nationality, birth_date, gender, phone) VALUES " + args_str)

    # 2. Lokasyon ve Sağlık Kayıtları Üretimi
    print("Lokasyonlar ve sağlık kayıtları üretiliyor...")
    for i in range(1, toplam_kayit + 1):
        # Konum (PostGIS GEOMETRY)
        lat = base_lat + random.uniform(-0.1, 0.1)
        lon = base_lon + random.uniform(-0.1, 0.1)
        geom_point = f"POINT({lon} {lat})"
        border = random.choice(sinirlere_gore_kapilar)
        entry_time = datetime(2026, 1, 1) + timedelta(days=random.randint(0, 250))

        locations_data.append((i, border, entry_time, geom_point))

        # Sağlık Kaydı
        disease = random.choice(hastaliklar)
        chronic = True if disease in ["Hipertansiyon", "Diyabet", "Astım"] else False
        vaccination = random.choice(as_durumlari)
        risk = random.randint(1, 10) if chronic else random.randint(1, 3)

        health_records_data.append((i, disease, chronic, vaccination, risk))

    # Lokasyonları ekleyelim
    for patient_id, border, entry_time, point in locations_data:
        cursor.execute(
            "INSERT INTO locations (patient_id, border_name, entry_time, geom) VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))",
            (patient_id, border, entry_time, point)
        )

    # Sağlık kayıtlarını ekleyelim
    for record in health_records_data:
        cursor.execute(
            "INSERT INTO health_records (patient_id, disease_name, chronic_disease, vaccination_status, risk_score) VALUES (%s, %s, %s, %s, %s)",
            record
        )

    print(f"\nBAŞARILI: {toplam_kayit} adet sentetik hasta, lokasyon ve sağlık kaydı veritabanına başarıyla yüklendi!")

except Exception as error:
    print(f"Veri üretimi sırasında hata oluştu: {error}")

finally:
    if 'connection' in locals() and connection:
        cursor.close()
        connection.close()