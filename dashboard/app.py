from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

app = Flask(__name__)

# Route: Halaman Utama (Dashboard)
@app.route('/')
def index():
    # Ambil parameter periode dari URL (default = "2023/2024")
    periode = request.args.get("periode", "2023/2024")

    # Ambil data Google Sheets
    url_ruang = "https://docs.google.com/spreadsheets/d/1CJuK0EetknB67O6CwXxXlFObHkYHhGPP/export?format=csv"
    url_matkul = "https://docs.google.com/spreadsheets/d/13PXTH2JAk51azCj6KzwjD59OAZrKt1f0/export?format=csv"
    df_ruang = pd.read_csv(url_ruang)
    df_matkul = pd.read_csv(url_matkul)

    # Bersihkan dan filter data berdasarkan tahun ajaran
    df_matkul['th_ajaran'] = df_matkul['th_ajaran'].astype(str).str.strip()
    df_filtered = df_matkul[df_matkul['th_ajaran'] == periode]

    # Gabungkan dengan data ruang
    df_gabung = df_filtered.merge(df_ruang[['ruang', 'kapasitas']], on='ruang', how='left')
    df_gabung['peserta'] = pd.to_numeric(df_gabung['peserta'], errors='coerce')
    df_gabung['kapasitas'] = pd.to_numeric(df_gabung['kapasitas'], errors='coerce')
    df_gabung['efisiensi'] = df_gabung['peserta'] / df_gabung['kapasitas']

    # Grafik_1 Berdasarkan Ruang
    efisiensi_per_ruang = (
        df_gabung.groupby('ruang')['efisiensi']
        .mean()
        .reset_index()
    )
    efisiensi_per_ruang['efisiensi (%)'] = (efisiensi_per_ruang['efisiensi'] * 100).round(2)
    efisiensi_per_ruang = efisiensi_per_ruang.sort_values('efisiensi (%)', ascending=False)
    top10 = efisiensi_per_ruang.head(10)
    bottom10 = efisiensi_per_ruang.tail(10)
    all_data = efisiensi_per_ruang

    fig_ruang = go.Figure()
    fig_ruang.add_trace(go.Bar(x=all_data['ruang'], y=all_data['efisiensi (%)'], visible=False, marker_color='steelblue'))
    fig_ruang.add_trace(go.Bar(x=top10['ruang'], y=top10['efisiensi (%)'], visible=True, marker_color='seagreen'))
    fig_ruang.add_trace(go.Bar(x=bottom10['ruang'], y=bottom10['efisiensi (%)'], visible=False, marker_color='indianred'))

    fig_ruang.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        updatemenus=[dict(
            buttons=[
                dict(label="Semua Ruang", method="update", args=[{"visible": [True, False, False]}]),
                dict(label="Top 10", method="update", args=[{"visible": [False, True, False]}]),
                dict(label="Bottom 10", method="update", args=[{"visible": [False, False, True]}]),
            ],
            direction="down",
            x=0.9, y=1.15
        )]
    )
    graph_ruang = pio.to_html(fig_ruang, full_html=False, include_plotlyjs='cdn')

    # Grafik_2 Berdasarkan Program Studi (Grafik Donut)
    df_gabung['prodi'] = df_gabung['prodi'].astype(str).str.strip().str.upper()
    efisiensi_per_prodi = (
        df_gabung.groupby('prodi')
        .agg({'peserta': 'sum', 'kapasitas': 'sum'})
        .reset_index()
    )
    efisiensi_per_prodi['efisiensi (%)'] = (
        efisiensi_per_prodi['peserta'] / efisiensi_per_prodi['kapasitas'] * 100
    ).round(2)

    fig_prodi = go.Figure(
        data=[go.Pie(
            labels=efisiensi_per_prodi['prodi'],
            values=efisiensi_per_prodi['efisiensi (%)'],
            hole=0.5
        )]
    )
    fig_prodi.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=40)
    )
    graph_prodi = pio.to_html(fig_prodi, full_html=False, include_plotlyjs=False)

    # Grafik_3 Berdasarkan Hari & Sesi
    df_gabung['hari'] = df_gabung['hari'].astype(str).str.strip().str.upper().replace(r'\s+', ' ', regex=True)
    df_gabung['sesi'] = df_gabung['sesi'].astype(str).str.strip().str.upper().replace(r'\s+', ' ', regex=True)

    efisiensi_hari_sesi = (
        df_gabung.groupby(['hari', 'sesi'])
        .agg({'peserta': 'sum', 'kapasitas': 'sum'})
        .reset_index()
    )
    efisiensi_hari_sesi['efisiensi (%)'] = (
        efisiensi_hari_sesi['peserta'] / efisiensi_hari_sesi['kapasitas'] * 100
    ).round(2)

    urutan_hari = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT"]
    efisiensi_hari_sesi['hari'] = pd.Categorical(efisiensi_hari_sesi['hari'], categories=urutan_hari, ordered=True)
    efisiensi_hari_sesi = efisiensi_hari_sesi.sort_values(['hari', 'sesi'])

    fig_hari_sesi = go.Figure()
    traces = []
    for hari in urutan_hari:
        df_hari = efisiensi_hari_sesi[efisiensi_hari_sesi['hari'] == hari]
        trace = go.Bar(x=df_hari['sesi'], y=df_hari['efisiensi (%)'], name=hari, visible=False)
        fig_hari_sesi.add_trace(trace)
        traces.append(trace)

    buttons = [
        dict(label="Semua Hari", method="update", args=[{"visible": [True] * len(traces)}, {"title": ""}])
    ]
    for i, hari in enumerate(urutan_hari):
        vis = [False] * len(traces)
        vis[i] = True
        buttons.append(dict(label=hari.title(), method="update",
                            args=[{"visible": vis}, {"title": f"Efisiensi Hari {hari.title()}"}]))

    fig_hari_sesi.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        updatemenus=[dict(buttons=buttons, direction="down", x=0.9, y=1.15)],
        barmode='group'
    )
    for trace in fig_hari_sesi.data:
        trace.visible = True
    graph_hari_sesi = pio.to_html(fig_hari_sesi, full_html=False, include_plotlyjs=False)

    # Dapatkan semua pilihan tahun ajaran unik
    periode_list = sorted(df_matkul['th_ajaran'].dropna().unique())

    return render_template(
        'dashboard.html',
        graph_ruang=graph_ruang,
        graph_prodi=graph_prodi,
        graph_hari_sesi=graph_hari_sesi,
        periode=periode,
        periode_list=periode_list
    )


# Route: Lihat Data Lengkap
@app.route('/lihat_data')
def lihat_data():
    spreadsheets = {
        "ruang": "https://docs.google.com/spreadsheets/d/1CJuK0EetknB67O6CwXxXlFObHkYHhGPP/export?format=csv",
        "matkul": "https://docs.google.com/spreadsheets/d/13PXTH2JAk51azCj6KzwjD59OAZrKt1f0/export?format=csv"
    }
    selected = request.args.get("sheet", "ruang")
    url = spreadsheets.get(selected, spreadsheets["ruang"])
    df = pd.read_csv(url)
    table_html = df.to_html(classes="table table-striped table-bordered table-hover", index=False)

    return render_template("lihat_data.html", table_html=table_html, selected=selected, spreadsheets=spreadsheets)


if __name__ == '__main__':
    app.run(debug=True)