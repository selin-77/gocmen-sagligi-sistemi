from datetime import datetime, timedelta
import os
import random
import psycopg2

print("Sentetik veri üretimi ve veritabanına aktarımı başlatılıyor...")

CLEAR_EXISTING_DATA = False

try:
  db_password = os.getenv("DB_PASSWORD", "")

  connection = psycopg2.connect(
      host="localhost",
      database="gocmen_sagligi_db",
      user="postgres",
      password=db_password,
      port="5432",
  )
  connection.autocommit = False
  cursor = connection.cursor()

  if CLEAR_EXISTING_DATA:
    cursor.execute(
        "TRUNCATE TABLE health_records, locations, patients RESTART IDENTITY"
        " CASCADE;"
    )
    print(
        "UYARI: CLEAR_EXISTING_DATA aktif olduğu için eski veriler temizlendi."
    )
  else:
    print(
        "Mevcut veriler korunuyor; yeni veriler güvenli akışla işleniyor."
    )

  toplam_kayit = 20000

  base_lat = 39.6484
  base_lon = 27.8826

  isimler = [
      "Ali",
      "Fatma",
      "Mehmet",
      "Aisha",
      "Omar",
      "Zainab",
      "Youssef",
      "Leyla",
      "Ahmed",
      "Meryem",
  ]
  soyisimler = [
      "Yılmaz",
      "Demir",
      "Al-Hassan",
      "Kaya",
      "Chechen",
      "Çelik",
      "El-Amin",
      "Şahin",
  ]
  cinsiyetler = ["E", "K"]
  uyruklar = ["Suriye", "Afganistan", "Irak", "Filistin", "Ukrayna"]
  hastaliklar = [
      "Hipertansiyon",
      "Diyabet",
      "Astım",
      "Grip",
      "Sağlıklı",
      "Bronşit",
  ]
  as_durumlari = ["Tam Aşılı", "Eksik Aşılı", "Aşısız"]
  sinirlere_gore_kapilar = [
      "Kapıkule",
      "Hamzabeyli",
      "Öncüpınar",
      "Yayladağı",
      "Derecik",
  ]

  print(
      "Hastalar üretiliyor ve veritabanına eklenip gerçek ID'leri alınıyor..."
  )

  # 1. Adım: Hastaları ekleyip RETURNING patient_id ile gerçek veritabanı ID'lerini topluyoruz
  uretilen_patient_id_listesi = []

  for _ in range(toplam_kayit):
    ad = random.choice(isimler)
    soyad = random.choice(soyisimler)
    passport = f"U{random.randint(1000000, 9999999)}"
    uyruk = random.choice(uyruklar)
    dogum_tarihi = datetime(1960, 1, 1) + timedelta(
        days=random.randint(0, 18000)
    )
    cinsiyet = random.choice(cinsiyetler)
    telefon = f"05{random.randint(100, 999)}{random.randint(1000000, 9999999)}"

    cursor.execute(
        """
            INSERT INTO patients (first_name, last_name, passport_number, nationality, birth_date, gender, phone) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            RETURNING patient_id;
        """,
        (ad, soyad, passport, uyruk, dogum_tarihi.date(), cinsiyet, telefon),
    )

    # Veritabanının atadığı gerçek ID'yi alıp listeye atıyoruz
    gercek_id = cursor.fetchone()[0]
    uretilen_patient_id_listesi.append(gercek_id)

  print(
      "Lokasyonlar ve sağlık kayıtları, alınan gerçek patient_id'lerle"
      " ilişkilendiriliyor..."
  )

  # 2. Adım: Alınan gerçek ID'leri kullanarak locations ve health_records kayıtlarını oluşturalım
  for p_id in uretilen_patient_id_listesi:
    # Lokasyon verisi
    lat = base_lat + random.uniform(-0.1, 0.1)
    lon = base_lon + random.uniform(-0.1, 0.1)
    geom_point = f"POINT({lon} {lat})"
    border = random.choice(sinirlere_gore_kapilar)
    entry_time = datetime(2026, 1, 1) + timedelta(
        days=random.randint(0, 250)
    )

    cursor.execute(
        """
            INSERT INTO locations (patient_id, border_name, entry_time, geom) 
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326));
        """,
        (p_id, border, entry_time, geom_point),
    )

    # Sağlık kaydı verisi
    disease = random.choice(hastaliklar)
    chronic = True if disease in ["Hipertansiyon", "Diyabet", "Astım"] else False
    vaccination = random.choice(as_durumlari)
    risk = random.randint(1, 10) if chronic else random.randint(1, 3)

    cursor.execute(
        """
            INSERT INTO health_records (patient_id, disease_name, chronic_disease, vaccination_status, risk_score) 
            VALUES (%s, %s, %s, %s, %s);
        """,
        (p_id, disease, chronic, vaccination, risk),
    )

  # Her şey yolunda gittiyse kalıcı olarak işle
  connection.commit()
  print(
      f"\nBAŞARILI: {toplam_kayit} hasta, lokasyon ve sağlık kaydı gerçek"
      " ID'leriyle güvenle eşleştirilip yüklendi!"
  )

except Exception as error:
  if "connection" in locals() and connection:
    connection.rollback()
  print(f"Hata oluştu, işlem geri alındı: {error}")

finally:
  if "connection" in locals() and connection:
    cursor.close()
    connection.close()