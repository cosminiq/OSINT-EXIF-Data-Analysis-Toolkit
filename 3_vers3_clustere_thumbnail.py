import json
import folium
import pandas as pd
import os
import shutil
from tqdm import tqdm
from PIL import Image
import html
from folium.plugins import MarkerCluster

# Crearea unui director static pentru a salva fișierele
static_dir = "static"
# Definește calea fișierului JSON
json_file_path = r"Jpg_folder\Geolocation_data_output\geo_location.json"



if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Funcție pentru a crea un thumbnail
def create_thumbnail(image_path, thumbnail_path):
    try:
        img = Image.open(image_path)
        img.thumbnail((200, 200))  # dimensiune thumbnail
        img.save(thumbnail_path)
    except Exception as e:
        print(f"❌ Eroare la crearea thumbnail-ului pentru {image_path}: {e}")

# Încarcă datele din fișierul JSON
with open(json_file_path, encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Elimină rândurile fără coordonate
df = df[df['GeolocationPosition'].notna()]
df[['lat', 'lon']] = df['GeolocationPosition'].str.split(', ', expand=True)
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon"])

# Verifică dacă există date valide
if df.empty:
    print("❌ Eroare: Nicio coordonată validă găsită!")
    exit()

# Creare hartă centrată pe primul punct valid
m = folium.Map(location=[df.iloc[0]["lat"], df.iloc[0]["lon"]], zoom_start=10)

# Creează un cluster
marker_cluster = MarkerCluster().add_to(m)

# Listă pentru coordonatele markerelor
coordinates = []

# Adaugă marker-ele și salvează coordonatele pentru linie
for _, row in tqdm(df.iterrows(), total=len(df), desc="Procesare imagini"):
    popup_text = f"""
        <b>Filename:</b> {html.escape(row['Filename'])}<br>
        <b>MD5:</b> {row['MD5_Hash']}<br>
        <b>Location:</b> {row.get('GeolocationCity', 'Unknown')}, {row.get('GeolocationCountry', 'Unknown')}<br>
    """
    
    # Calea completă a imaginii
    image_path = row['Full Path']
    
    # Verifică dacă imaginea există și are coordonate valide
    if os.path.exists(image_path):
        # Calea thumbnail-ului în directorul static
        thumbnail_filename = f"thumb_{os.path.basename(image_path)}"
        thumbnail_path = os.path.join(static_dir, thumbnail_filename)
        
        # Crează thumbnail-ul
        create_thumbnail(image_path, thumbnail_path)
        
        # Adăugăm thumbnail-ul la popup
        popup_text += f'<img src="static/{thumbnail_filename}" alt="Thumbnail" style="width:100px;height:100px;"><br>'
    
    # Adaugă marker-ul la hartă
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=folium.Popup(popup_text, max_width=250),
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(marker_cluster)
    
    # Colectăm coordonatele pentru PolyLine
    coordinates.append((row["lat"], row["lon"]))

# Adaugă linia (PolyLine) între toate marker-ele
folium.PolyLine(
    coordinates, 
    color="blue", 
    weight=2.5, 
    opacity=0.8
).add_to(m)

# Salvează harta și anunță utilizatorul
m.save("harta_exif_clusterizata_thumbnail_linii_.html")
print("✅ Harta cu MarkerCluster, linii și imagini (thumbnails) a fost generată: harta_exif_clusterizata_si_linii.html")
