import pandas as pd
import plotly.graph_objects as go

# 1. Baca data
url_ruang = "https://docs.google.com/spreadsheets/d/1CJuK0EetknB67O6CwXxXlFObHkYHhGPP/export?format=csv"
url_matkul = "https://docs.google.com/spreadsheets/d/13PXTH2JAk51azCj6KzwjD59OAZrKt1f0/export?format=csv"

df_ruang = pd.read_csv(url_ruang)
df_matkul = pd.read_csv(url_matkul)

# 2. Gabungkan
df_gabung = df_matkul.merge(df_ruang[['ruang', 'kapasitas']], on='ruang', how='left')

# 3. Pastikan angka
df_gabung['peserta'] = pd.to_numeric(df_gabung['peserta'], errors='coerce')
df_gabung['kapasitas'] = pd.to_numeric(df_gabung['kapasitas'], errors='coerce')

# 4. Hitung efisiensi per kelas
df_gabung['efisiensi'] = df_gabung['peserta'] / df_gabung['kapasitas']

# 5. Rata-rata efisiensi per ruang
efisiensi_per_ruang = (
    df_gabung.groupby('ruang')['efisiensi']
    .mean()
    .reset_index()
)

# 6. Ubah ke persen
efisiensi_per_ruang['efisiensi (%)'] = (efisiensi_per_ruang['efisiensi'] * 100).round(2)

# 7. Urutkan dari tertinggi ke terendah
efisiensi_per_ruang = efisiensi_per_ruang.sort_values('efisiensi (%)', ascending=False)

# 8. Buat subset data
top10 = efisiensi_per_ruang.head(10)
bottom10 = efisiensi_per_ruang.tail(10)
all_data = efisiensi_per_ruang

# 9. Buat grafik interaktif dengan label di batang
fig = go.Figure()

# --- Semua data ---
fig.add_trace(go.Bar(
    x=all_data['ruang'],
    y=all_data['efisiensi (%)'],
    name='Semua Ruang',
    visible=False,  # tidak tampil duluan
    text=all_data['efisiensi (%)'].astype(str) + '%',
    textposition='outside',
    marker_color='steelblue'
))

# --- 10 Teratas ---
fig.add_trace(go.Bar(
    x=top10['ruang'],
    y=top10['efisiensi (%)'],
    name='10 Teratas',
    visible=True,  # tampil pertama
    text=top10['efisiensi (%)'].astype(str) + '%',
    textposition='outside',
    marker_color='seagreen'
))

# --- 10 Terbawah ---
fig.add_trace(go.Bar(
    x=bottom10['ruang'],
    y=bottom10['efisiensi (%)'],
    name='10 Terbawah',
    visible=False,
    text=bottom10['efisiensi (%)'].astype(str) + '%',
    textposition='outside',
    marker_color='indianred'
))

# 10. Dropdown filter
fig.update_layout(
    title="Efisiensi Penggunaan Ruangan (%)",
    xaxis_title="Ruang",
    yaxis_title="Efisiensi (%)",
    xaxis_tickangle=90,
    updatemenus=[
        dict(
            buttons=list([
                dict(label="Semua Ruang",
                     method="update",
                     args=[{"visible": [True, False, False]},
                           {"title": "Semua Ruangan"}]),
                dict(label="10 Teratas",
                     method="update",
                     args=[{"visible": [False, True, False]},
                           {"title": "10 Ruangan dengan Efisiensi Tertinggi"}]),
                dict(label="10 Terbawah",
                     method="update",
                     args=[{"visible": [False, False, True]},
                           {"title": "10 Ruangan dengan Efisiensi Terendah"}]),
            ]),
            direction="down",
            showactive=True,
            x=0.1,
            y=1.15,
            xanchor="left",
            yanchor="top"
        ),
    ],
    height=600
)

# 11. Sedikit styling tambahan
fig.update_traces(textfont_size=11)
fig.update_yaxes(range=[0, efisiensi_per_ruang['efisiensi (%)'].max() + 10])

# 12. Tampilkan grafik
fig.show()