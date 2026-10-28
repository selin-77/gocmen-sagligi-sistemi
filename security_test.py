import os
import psycopg2

print("=== GÖÇMEN SAĞLIĞI SİSTEMİ - ŞEVVAL'İN RLS VE ROL TESTİ ===")

toplam_test_sayisi = 0
basari_sayisi = 0

try:
  db_password = os.getenv("DB_PASSWORD", "")

  # Ana bağlantı (Admin yetkisiyle bağlanıp SET ROLE testi yapacağız)
  conn = psycopg2.connect(
      host="localhost",
      database="gocmen_sagligi_db",
      user="postgres",
      password=db_password,
      port="5432",
  )
  cursor = conn.cursor()

  # 1. TEST: Unauthorized Role (Yetkisiz Rol) Testi
  print("\n[Test 1] unauthorized_role ile hassas verilere erişim deneniyor...")
  toplam_test_sayisi += 1
  try:
    cursor.execute("SET ROLE unauthorized_role;")
    cursor.execute("SELECT COUNT(*) FROM health_records;")
    print("UYARI: Yetkisiz rol veriye erişebildi!")
    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(
        "BAŞARILI: Yetkisiz rolün erişimi engellendi! Hata kodu:"
        f" {getattr(e, 'pgcode', 'Bilinmiyor')}"
    )
    basari_sayisi += 1
    conn.rollback()  # Hata alan transaction'ı sıfırla
    cursor.execute("RESET ROLE;")

  # 2. TEST: Doctor Role (Doktor Rolü) Testi
  print("\n[Test 2] doctor_role ile sağlık kayıtlarına erişim test ediliyor...")
  toplam_test_sayisi += 1
  try:
    cursor.execute("SET ROLE doctor_role;")
    cursor.execute("SELECT COUNT(*) FROM health_records;")
    res = cursor.fetchone()[0]
    print(f"BAŞARILI: Doktor rolü verileri okudu (Kayıt sayısı: {res}).")
    basari_sayisi += 1
    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(f"HATA: Doktor rolü erişemedi: {e}")
    conn.rollback()
    cursor.execute("RESET ROLE;")

  # 3. TEST: Analyst Role (Analist Rolü - Maskelenmiş Görünüm) Testi
  print(
      "\n[Test 3] analyst_role ile anonymized_patients görünümü test ediliyor..."
  )
  toplam_test_sayisi += 1
  try:
    cursor.execute("SET ROLE analyst_role;")
    cursor.execute("SELECT COUNT(*) FROM anonymized_patients;")
    res = cursor.fetchone()[0]
    print(
        "BAŞARILI: Analist maskelenmiş görünüme erişti (Kayıt sayısı: {res})."
    )
    basari_sayisi += 1
    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(f"HATA: Analist rolü görünümde hata aldı: {e}")
    conn.rollback()
    cursor.execute("RESET ROLE;")

  cursor.close()
  conn.close()

  # --- METRİK RAPORU ---
  print("\n" + "=" * 50)
  print("GÜVENLİK VE RLS TEST RAPORU")
  print("=" * 50)
  print(f"Toplam Test Senaryosu : {toplam_test_sayisi}")
  print(f"Başarılı Doğrulama    : {basari_sayisi}")

  basari_orani = (basari_sayisi / toplam_test_sayisi) * 100
  print(f"Erişim Yetkilendirme Başarı Oranı : %{basari_orani:.2f}")
  print("=" * 50)

except Exception as error:
  print(f"Kritik hata oluştu: {error}")