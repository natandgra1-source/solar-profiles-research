"""
app.py — Integrated Solar + Load Profile Dashboard
Run:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="⚡ Solar & Load Profiles",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def load_solar():
    return pd.read_csv(Path(__file__).parent / "data" / "solar_seasonal_profiles.csv")

@st.cache_data
def load_demand():
    df = pd.read_csv(Path(__file__).parent / "data" / "load_profiles.csv")
    df.columns = df.columns.str.strip()
    df["Country"] = df["Country"].str.strip()
    return df

solar_df = load_solar()
load_df  = load_demand()

SEASONS = {
    "Winter (Jan 1)": "Winter_Jan1",
    "Spring (Apr 1)": "Spring_Apr1",
    "Summer (Jul 1)": "Summer_Jul1",
    "Autumn (Oct 1)": "Autumn_Oct1",
}
SOLAR_COLOR   = "#f59e0b"
LOAD_COLOR    = "#60a5fa"
SURPLUS_COLOR = "#34d399"
DEFICIT_COLOR = "#f87171"

BOTH = sorted(set(solar_df["Country"]) & set(load_df["Country"]))

def get_solar_hours(country, season_key):
    row = solar_df[solar_df["Country"] == country].iloc[0]
    return np.array([row[f"{season_key}_Hour_{h:02d}_W"] for h in range(24)])

def get_load_hours(country):
    row = load_df[load_df["Country"] == country].iloc[0]
    raw = np.array([row[f"Hour {h}"] for h in range(24)])
    industrial = row["Industrial"] if pd.notna(row["Industrial"]) else 10
    base_load_w = 300 + industrial * 30
    return raw * base_load_w

def get_load_meta(country):
    row = load_df[load_df["Country"] == country].iloc[0]
    return {
        "climate":    row["Climate"],
        "population": row["Population"],
        "gdp":        row["GDP"],
        "industrial": row["Industrial"],
        "solar_index":row["Solar"],
    }

def dark_layout(height=380, title="", xtitle="Hour", ytitle="Power (W)"):
    return dict(
        title=title, height=height,
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="white"),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
        xaxis=dict(gridcolor="#1e293b", title=xtitle),
        yaxis=dict(gridcolor="#1e293b", title=ytitle),
    )

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("⚡ Solar & Load Atlas")
st.sidebar.caption("PVWatts V8 · Load Profiles · 96 Countries")
st.sidebar.divider()
page = st.sidebar.radio("Navigate", [
    "🏠 Overview",
    "📊 Country Deep Dive",
    "⚖️ Solar vs Load",
    "🌍 World Map",
    "🏆 Rankings",
    "🔍 Compare Countries",
])

# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("⚡ Global Solar Generation & Load Profiles")
    st.markdown("Combining **PVWatts solar generation** with **electricity load profiles** for **96 countries** across 4 seasons.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍 Countries", "96")
    c2.metric("🌞 Solar Model", "PVWatts V8")
    c3.metric("📅 Seasons", "4")
    c4.metric("⏰ Resolution", "Hourly")

    st.divider()
    st.subheader("Countries by Climate Type")
    climate_counts = load_df[load_df["Country"].isin(BOTH)]["Climate"].str.strip().value_counts()
    fig = px.bar(x=climate_counts.index, y=climate_counts.values,
                 color=climate_counts.index, color_discrete_sequence=px.colors.qualitative.Bold,
                 labels={"x": "Climate", "y": "Countries"})
    fig.update_layout(**dark_layout(300, ytitle="Countries", xtitle="Climate"), showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.info("**📊 Country Deep Dive**\nSolar vs load, surplus/deficit, seasonal coverage for any country.")
    c2.info("**⚖️ Solar vs Load**\nDirect hourly overlay with adjustable system size and coverage gauge.")
    c3.info("**🏆 Rankings**\nRank all 96 countries by coverage %, surplus, or deficit.")

# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Country Deep Dive":
    st.title("📊 Country Deep Dive")

    col1, col2 = st.columns([2, 1])
    with col1:
        country = st.selectbox("Select Country", BOTH)
    with col2:
        season_label = st.selectbox("Season", list(SEASONS.keys()))

    season_key = SEASONS[season_label]
    solar_h = get_solar_hours(country, season_key)
    load_h  = get_load_hours(country)
    meta    = get_load_meta(country)
    hours   = [f"{h:02d}:00" for h in range(24)]
    net     = solar_h - load_h
    surplus = np.where(net > 0, net, 0)
    deficit = np.where(net < 0, -net, 0)
    coverage = np.sum(np.minimum(solar_h, load_h)) / np.sum(load_h) * 100

    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("☀️ Solar Daily",    f"{solar_h.sum()/1000:.1f} kWh")
    c2.metric("⚡ Load Daily",     f"{load_h.sum()/1000:.1f} kWh")
    c3.metric("✅ Solar Coverage", f"{coverage:.1f}%")
    c4.metric("📈 Peak Surplus",   f"{surplus.max():.0f} W", f"at {np.argmax(surplus):02d}:00")
    c5.metric("📉 Peak Deficit",   f"{deficit.max():.0f} W", f"at {np.argmax(deficit):02d}:00")

    st.divider()

    # Overlay chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=load_h, name="⚡ Load",
        mode="lines", line=dict(color=LOAD_COLOR, width=2.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(96,165,250,0.1)"))
    fig.add_trace(go.Scatter(x=hours, y=solar_h, name="☀️ Solar",
        mode="lines", line=dict(color=SOLAR_COLOR, width=2.5),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.15)"))
    fig.update_layout(**dark_layout(380, f"Solar vs Load — {country} · {season_label}"),
                      legend=dict(bgcolor="#1e293b", orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    # Net balance
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=hours, y=[v if v >= 0 else 0 for v in net],
                          name="Surplus", marker_color=SURPLUS_COLOR))
    fig2.add_trace(go.Bar(x=hours, y=[v if v < 0 else 0 for v in net],
                          name="Deficit", marker_color=DEFICIT_COLOR))
    fig2.add_hline(y=0, line_color="white", line_width=1, opacity=0.3)
    fig2.update_layout(**dark_layout(280, f"Net Balance (Solar − Load)", ytitle="Net Power (W)"),
                       barmode="overlay", margin=dict(t=40))
    st.plotly_chart(fig2, use_container_width=True)

    # Seasonal summary
    st.divider()
    st.subheader("All Seasons Comparison")
    solar_kwh, load_kwh, covs = [], [], []
    for sk in SEASONS.values():
        sh = get_solar_hours(country, sk)
        lh = get_load_hours(country)
        solar_kwh.append(round(sh.sum()/1000, 1))
        load_kwh.append(round(lh.sum()/1000, 1))
        covs.append(round(np.sum(np.minimum(sh, lh)) / np.sum(lh) * 100, 1))

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=list(SEASONS.keys()), y=solar_kwh, name="☀️ Solar (kWh)", marker_color=SOLAR_COLOR))
    fig3.add_trace(go.Bar(x=list(SEASONS.keys()), y=load_kwh,  name="⚡ Load (kWh)",  marker_color=LOAD_COLOR))
    fig3.update_layout(**dark_layout(280, ytitle="Daily Energy (kWh)", xtitle="Season"),
                       barmode="group", margin=dict(t=10))
    st.plotly_chart(fig3, use_container_width=True)

    cov_cols = st.columns(4)
    for i, (sl, cov) in enumerate(zip(SEASONS.keys(), covs)):
        cov_cols[i].metric(sl, f"{cov:.1f}%", "coverage")

    st.divider()
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("🌡️ Climate",        meta["climate"])
    mc2.metric("👥 Population",     f"{meta['population']/1e6:.1f}M")
    mc3.metric("💰 GDP",            f"${meta['gdp']/1e9:.0f}B")
    mc4.metric("🏭 Industrial Idx", f"{meta['industrial']:.0f}")

# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚖️ Solar vs Load":
    st.title("⚖️ Solar Generation vs Load Demand")

    col1, col2, col3 = st.columns(3)
    with col1:
        country = st.selectbox("Country", BOTH)
    with col2:
        season_label = st.selectbox("Season", list(SEASONS.keys()))
    with col3:
        system_kw = st.slider("System Size (kW DC)", 1, 100, 4)

    season_key = SEASONS[season_label]
    solar_h = get_solar_hours(country, season_key) * (system_kw / 4.0)
    load_h  = get_load_hours(country)
    hours   = [f"{h:02d}:00" for h in range(24)]
    net     = solar_h - load_h
    coverage = np.sum(np.minimum(solar_h, load_h)) / np.sum(load_h) * 100

    st.divider()
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(coverage, 1),
        title={"text": "Solar Coverage of Load (%)", "font": {"color": "white", "size": 15}},
        number={"suffix": "%", "font": {"color": SOLAR_COLOR, "size": 42}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "white"},
            "bar": {"color": SOLAR_COLOR},
            "steps": [
                {"range": [0,  30], "color": "#1e293b"},
                {"range": [30, 70], "color": "#1e3a5f"},
                {"range": [70,100], "color": "#14532d"},
            ],
        },
    ))
    gauge.update_layout(height=230, paper_bgcolor="#0f172a",
                        font=dict(color="white"), margin=dict(t=20, b=0))
    st.plotly_chart(gauge, use_container_width=True)

    st.divider()
    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hours, y=load_h, name="⚡ Load",
            fill="tozeroy", fillcolor="rgba(96,165,250,0.2)",
            line=dict(color=LOAD_COLOR, width=2)))
        fig.add_trace(go.Scatter(x=hours, y=solar_h, name="☀️ Solar",
            fill="tozeroy", fillcolor="rgba(245,158,11,0.25)",
            line=dict(color=SOLAR_COLOR, width=2.5)))
        fig.update_layout(**dark_layout(350, f"{country} · {season_label} · {system_kw} kW"),
                          legend=dict(bgcolor="#1e293b"))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("**Hourly Balance**")
        rows = [{"Hour": f"{h:02d}:00",
                 "Solar W": f"{solar_h[h]:.0f}",
                 "Load W":  f"{load_h[h]:.0f}",
                 "Balance": f"{'▲' if net[h]>=0 else '▼'} {abs(net[h]):.0f}"}
                for h in range(24)]
        st.dataframe(pd.DataFrame(rows), height=340, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 World Map":
    st.title("🌍 World Map")

    col1, col2 = st.columns(2)
    with col1:
        season_label = st.selectbox("Season", list(SEASONS.keys()))
    with col2:
        metric = st.radio("Metric", ["Solar Coverage %", "Solar Daily kWh", "Load Daily kWh"], horizontal=True)

    season_key = SEASONS[season_label]
    rows = []
    for country in BOTH:
        sh = get_solar_hours(country, season_key)
        lh = get_load_hours(country)
        cov = np.sum(np.minimum(sh, lh)) / np.sum(lh) * 100
        rows.append({"Country": country, "Solar Coverage %": round(cov, 1),
                     "Solar Daily kWh": round(sh.sum()/1000, 1),
                     "Load Daily kWh":  round(lh.sum()/1000, 1)})
    map_df = pd.DataFrame(rows)

    cscale = [[0,"#1e293b"],[0.4,"#1d4ed8"],[0.7,"#f59e0b"],[1,"#34d399"]] if "Coverage" in metric \
              else [[0,"#1d4ed8"],[0.5,"#f59e0b"],[1,"#ef4444"]]

    fig = px.choropleth(map_df, locations="Country", locationmode="country names",
                        color=metric, hover_name="Country",
                        color_continuous_scale=cscale, labels={metric: metric})
    fig.update_layout(
        height=500, paper_bgcolor="#0f172a",
        geo=dict(bgcolor="#0f172a", showframe=False, showcoastlines=True,
                 coastlinecolor="#334155", showland=True, landcolor="#1e293b",
                 showocean=True, oceancolor="#0f172a"),
        coloraxis_colorbar=dict(
            title=dict(text=metric, font=dict(color="white")),
            tickfont=dict(color="white")),
        font=dict(color="white"), margin=dict(l=0,r=0,t=10,b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🥇 Best Coverage",   map_df.nlargest(1,"Solar Coverage %").iloc[0]["Country"],
              f"{map_df['Solar Coverage %'].max():.1f}%")
    c2.metric("🥉 Lowest Coverage", map_df.nsmallest(1,"Solar Coverage %").iloc[0]["Country"],
              f"{map_df['Solar Coverage %'].min():.1f}%")
    c3.metric("📊 Avg Coverage",    f"{map_df['Solar Coverage %'].mean():.1f}%")
    c4.metric("✅ >50% coverage",   f"{(map_df['Solar Coverage %']>50).sum()} countries")

# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Rankings":
    st.title("🏆 Rankings")

    col1, col2, col3 = st.columns(3)
    with col1:
        season_label = st.selectbox("Season", list(SEASONS.keys()))
    with col2:
        metric = st.radio("Rank by", ["Solar Coverage %", "Solar Daily kWh", "Peak Surplus W", "Peak Deficit W"])
    with col3:
        top_n = st.slider("Top N", 10, 96, 20)

    season_key = SEASONS[season_label]
    rows = []
    for country in BOTH:
        sh = get_solar_hours(country, season_key)
        lh = get_load_hours(country)
        net = sh - lh
        cov = np.sum(np.minimum(sh, lh)) / np.sum(lh) * 100
        rows.append({"Country": country,
                     "Solar Coverage %": round(cov, 1),
                     "Solar Daily kWh":  round(sh.sum()/1000, 1),
                     "Peak Surplus W":   round(max(0, net.max()), 0),
                     "Peak Deficit W":   round(max(0, (-net).max()), 0)})
    rank_df = pd.DataFrame(rows).sort_values(metric, ascending=False).head(top_n).reset_index(drop=True)
    rank_df.index += 1

    fig = go.Figure(go.Bar(
        x=rank_df[metric], y=rank_df["Country"], orientation="h",
        marker=dict(color=rank_df[metric],
                    colorscale=[[0,"#1d4ed8"],[0.5,"#f59e0b"],[1,"#34d399"]]),
        text=rank_df[metric].apply(lambda v: f"{v:,.1f}"), textposition="outside",
    ))
    fig.update_layout(**dark_layout(max(400, top_n*22), f"Top {top_n} — {metric} · {season_label}",
                                    xtitle=metric, ytitle=""),
                      yaxis=dict(autorange="reversed", gridcolor="#1e293b"),
                      margin=dict(l=150, r=80, t=50))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(rank_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Compare Countries":
    st.title("🔍 Compare Countries")

    col1, col2 = st.columns([3, 1])
    with col1:
        default = [c for c in ["Germany","Nigeria","India","Japan"] if c in BOTH]
        countries = st.multiselect("Select countries (up to 6)", BOTH,
                                    default=default, max_selections=6)
    with col2:
        season_label = st.selectbox("Season", list(SEASONS.keys()))

    if len(countries) < 2:
        st.info("Select at least 2 countries.")
    else:
        season_key = SEASONS[season_label]
        hours  = [f"{h:02d}:00" for h in range(24)]
        colors = px.colors.qualitative.Bold

        tab1, tab2, tab3 = st.tabs(["☀️ Solar Profiles", "⚡ Load Profiles", "📊 Summary"])

        with tab1:
            fig = go.Figure()
            for i, c in enumerate(countries):
                sh = get_solar_hours(c, season_key)
                fig.add_trace(go.Scatter(x=hours, y=sh, name=c, mode="lines",
                                          line=dict(width=2, color=colors[i])))
            fig.update_layout(**dark_layout(350, f"Solar Generation — {season_label}"))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = go.Figure()
            for i, c in enumerate(countries):
                lh = get_load_hours(c)
                fig.add_trace(go.Scatter(x=hours, y=lh, name=c, mode="lines",
                                          line=dict(width=2, color=colors[i], dash="dot")))
            fig.update_layout(**dark_layout(350, "Load Demand Profiles"))
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            summary = []
            for c in countries:
                sh  = get_solar_hours(c, season_key)
                lh  = get_load_hours(c)
                net = sh - lh
                cov = np.sum(np.minimum(sh, lh)) / np.sum(lh) * 100
                meta = get_load_meta(c)
                summary.append({"Country": c, "Climate": meta["climate"],
                                 "Solar kWh": f"{sh.sum()/1000:.1f}",
                                 "Load kWh":  f"{lh.sum()/1000:.1f}",
                                 "Coverage":  f"{cov:.1f}%",
                                 "Surplus W": f"{max(0,net.max()):.0f}",
                                 "Deficit W": f"{max(0,(-net).max()):.0f}"})
            st.dataframe(pd.DataFrame(summary).set_index("Country"), use_container_width=True)

            covs = [float(r["Coverage"].replace("%","")) for r in summary]
            fig = go.Figure(go.Bar(x=[r["Country"] for r in summary], y=covs,
                                    marker_color=colors[:len(countries)],
                                    text=[f"{v:.1f}%" for v in covs], textposition="outside"))
            fig.update_layout(**dark_layout(300, "Solar Coverage of Load (%)", xtitle="Country", ytitle="%"),
                               showlegend=False,
                               yaxis=dict(gridcolor="#1e293b", range=[0, max(covs)*1.2]))
            st.plotly_chart(fig, use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("© 2026 Nathaniel Grange\nGeorgia Institute of Technology")
st.sidebar.caption("Solar: PVWatts V8 (pvlib)\nLoad: Country load profile dataset")
