# Göçmen Sağlığı Verileri İçin Rol Bazlı Güvenli Erişim ve Epidemiolojik Takip Sistemi

## Proje Hakkında

Bu proje, göçmen sağlığı verilerinin PostgreSQL üzerinde güvenli bir şekilde saklanmasını, rol bazlı erişim kontrolleriyle korunmasını ve epidemiolojik analizler için kullanılmasını amaçlamaktadır.

## Projenin Amaçları

- Hasta sağlık verilerine erişimi kullanıcı rollerine göre sınırlandırmak.
- PostgreSQL Row-Level Security (RLS) ile hasta kayıtlarına erişimi kontrol etmek.
- Analistler için ham veriler yerine güvenli veri görünümleri sunmak.
- Epidemiolojik özetler üzerinden hastalık ve risk dağılımlarını incelemek.
- Veritabanı sorgularının performansını ölçmek ve karşılaştırmak.
- Sentetik verilerle analiz ve coğrafi görselleştirme çalışmaları yapmak.

## Kullanılan Teknolojiler

- **Veritabanı:** PostgreSQL 15
- **Coğrafi veri:** PostGIS
- **Veri analizi ve test:** Python, psycopg2
- **Güvenlik:** Rol bazlı erişim kontrolü, Row-Level Security (RLS), SQL görünümleri
- **Görselleştirme:** Python ve HTML tabanlı harita

## Veritabanı Güvenliği

Sistemde doktor, analist ve yetkisiz kullanıcı rolleri tanımlanmıştır. Doktorların hasta kayıtlarına erişimi hasta bazlı eşleştirmelerle sınırlandırılır. Analistlere epidemiolojik özetler ve maskelenmiş hasta bilgileri sunan görünümler üzerinden erişim verilir.

## Performans Testleri

Baseline sorguları ile güvenli görünüm üzerinden gerçekleştirilen sorguların çalışma süreleri ölçülür. Sonuçlar test ortamına özgüdür; ölçümler tek başına RLS'nin performansa etkisini kanıtlamaz.

## Proje Dosyaları

- `database/`: Veritabanı kurulum ve güvenlik SQL dosyaları
- `setup_db.py`: Veritabanı kurulum işlemleri
- `veri_uretici.py`: Sentetik veri üretimi
- `veri_uret_ve_yukle.py`: Veri üretimi ve yükleme işlemleri
- `security_test.py`: Güvenlik testleri
- `baseline_test.py`: Baseline testleri
- `baseline_app.py`: Baseline uygulaması
- `compare_performance.py`: Performans karşılaştırması
- `rls_performance_test.py`: Güvenli görünüm performans testi
- `harita_analiz.py`: Coğrafi analiz
- `gocmen_ogun_isi_haritasi.html`: Oluşturulan harita çıktısı

## Kurulum

1. PostgreSQL ve PostGIS kurun.
2. `gocmen_sagligi_db` veritabanını oluşturun.
3. `database/` klasöründeki SQL dosyalarını proje kurulum sırasına göre çalıştırın.
4. Python bağımlılıklarını kurun:

   ```bash
   pip install psycopg2-binary
   ```

5. Veritabanı bağlantı bilgilerini ortam değişkenleri üzerinden tanımlayın.
6. İlgili Python betiklerini çalıştırın.

> Not: Bu projede sentetik veriler kullanılmaktadır. Gerçek kişilere ait sağlık verileri veya kimlik bilgileri paylaşılmamalıdır.
