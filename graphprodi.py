import pandas as pd
import plotly.graph_objects as go

# 1. Baca data dari Google Sheets
url_ruang = "https://docs.google.com/spreadsheets/d/1CJuK0EetknB67O6CwXxXlFObHkYHhGPP/export?format=csv"
url_matkul = "https://docs.google.com/spreadsheets/d/13PXTH2JAk51azCj6KzwjD59OAZrKt1f0/export?format=csv"

df_ruang = pd.read_csv(url_ruang)
df_matkul = pd.read_csv(url_matkul)

# 2. Gabungkan data ruang & matkul
df_gabung = df_matkul.merge(df_ruang[['ruang', 'kapasitas']], on='ruang', how='left')

# 3. Ubah tipe data
df_gabung['peserta'] = pd.to_numeric(df_gabung['peserta'], errors='coerce')
df_gabung['kapasitas'] = pd.to_numeric(df_gabung['kapasitas'], errors='coerce')

# 4. Bersihkan kolom prodi agar tidak dobel
df_gabung['prodi'] = (
    df_gabung['prodi']
    .astype(str)
    .str.strip()
    .str.upper()
    .replace(r'\s+', ' ', regex=True)
)

# 5. Hapus data kosong
df_gabung = df_gabung.dropna(subset=['prodi', 'peserta', 'kapasitas'])

# 6. Hitung total peserta dan kapasitas per prodi
efisiensi_per_prodi = (
    df_gabung.groupby('prodi')
    .agg({'peserta': 'sum', 'kapasitas': 'sum'})
    .reset_index()
)

# 7. Hitung efisiensi (%)
efisiensi_per_prodi['efisiensi (%)'] = (
    efisiensi_per_prodi['peserta'] / efisiensi_per_prodi['kapasitas'] * 100
).round(2)

# 8. Tambahkan jumlah kelas
efisiensi_per_prodi['jumlah_kelas'] = df_gabung.groupby('prodi').size().values

# 9. Urutkan dari efisiensi tertinggi ke terendah
efisiensi_per_prodi = efisiensi_per_prodi.sort_values('efisiensi (%)', ascending=False)

# 10. Buat grafik batang
fig = go.Figure(
    data=[
        go.Bar(
            x=efisiensi_per_prodi['prodi'],
            y=efisiensi_per_prodi['efisiensi (%)'],
            text=efisiensi_per_prodi['efisiensi (%)'].astype(str) + '%',
            textposition='outside',
            marker_color='steelblue'
        )
    ]
)

# 11. Layout tampilan tanpa judul
fig.update_layout(
    xaxis_title="Program Studi",
    yaxis_title="Efisiensi (%)",
    xaxis_tickangle=45,
    height=600,
    plot_bgcolor='rgba(245,245,245,1)',
    paper_bgcolor='rgba(255,255,255,1)',
    font=dict(size=12),
    title=""  # ← kosongkan judul
)

fig.update_yaxes(range=[0, efisiensi_per_prodi['efisiensi (%)'].max() + 10])
fig.update_traces(textfont_size=11)

# 12. Tampilkan grafik
fig.show()