import psycopg2

print("Veritabanı performans indeksleri ekleniyor...")

try:
    connection = psycopg2.connect(
        host="localhost",
        database="gocmen_sagligi_db",
        user="postgres",
        password="",
        port="5432"
    )
    connection.autocommit = True
    cursor = connection.cursor()

    # Performans için kritik indeksler
    index_komutlari = [
        "CREATE INDEX IF NOT EXISTS idx_health_patient_id ON health_records(patient_id);",
        "CREATE INDEX IF NOT EXISTS idx_health_disease ON health_records(disease_name);",
        "CREATE INDEX IF NOT EXISTS idx_locations_patient_id ON locations(patient_id);",
        # PostGIS coğrafi alan hızı için GIST indeks (Çok önemlidir!)
        "CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST (geom);"
    ]

    for komut in index_komutlari:
        print(f"Çalıştırılıyor: {komut}")
        cursor.execute(komut)

    print("\nBAŞARILI: Tüm indeksler (GIST dahil) başarıyla oluşturuldu!")

    cursor.close()
    connection.close()

except Exception as error:
    print(f"İndeks ekleme sırasında hata oluştu: {error}")