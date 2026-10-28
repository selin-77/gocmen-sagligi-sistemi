import random
from faker import Faker
import pandas as pd

# Türkçe sahte veri üretmek için Faker ayarı
fake = Faker('tr_TR')

print("20.000+ sentetik sağlık verisi üretiliyor, lütfen bekleyin...")

# 20.000 adet kayıt üretelim
num_records = 20050
data = []

chronic_conditions = ['Hipertansiyon', 'Diyabet', 'Astim', 'Kalp Rahatsizligi', 'Yok', 'Kronik Bronkit']
vaccination_statuses = ['Tam Asili', 'Eksik Asili', 'Asisiz']
genders = ['Kadin', 'Erkek']

# Türkiye sınırları ve geçiş bölgelerine yakın koordinat sınırları (Örn: Hatay, Kilis, Gaziantep çevresi)
for i in range(1, num_records + 1):
    record = {
        'patient_id': i,
        'full_name': fake.name(),
        'age': random.randint(1, 85),
        'gender': random.choice(genders),
        'chronic_disease': random.choice(chronic_conditions),
        'vaccination_status': random.choice(vaccination_statuses),
        # Sınır geçiş ve barınma bölgesi koordinatları (Enlem / Boylam)
        'latitude': round(random.uniform(36.5, 38.5), 6),
        'longitude': round(random.uniform(36.0, 38.0), 6),
        'registration_date': fake.date_between(start_date='-2y', end_date='today')
    }
    data.append(record)

# Pandas DataFrame'e dönüştürme
df = pd.DataFrame(data)

# CSV dosyası olarak da yedekleyelim (İstlersen veriyi dosya olarak da görürsün)
df.to_csv("gocmen_saglik_sentetik_veri.csv", index=False, encoding='utf-8-sig')

print(f"Başarıyla {num_records} adet sentetik kayıt üretildi ve 'gocmen_saglik_sentetik_veri.csv' olarak kaydedildi!")