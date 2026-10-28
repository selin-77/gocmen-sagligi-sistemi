from datetime import datetime, timedelta
import os
import random
import psycopg2

print("Suriyeli sığınmacı odaklı sentetik veri üretimi başlatılıyor...")

# Şevval'in uyarısı: Yanlışlıkla veri silinmesini önlemek için varsayılan kapalı
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
    print("UYARI: CLEAR_EXISTING_DATA aktif olduğu için eski veriler temizlendi.")
  else:
    print("Mevcut veriler korunuyor; yeni veriler güvenli akışla işleniyor.")

  toplam_kayit = 20000

  base_lat = 39.6484
  base_lon = 27.8826

  # Suriyeli mülteci profiline uygun isim, soyisim ve sınır kapıları havuzu
  isimler = [
      "Muhammed",
      "Ahmed",
      "Ali",
      "Omar",
      "Youssef",
      "İbrahim",
      "Fatima",
      "Aisha",
      "Zainab",
      "Meryem",
      "Halil",
      "Mahmoud",
  ]
  soyisimler = [
      "El-Hasan",
      "El-Ahmed",
      "Al-Khatib",
      "Al-Jassem",
      "El-Amin",
      "Demir",
      "Kaya",
      "Çelik",
  ]
  cinsiyetler = ["E", "K"]
  
  hastaliklar = [
      "Hipertansiyon",
      "Diyabet",
      "Astım",
      "Grip",
      "Sağlıklı",
      "Bronşit",
  ]
  as_durumlari = ["Tam Aşılı", "Eksik Aşılı", "Aşısız"]
  
  sinir_kapilari = [
      "Öncüpınar (Kilis)",
      "Cilvegözü (Hatay)",
      "Akçakale (Şanlıurfa)",
      "Yayladağı (Hatay)",
  ]

  print("Hastalar üretiliyor ve 99 ile başlayan Geçici Kimlik numaraları atanıyor...")

  uretilen_patient_id_listesi = []

  for _ in range(toplam_kayit):
    ad = random.choice(isimler)
    soyad = random.choice(soyisimler)
    
    # Türkiye'deki geçici koruma statüsüne uygun 99 ile başlayan 11 haneli yabancı kimlik no
    kimlik_no = f"99{random.randint(100000000, 999999999)}"
    
    uyruk = "Suriye"
    dogum_tarihi = datetime(1960, 1, 1) + timedelta(days=random.randint(0, 18000))
    cinsiyet = random.choice(cinsiyetler)
    telefon = f"05{random.randint(100, 999)}{random.randint(1000000, 9999999)}"

    cursor.execute(
        """
            INSERT INTO patients (first_name, last_name, passport_number, nationality, birth_date, gender, phone) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            RETURNING patient_id;
        """,
        (ad, soyad, kimlik_no, uyruk, dogum_tarihi.date(), cinsiyet, telefon),
    )

    gercek_id = cursor.fetchone()[0]
    uretilen_patient_id_listesi.append(gercek_id)

  print("Sınır kapısı lokasyonları ve sağlık kayıtları gerçek ID'lerle ilişkilendiriliyor...")

  for p_id in uretilen_patient_id_listesi:
    lat = base_lat + random.uniform(-0.1, 0.1)
    lon = base_lon + random.uniform(-0.1, 0.1)
    geom_point = f"POINT({lon} {lat})"
    border = random.choice(sinir_kapilari)
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

  connection.commit()
  print(
      f"\nBAŞARILI: {toplam_kayit} Suriyeli sığınmacı kaydı, sınır kapıları ve"
      " sağlık verileriyle veritabanına güvenle işlendi!"
  )

except Exception as error:
  if "connection" in locals() and connection:
    connection.rollback()
  print(f"Hata oluştu, işlem geri alındı: {error}")

finally:
  if "connection" in locals() and connection:
    cursor.close()
    connection.close()