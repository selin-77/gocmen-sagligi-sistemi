import os
import psycopg2

print(
    "Veritabanı şeması ve tabloları mevcut yapıyla çakışmadan kontrol"
    " ediliyor..."
)

try:
  # Diğer dosyalarımızla tam tutarlı çevre değişkeni tabanlı parola güvenliği
  db_password = os.getenv("DB_PASSWORD", "")

  connection = psycopg2.connect(
      host="localhost",
      database="gocmen_sagligi_db",
      user="postgres",
      password=db_password,
      port="5432",
  )
  connection.autocommit = True
  cursor = connection.cursor()

  # 1. PostGIS Uzantısı
  cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
  print("PostGIS eklentisi kontrol edildi.")

  # 2. Patients Tablosu (Şevval'in şemasıyla birebir uyumlu)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            passport_number VARCHAR(50),
            nationality VARCHAR(50),
            birth_date DATE,
            gender VARCHAR(10),
            phone VARCHAR(20)
        );
    """)
  print("Patients tablosu hazır.")

  # 3. Health Records Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            record_id SERIAL PRIMARY KEY,
            patient_id INT REFERENCES patients(patient_id),
            disease_name VARCHAR(100),
            chronic_disease BOOLEAN,
            vaccination_status VARCHAR(50),
            risk_score INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
  print("Health Records tablosu hazır.")

  # 4. Locations Tablosu (PostGIS GEOMETRY desteğiyle)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            location_id SERIAL PRIMARY KEY,
            patient_id INT REFERENCES patients(patient_id),
            border_name VARCHAR(100),
            entry_time TIMESTAMP,
            geom GEOMETRY(Point, 4326)
        );
    """)
  print("Locations tablosu hazır.")

  print(
      "\nBAŞARILI: Tüm veritabanı şeması ve tabloları güvenli bir şekilde"
      " oluşturuldu/doğrulandı!"
  )

  cursor.close()
  connection.close()

except Exception as error:
  print(f"Veritabanı kurulumu sırasında hata oluştu: {error}")