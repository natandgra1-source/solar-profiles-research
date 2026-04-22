"""
app.py — Streamlit dashboard for Global Solar Profiles
Run:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="🌞 Global Solar Profiles",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = Path(__file__).parent / "data" / "solar_seasonal_profiles.csv"
    return pd.read_csv(path)

df = load_data()

SEASONS = {
    "Winter (Jan 1)":  "Winter_Jan1",
    "Spring (Apr 1)":  "Spring_Apr1",
    "Summer (Jul 1)":  "Summer_Jul1",
    "Autumn (Oct 1)":  "Autumn_Oct1",
}
SEASON_COLORS = {
    "Winter_Jan1": "#60a5fa",
    "Spring_Apr1": "#34d399",
    "Summer_Jul1": "#f59e0b",
    "Autumn_Oct1": "#f97316",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Georgia_Tech_Yellow_Jackets_logo.svg/200px-Georgia_Tech_Yellow_Jackets_logo.svg.png", width=80)
st.sidebar.title("Solar Profiles")
st.sidebar.caption("PVWatts V8 · 4 kW DC · 197 Countries")
st.sidebar.divider()

page = st.sidebar.radio("Navigate", ["🌍 World Map", "📊 Country Profile", "⚖️ Compare", "🏆 Rankings"])

# ── Page: World Map ───────────────────────────────────────────────────────────
if page == "🌍 World Map":
    st.title("🌍 Global Solar Generation Map")
    st.caption("Daily energy output by country — 4 kW PVWatts system, clear-sky model")

    col1, col2 = st.columns([3, 1])
    with col2:
        sel_season_label = st.selectbox("Season", list(SEASONS.keys()))
        metric = st.radio("Metric", ["Daily Energy (Wh)", "Peak Power (W)"])

    season_key = SEASONS[sel_season_label]
    col_name = f"{season_key}_Daily_Wh" if "Energy" in metric else f"{season_key}_Peak_W"
    label = "Daily Energy (Wh)" if "Energy" in metric else "Peak AC Power (W)"

    fig = px.choropleth(
        df,
        locations="Country",
        locationmode="country names",
        color=col_name,
        hover_name="Country",
        hover_data={col_name: ":,.0f", "Latitude": ":.2f", "Longitude": ":.2f"},
        color_continuous_scale=["#1e3a5f", "#1d4ed8", "#f59e0b", "#ef4444"],
        labels={col_name: label},
        title=f"{label} · {sel_season_label}",
    )
    fig.update_layout(
        height=520,
        paper_bgcolor="#0f172a",
        geo=dict(bgcolor="#0f172a", showframe=False, showcoastlines=True,
                 coastlinecolor="#334155", showland=True, landcolor="#1e293b",
                 showocean=True, oceancolor="#0f172a"),
        coloraxis_colorbar=dict(title=label, tickfont=dict(color="white"), titlefont=dict(color="white")),
        font=dict(color="white"),
        title_font=dict(color="white", size=16),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # Quick stats row
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    top = df.nlargest(1, col_name).iloc[0]
    bot = df.nsmallest(1, col_name).iloc[0]
    avg = df[col_name].mean()
    c1.metric("🥇 Highest", top["Country"], f"{top[col_name]:,.0f} {label.split('(')[1][:-1]}")
    c2.metric("🥉 Lowest", bot["Country"], f"{bot[col_name]:,.0f} {label.split('(')[1][:-1]}")
    c3.metric("📊 World Average", f"{avg:,.0f} {label.split('(')[1][:-1]}")
    c4.metric("🌐 Countries", "197")

# ── Page: Country Profile ─────────────────────────────────────────────────────
elif page == "📊 Country Profile":
    st.title("📊 Country Solar Profile")

    col1, col2 = st.columns([2, 1])
    with col1:
        country = st.selectbox("Select Country", sorted(df["Country"].tolist()))
    with col2:
        show_seasons = st.multiselect("Seasons", list(SEASONS.keys()), default=list(SEASONS.keys()))

    row = df[df["Country"] == country].iloc[0]
    hours = list(range(24))
    hour_labels = [f"{h:02d}:00" for h in hours]

    # Stats cards
    st.divider()
    cols = st.columns(4)
    for i, (label, key) in enumerate(SEASONS.items()):
        wh = row[f"{key}_Daily_Wh"]
        pk = row[f"{key}_Peak_W"]
        cols[i].metric(label, f"{wh:,.0f} Wh/day", f"Peak: {pk:,.0f} W")

    # 24-hour chart
    st.divider()
    fig = go.Figure()
    for label in show_seasons:
        key = SEASONS[label]
        vals = [row[f"{key}_Hour_{h:02d}_W"] for h in hours]
        fig.add_trace(go.Scatter(
            x=hour_labels, y=vals, name=label,
            mode="lines", fill="tozeroy",
            line=dict(color=SEASON_COLORS[key], width=2),
            fillcolor=SEASON_COLORS[key].replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in SEASON_COLORS[key] else SEASON_COLORS[key] + "26",
        ))

    fig.update_layout(
        title=f"24-Hour AC Power Profile — {country}",
        xaxis_title="Local Solar Hour",
        yaxis_title="AC Power (W)",
        height=400,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="white"),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
        xaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
        yaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Seasonal energy bar chart
    season_labels = list(SEASONS.keys())
    energy_vals = [row[f"{SEASONS[s]}_Daily_Wh"] for s in season_labels]
    fig2 = go.Figure(go.Bar(
        x=season_labels, y=energy_vals,
        marker_color=[SEASON_COLORS[SEASONS[s]] for s in season_labels],
        text=[f"{v:,.0f} Wh" for v in energy_vals],
        textposition="outside",
    ))
    fig2.update_layout(
        title=f"Daily Energy by Season — {country}",
        yaxis_title="Daily Energy (Wh)",
        height=320,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b"),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Page: Compare ─────────────────────────────────────────────────────────────
elif page == "⚖️ Compare":
    st.title("⚖️ Compare Countries")

    countries = st.multiselect(
        "Select countries to compare (up to 8)",
        sorted(df["Country"].tolist()),
        default=["United States", "Germany", "Australia", "Nigeria"],
        max_selections=8,
    )
    season_label = st.selectbox("Season", list(SEASONS.keys()))
    season_key = SEASONS[season_label]

    if len(countries) < 2:
        st.info("Select at least 2 countries.")
    else:
        hours = list(range(24))
        hour_labels = [f"{h:02d}:00" for h in hours]
        compare_colors = px.colors.qualitative.Bold

        fig = go.Figure()
        for i, c in enumerate(countries):
            row = df[df["Country"] == c].iloc[0]
            vals = [row[f"{season_key}_Hour_{h:02d}_W"] for h in hours]
            fig.add_trace(go.Scatter(
                x=hour_labels, y=vals, name=c,
                mode="lines", line=dict(width=2.5, color=compare_colors[i % len(compare_colors)]),
            ))

        fig.update_layout(
            title=f"24-Hour Comparison — {season_label}",
            xaxis_title="Local Solar Hour", yaxis_title="AC Power (W)",
            height=420,
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        st.subheader("Summary Table")
        rows = []
        for c in countries:
            r = df[df["Country"] == c].iloc[0]
            rows.append({
                "Country": c,
                **{s: f"{r[f'{SEASONS[s]}_Daily_Wh']:,.0f} Wh" for s in SEASONS},
            })
        st.dataframe(pd.DataFrame(rows).set_index("Country"), use_container_width=True)

# ── Page: Rankings ────────────────────────────────────────────────────────────
elif page == "🏆 Rankings":
    st.title("🏆 Country Rankings")

    col1, col2, col3 = st.columns(3)
    with col1:
        season_label = st.selectbox("Season", list(SEASONS.keys()))
    with col2:
        metric = st.radio("Metric", ["Daily Energy (Wh)", "Peak Power (W)"])
    with col3:
        top_n = st.slider("Show top N", 10, 50, 20)

    season_key = SEASONS[season_label]
    col_name = f"{season_key}_Daily_Wh" if "Energy" in metric else f"{season_key}_Peak_W"

    ranked = df[["Country", "Latitude", col_name]].sort_values(col_name, ascending=False).head(top_n).reset_index(drop=True)
    ranked.index += 1
    ranked.columns = ["Country", "Latitude (°)", metric]

    fig = go.Figure(go.Bar(
        x=ranked[metric], y=ranked["Country"],
        orientation="h",
        marker=dict(
            color=ranked[metric],
            colorscale=[[0, "#1d4ed8"], [0.5, "#f59e0b"], [1, "#ef4444"]],
        ),
        text=ranked[metric].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
    ))
    fig.update_layout(
        title=f"Top {top_n} Countries — {metric} · {season_label}",
        height=max(400, top_n * 22),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#1e293b", title=metric),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=150, r=80),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(ranked, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.caption("© 2026 Nathaniel Grange\nGeorgia Institute of Technology")
st.sidebar.caption("Data: PVWatts V8 algorithm (pvlib)\n4 kW DC · Standard module · 14% losses")
