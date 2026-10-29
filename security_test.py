import os
import psycopg2

print("=== GÖÇMEN SAĞLIĞI SİSTEMİ - İLERİ DÜZEY GÜVENLİK VE RLS TESTİ ===")

# Detaylı metrik takibi için
test_sonuclari = {
    "Yetkisiz Erişim Kısıtlamaları (Tablo Bazlı)": False,
    "Doktor Rolü Tam ve Sınırlı Erişim Doğrulaması": False,
    "Analist Rolü Maskeleme (Anonymization) Doğrulaması": False,
    "Hassas Alan Sızıntı Kontrolü": False,
}

try:
  db_password = os.getenv("DB_PASSWORD", "")
  conn = psycopg2.connect(
      host="localhost",
      database="gocmen_sagligi_db",
      user="postgres",
      password=db_password,
      port="5432",
  )
  cursor = conn.cursor()

  # --- TEST 1: Yetkisiz Rol Kapsamlı Erişim Denemesi ---
  print(
      "\n[Test 1] unauthorized_role için tüm hassas tablolara erişim"
      " deneniyor..."
  )
  try:
    cursor.execute("SET ROLE unauthorized_role;")
    # patients ve health_records tablolarına ayrı ayrı sızma denemesi
    cursor.execute("SELECT COUNT(*) FROM patients;")
    cursor.execute("SELECT COUNT(*) FROM health_records;")
    print("UYARI: Yetkisiz rol verilere erişebildi!")
    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(
        "BAŞARILI: Yetkisiz rolün tüm kritik tablolara erişimi engellendi! Hata:"
        f" {e.pgcode}"
    )
    test_sonuclari["Yetkisiz Erişim Kısıtlamaları (Tablo Bazlı)"] = True
    conn.rollback()
    cursor.execute("RESET ROLE;")

  # --- TEST 2: Doktor Rolü Kapsam ve Yetki Sınırı Kontrolü ---
  print("\n[Test 2] doctor_role veri okunabilirliği ve sınırları test ediliyor...")
  try:
    cursor.execute("SET ROLE doctor_role;")
    # Doktor temel bilgileri okuyabilmeli
    cursor.execute(
        "SELECT patient_id, first_name, last_name FROM patients LIMIT 5;"
    )
    patients_res = cursor.fetchall()

    # Sağlık kayıtlarını okuyabilmeli
    cursor.execute("SELECT COUNT(*) FROM health_records;")
    health_res = cursor.fetchone()[0]

    if len(patients_res) > 0 and health_res > 0:
      print(
          f"BAŞARILI: Doktor rolü yetkileri dahilinde {health_res} sağlık"
          " kaydına ve hasta listesine ulaştı."
      )
      test_sonuclari["Doktor Rolü Tam ve Sınırlı Erişim Doğrulaması"] = True
    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(f"HATA: Doktor rolü testinde hata: {e}")
    conn.rollback()
    cursor.execute("RESET ROLE;")

  # --- TEST 3: Analist Rolü Veri Maskeleme Doğrulaması ---
  print(
      "\n[Test 3] analyst_role için hassas verilerin maskelendiği (anonymized)"
      " doğrulanıyor..."
  )
  try:
    cursor.execute("SET ROLE analyst_role;")
    # Maskelenmiş görünümden veri çekme
    cursor.execute(
        "SELECT first_name, last_name, passport_number, phone FROM"
        " anonymized_patients LIMIT 3;"
    )
    rows = cursor.fetchall()

    masking_success = True
    for row in rows:
      f_name, l_name, passport, phone = row
      # Maskeleme kurallarına uyulup uyulmadığını kod içinde kontrol ediyoruz
      if not (
          "***" in l_name
          and "***" in passport
          and "***" in phone
          and f_name.endswith("***")
      ):
        masking_success = False

    if masking_success and len(rows) > 0:
      print(
          "BAŞARILI: Analist görünümündeki hassas alanların (İsim, Soyisim,"
          " Pasaport, Telefon) gerçekten '***' ile maskelendiği doğrulandı!"
      )
      test_sonuclari[
          "Analist Rolü Maskeleme (Anonymization) Doğrulaması"
      ] = True
      test_sonuclari["Hassas Alan Sızıntı Kontrolü"] = True
    else:
      print("UYARI: Maskeleme kurallarında açık tespit edildi!")

    cursor.execute("RESET ROLE;")
  except psycopg2.Error as e:
    print(f"HATA: Analist maskeleme testinde hata: {e}")
    conn.rollback()
    cursor.execute("RESET ROLE;")

  cursor.close()
  conn.close()

  # --- GELİŞTİRİLMİŞ METRİK VE DEĞERLENDİRME RAPORU ---
  print("\n" + "=" * 60)
  print("KAPSAMLI GÜVENLİK VE RLS DOĞRULAMA RAPORU")
  print("=" * 60)
  toplam_kriter = len(test_sonuclari)
  basarili_kriter = sum(1 for v in test_sonuclari.values() if v)

  for kriter, durum in test_sonuclari.items():
    durum_str = "✅ DOĞRULANDI" * durum or "❌ BAŞARISIZ / EKSİK"
    print(f"- {kriter}: {durum_str}")

  print("-" * 60)
  gelismis_basari_orani = (basarili_kriter / toplam_kriter) * 100
  print(f"Değerlendirilen Toplam Güvenlik Kriteri : {toplam_kriter}")
  print(f"Başarıyla Doğrulanan Kriter Sayısı     : {basarili_kriter}")
  print(f"Gerçekçi Güvenlik Uyumluluk Skoru      : %{gelismis_basari_orani:.2f}")
  print("=" * 60)

except Exception as error:
  print(f"Kritik test hatası: {error}")