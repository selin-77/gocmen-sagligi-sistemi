import pandas as pd
import folium
from folium.plugins import HeatMap

print("Sentetik veriler okunuyor ve harita hazırlanıyor...")

# 1. Ürettiğimiz CSV dosyasını okuyoruz
df = pd.read_csv("gocmen_saglik_sentetik_veri.csv")

# 2. Türkiye merkezli boş bir harita oluşturuyoruz (Hatay/Gaziantep bölgesi koordinatları)
harita = folium.Map(location=[37.0, 37.0], zoom_start=8)

# 3. Enlem ve boylam verilerini harita için uygun formata getiriyoruz
koordinatlar = df[['latitude', 'longitude']].values.tolist()

# 4. Isı Haritası (Heatmap) katmanını haritaya ekliyoruz
HeatMap(koordinatlar, radius=15).add_to(harita)

# 5. Haritayı HTML dosyası olarak kaydediyoruz
harita.save("gocmen_ogun_isi_haritasi.html")

print("HARİTA HAZIR! 'gocmen_ogun_isi_haritasi.html' dosyası oluşturuldu.")