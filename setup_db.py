import os
import psycopg2

print("Veritabanı kontrol ediliyor ve kuruluyor...")

try:
    # 1. Adım: Veritabanını kodla oluşturalım
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="",
        port="5432"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'gocmen_sagligi_db'")
    exists = cur.fetchone()
    if not exists:
        cur.execute("CREATE DATABASE gocmen_sagligi_db;")
        print("'gocmen_sagligi_db' veritabanı kodla otomatik olarak oluşturuldu!")
    else:
        print("'gocmen_sagligi_db' veritabanı zaten mevcut.")
    
    cur.close()
    conn.close()

    # 2. Adım: Proje içinde '01_create_tables.sql' dosyasını konum bağımsız otomatik bulalım
    sql_dosya_yolu = None
    for kok, dizinler, dosyalar in os.walk("."):
        if "01_create_tables.sql" in dosyalar:
            sql_dosya_yolu = os.path.join(kok, "01_create_tables.sql")
            break

    if sql_dosya_yolu:
        print(f"SQL dosyası bulundu: {sql_dosya_yolu}")
        
        # Yeni oluşturduğumuz veritabanına bağlanıp tabloları kuralım
        connection = psycopg2.connect(
            host="localhost",
            database="gocmen_sagligi_db",
            user="postgres",
            password="",
            port="5432"
        )
        connection.autocommit = True
        cursor = connection.cursor()

        with open(sql_dosya_yolu, "r", encoding="utf-8") as f:
            sql_komutlari = f.read()
        
        cursor.execute(sql_komutlari)
        print("\nBAŞARILI: Şevval'in hazırladığı tablolar (patients, health_records, locations) veritabanına başarıyla kuruldu!")
        
        cursor.close()
        connection.close()
    else:
        print("Hata: Proje klasöründe '01_create_tables.sql' dosyası hiçbir yerde bulunamadı.")

except Exception as error:
    print(f"Kurulum sırasında hata oluştu: {error}")