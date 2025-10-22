import pandas as pd
import plotly.graph_objects as go

# 1. Baca data dari Google Sheets
url_ruang = "https://docs.google.com/spreadsheets/d/1CJuK0EetknB67O6CwXxXlFObHkYHhGPP/export?format=csv"
url_matkul = "https://docs.google.com/spreadsheets/d/13PXTH2JAk51azCj6KzwjD59OAZrKt1f0/export?format=csv"

df_ruang = pd.read_csv(url_ruang)
df_matkul = pd.read_csv(url_matkul)

# 2. Gabungkan data ruang & matkul
df_gabung = df_matkul.merge(df_ruang[['ruang', 'kapasitas']], on='ruang', how='left')

# 3. Pastikan kolom numerik
df_gabung['peserta'] = pd.to_numeric(df_gabung['peserta'], errors='coerce')
df_gabung['kapasitas'] = pd.to_numeric(df_gabung['kapasitas'], errors='coerce')

# 4. Bersihkan teks hari dan sesi
df_gabung['hari'] = (
    df_gabung['hari']
    .astype(str)
    .str.strip()
    .str.upper()
    .replace(r'\s+', ' ', regex=True)
)

df_gabung['sesi'] = (
    df_gabung['sesi']
    .astype(str)
    .str.strip()
    .str.upper()
    .replace(r'\s+', ' ', regex=True)
)

# 5. Gabungkan kolom hari dan sesi
df_gabung['hari_sesi'] = df_gabung['hari'] + " - " + df_gabung['sesi']

# 6. Hitung efisiensi total per hari-sesi
efisiensi_hari_sesi = (
    df_gabung.groupby(['hari', 'sesi'])
    .agg({'peserta': 'sum', 'kapasitas': 'sum'})
    .reset_index()
)
efisiensi_hari_sesi['efisiensi (%)'] = (
    efisiensi_hari_sesi['peserta'] / efisiensi_hari_sesi['kapasitas'] * 100
).round(2)

# 7. Urutkan hari dan sesi agar rapi
urutan_hari = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT"]
efisiensi_hari_sesi['hari'] = pd.Categorical(
    efisiensi_hari_sesi['hari'], categories=urutan_hari, ordered=True
)
efisiensi_hari_sesi = efisiensi_hari_sesi.sort_values(['hari', 'sesi'])

# 8. Buat kolom gabungan Hari - Sesi
efisiensi_hari_sesi['hari_sesi'] = (
    efisiensi_hari_sesi['hari'].astype(str) + " - " + efisiensi_hari_sesi['sesi'].astype(str)
)

# 9. Buat figure Plotly
fig = go.Figure()

# --- Semua Hari (default tampil) ---
fig.add_trace(go.Bar(
    x=efisiensi_hari_sesi['hari_sesi'],
    y=efisiensi_hari_sesi['efisiensi (%)'],
    name="Semua Hari",
    visible=True,
    text=efisiensi_hari_sesi['efisiensi (%)'].astype(str) + '%',
    textposition='outside',
    marker_color='steelblue'
))

# --- Tambahkan trace per hari ---
traces = ['Semua Hari']
for hari in urutan_hari:
    subset = efisiensi_hari_sesi[efisiensi_hari_sesi['hari'] == hari]
    fig.add_trace(go.Bar(
        x=subset['hari_sesi'],
        y=subset['efisiensi (%)'],
        name=hari,
        visible=False,
        text=subset['efisiensi (%)'].astype(str) + '%',
        textposition='outside',
        marker_color='seagreen'
    ))
    traces.append(hari)

# 10. Dropdown filter per hari
buttons = [
    dict(
        label="Semua Hari",
        method="update",
        args=[{"visible": [True] + [False] * (len(traces) - 1)},
              {"title": ""}]
    )
]

for i, hari in enumerate(urutan_hari):
    vis = [False] * len(traces)
    vis[i + 1] = True
    buttons.append(
        dict(
            label=hari.title(),
            method="update",
            args=[{"visible": vis}, {"title": ""}]
        )
    )

# 11. Layout tampilan (tanpa judul + dropdown di kanan atas)
fig.update_layout(
    xaxis_title="Hari - Sesi",
    yaxis_title="Efisiensi (%)",
    xaxis_tickangle=45,
    updatemenus=[
        dict(
            buttons=buttons,
            direction="down",
            showactive=True,
            active=0,
            x=0.95,
            y=1.15,
            xanchor="right",
            yanchor="top"
        )
    ],
    height=650,
    plot_bgcolor='rgba(245,245,240,1)',
    paper_bgcolor='rgba(255,255,245,1)',
    font=dict(size=12),
    title=""  # ← tidak ada judul
)

# 12. Styling label & sumbu
fig.update_traces(textfont_size=11)
fig.update_yaxes(range=[0, efisiensi_hari_sesi['efisiensi (%)'].max() + 10])

# 13. Tampilkan grafik
fig.show()