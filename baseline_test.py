from datetime import datetime
import os
import time
import psycopg2

print("Baseline (Güvenliksiz/Klasik) Performans Testi Başlatılıyor...")

try:
  # Çevre değişkeninden parola okuma güvenliği
  db_password = os.getenv("DB_PASSWORD", "")

  connection = psycopg2.connect(
      host="localhost",
      database="gocmen_sagligi_db",
      user="postgres",
      password=db_password,
      port="5432",
  )
  cursor = connection.cursor()

  start_time = time.time()

  # Toplam hasta sayısı sorgusu
  cursor.execute("SELECT COUNT(*) FROM patients;")
  total_patients = cursor.fetchone()[0]

  # Ortalama doğum tarihinden yaş hesabı sorgusu
  cursor.execute(
      "SELECT AVG(EXTRACT(YEAR FROM AGE(birth_date))) FROM patients;"
  )
  avg_age = cursor.fetchone()[0]

  end_time = time.time()
  query_time_ms = (end_time - start_time) * 1000

  print("\n--- BASELINE TEST SONUÇLARI ---")
  print(f"Toplam Hasta Kayıt Sayısı: {total_patients}")
  print(f"Hesaplanan Ortalama Yaş: {round(avg_age, 2) if avg_age else 0}")
  print(f"Sorgu Yanıt Süresi (Baseline): {round(query_time_ms, 2)} ms")

  cursor.close()
  connection.close()
  print("Veritabanı bağlantısı kapatıldı.")

except Exception as error:
  print(f"Test sırasında hata oluştu: {error}")