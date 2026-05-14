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
    page_title=" Solar & Load Profiles",
    page_icon="",
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
        xaxis=dict(gridcolor="#1e293b", title=xtitle),
        yaxis=dict(gridcolor="#1e293b", title=ytitle),
    )

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title(" Solar & Load Atlas")
st.sidebar.caption("PVWatts V8 · Load Profiles · 96 Countries")
st.sidebar.divider()
page = st.sidebar.radio("Navigate", [
 "Home",
 "Country Deep Dive",
 "Normalized Load Profiles",
 "Solar vs Load",
 "Rankings",
 "Compare Countries",
])

# ══════════════════════════════════════════════════════════════════════════════
if page == "Home":
    st.title(" Global Solar Generation & Load Profiles")
    st.markdown("Combining **PVWatts solar generation** with **electricity load profiles** for **96 countries** across 4 seasons.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(" Countries", "96")
    c2.metric(" Solar Model", "PVWatts V8")
    c3.metric(" Seasons", "4")
    c4.metric(" Resolution", "Hourly")

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
    c1.info("** Country Deep Dive**\nSolar vs load, surplus/deficit, seasonal coverage for any country.")
    c2.info("** Solar vs Load**\nDirect hourly overlay with adjustable system size and coverage gauge.")
    c3.info("** Rankings**\nRank all 96 countries by coverage %, surplus, or deficit.")

# ══════════════════════════════════════════════════════════════════════════════
elif page == "Country Deep Dive":
    st.title(" Country Deep Dive")

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
    c1.metric(" Solar Daily",    f"{solar_h.sum()/1000:.1f} kWh")
    c2.metric(" Load Daily",     f"{load_h.sum()/1000:.1f} kWh")
    c3.metric(" Solar Coverage", f"{coverage:.1f}%")
    c4.metric(" Peak Surplus",   f"{surplus.max():.0f} W", f"at {np.argmax(surplus):02d}:00")
    c5.metric(" Peak Deficit",   f"{deficit.max():.0f} W", f"at {np.argmax(deficit):02d}:00")

    st.divider()

    # Overlay chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=load_h, name=" Load",
        mode="lines", line=dict(color=LOAD_COLOR, width=2.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(96,165,250,0.1)"))
    fig.add_trace(go.Scatter(x=hours, y=solar_h, name=" Solar",
        mode="lines", line=dict(color=SOLAR_COLOR, width=2.5),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.15)"))
    fig.update_layout(**dark_layout(380, f"Solar vs Load — {country} · {season_label}"))
    fig.update_layout(legend=dict(bgcolor="#1e293b", orientation="h", y=-0.2))
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
    fig3.add_trace(go.Bar(x=list(SEASONS.keys()), y=solar_kwh, name=" Solar (kWh)", marker_color=SOLAR_COLOR))
    fig3.add_trace(go.Bar(x=list(SEASONS.keys()), y=load_kwh,  name=" Load (kWh)",  marker_color=LOAD_COLOR))
    fig3.update_layout(**dark_layout(280, ytitle="Daily Energy (kWh)", xtitle="Season"),
                       barmode="group", margin=dict(t=10))
    st.plotly_chart(fig3, use_container_width=True)

    cov_cols = st.columns(4)
    for i, (sl, cov) in enumerate(zip(SEASONS.keys(), covs)):
        cov_cols[i].metric(sl, f"{cov:.1f}%", "coverage")

    st.divider()
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(" Climate",        meta["climate"])
    mc2.metric(" Population",     f"{meta['population']/1e6:.1f}M")
    mc3.metric(" GDP",            f"${meta['gdp']/1e9:.0f}B")
    mc4.metric(" Industrial Idx", f"{meta['industrial']:.0f}")

# ══════════════════════════════════════════════════════════════════════════════
elif page == "Solar vs Load":
    st.title(" Solar Generation vs Load Demand")

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
        fig.add_trace(go.Scatter(x=hours, y=load_h, name=" Load",
            fill="tozeroy", fillcolor="rgba(96,165,250,0.2)",
            line=dict(color=LOAD_COLOR, width=2)))
        fig.add_trace(go.Scatter(x=hours, y=solar_h, name=" Solar",
            fill="tozeroy", fillcolor="rgba(245,158,11,0.25)",
            line=dict(color=SOLAR_COLOR, width=2.5)))
        fig.update_layout(**dark_layout(350, f"{country} · {season_label} · {system_kw} kW"))
        fig.update_layout(legend=dict(bgcolor="#1e293b"))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("**Hourly Balance**")
        rows = [{"Hour": f"{h:02d}:00",
 "Solar W": f"{solar_h[h]:.0f}",
 "Load W":  f"{load_h[h]:.0f}",
 "Balance": f"{'' if net[h]>=0 else ''} {abs(net[h]):.0f}"}
                for h in range(24)]
        st.dataframe(pd.DataFrame(rows), height=340, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page == "Rankings":
    st.title(" Rankings")

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
                                    xtitle=metric, ytitle=""))
    fig.update_layout(legend=dict(bgcolor="#1e293b"), margin=dict(l=150, r=80, t=50))
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(rank_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page == "Compare Countries":
    st.title(" Compare Countries")

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

        tab1, tab2, tab3 = st.tabs([" Solar Profiles", " Load Profiles", " Summary"])

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
                               showlegend=False)
            fig.update_yaxes(range=[0, max(covs)*1.2])
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page == "Normalized Load Profiles":
    st.title(" Normalized Load Profiles")
    st.markdown(
 "Load profiles normalized around **1.0** (= average hourly demand). "
 "Values **above 1.0** are peak hours; **below 1.0** are off-peak. "
 "Compare the *shape* of demand across countries regardless of absolute scale."
    )
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        view_mode = st.radio("View mode", ["Single Country", "By Climate Group", "All Countries"])
    with col2:
        all_load_countries = sorted(load_df["Country"].str.strip().tolist())
        default_hl = [c for c in ["Germany","Nigeria","India","Japan","Brazil"] if c in all_load_countries]
        highlight = st.multiselect("Highlight countries", all_load_countries, default=default_hl, max_selections=8)
    with col3:
        show_mean = st.checkbox("Show group mean", value=True)
        show_range = st.checkbox("Show min/max band", value=True)

    hours = list(range(24))
    hour_labels = [f"{h:02d}:00" for h in hours]
    CLIMATE_COLORS = {
 "Arid": "#f59e0b", "Temperate": "#60a5fa", "Tropical": "#34d399",
 "Diverse": "#a78bfa", "Continential": "#f87171", "Polar": "#e2e8f0",
    }

    def get_norm(row):
        return np.array([row[f"Hour {h}"] for h in range(24)])

    # ── Single Country ────────────────────────────────────────────────────────
    if view_mode == "Single Country":
        country = st.selectbox("Select Country", all_load_countries)
        row = load_df[load_df["Country"].str.strip() == country].iloc[0]
        p = get_norm(row)
        climate = str(row["Climate"]).strip()
        color = CLIMATE_COLORS.get(climate, "#94a3b8")

        st.divider()
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric(" Climate", climate)
        c2.metric(" Peak Hour",   f"{np.argmax(p):02d}:00", f"{p.max():.3f}x avg")
        c3.metric(" Trough Hour", f"{np.argmin(p):02d}:00", f"{p.min():.3f}x avg")
        c4.metric(" Peak/Trough", f"{p.max()/p.min():.2f}x")
        c5.metric(" Night avg",   f"{np.mean(p[0:6]):.3f}x", "00-05h")

        fig = go.Figure()
        fig.add_hline(y=1.0, line_color="white", line_width=1, opacity=0.3,
                      annotation_text="Average", annotation_position="top right",
                      annotation_font_color="white")
        hex_c = color.lstrip("#")
        r2,g2,b2 = int(hex_c[0:2],16), int(hex_c[2:4],16), int(hex_c[4:6],16)
        fig.add_trace(go.Scatter(x=hour_labels, y=p, name=country,
            mode="lines+markers", marker=dict(size=6),
            line=dict(color=color, width=3),
            fill="tozeroy", fillcolor=f"rgba({r2},{g2},{b2},0.12)"))
        fig.update_layout(**dark_layout(400, f"Normalized Load Profile — {country}", ytitle="Load Factor (x avg)"))
        fig.update_layout(legend=dict(bgcolor="#1e293b"))
        fig.update_yaxes(range=[0.6, max(1.45, p.max()*1.05)])
        st.plotly_chart(fig, use_container_width=True)

        deviation = p - 1.0
        fig2 = go.Figure(go.Bar(
            x=hour_labels, y=deviation,
            marker_color=["#f87171" if v >= 0 else "#60a5fa" for v in deviation],
            text=[f"{v:+.3f}" for v in deviation], textposition="outside",
            textfont=dict(size=8),
        ))
        fig2.add_hline(y=0, line_color="white", line_width=1, opacity=0.4)
        fig2.update_layout(**dark_layout(280, f"Deviation from Average — {country}", ytitle="Load Factor - 1.0"),
                           margin=dict(t=40))
        st.plotly_chart(fig2, use_container_width=True)

    # ── By Climate Group ──────────────────────────────────────────────────────
    elif view_mode == "By Climate Group":
        climates = sorted(load_df["Climate"].str.strip().unique().tolist())
        selected_climates = st.multiselect("Climate groups", climates, default=climates)
        fig = go.Figure()
        fig.add_hline(y=1.0, line_color="white", line_width=1, opacity=0.25)
        for climate in selected_climates:
            grp = load_df[load_df["Climate"].str.strip() == climate]
            profiles = np.array([get_norm(row) for _, row in grp.iterrows()])
            mean_p = profiles.mean(axis=0)
            min_p  = profiles.min(axis=0)
            max_p  = profiles.max(axis=0)
            color  = CLIMATE_COLORS.get(climate, "#94a3b8")
            hex_c  = color.lstrip("#")
            r2,g2,b2 = int(hex_c[0:2],16), int(hex_c[2:4],16), int(hex_c[4:6],16)
            if show_range:
                fig.add_trace(go.Scatter(
                    x=hour_labels + hour_labels[::-1],
                    y=list(max_p) + list(min_p[::-1]),
                    fill="toself", fillcolor=f"rgba({r2},{g2},{b2},0.12)",
                    line=dict(color="rgba(0,0,0,0)"),
                    showlegend=False, hoverinfo="skip",
                ))
            if show_mean:
                fig.add_trace(go.Scatter(
                    x=hour_labels, y=mean_p, name=f"{climate} (n={len(grp)})",
                    mode="lines", line=dict(color=color, width=2.5),
                ))
        for c in highlight:
            rows = load_df[load_df["Country"].str.strip() == c]
            if not rows.empty:
                p = get_norm(rows.iloc[0])
                fig.add_trace(go.Scatter(x=hour_labels, y=p, name=f" {c}",
                    mode="lines", line=dict(width=1.5, dash="dot", color="white")))
        fig.update_layout(**dark_layout(480, "Normalized Load Profiles by Climate Group", ytitle="Load Factor (x avg)"))
        fig.update_layout(legend=dict(bgcolor="#1e293b", bordercolor="#334155"))
        fig.update_yaxes(range=[0.6, 1.5])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Climate Group Statistics")
        stats = []
        for climate in selected_climates:
            grp = load_df[load_df["Climate"].str.strip() == climate]
            profiles = np.array([get_norm(row) for _, row in grp.iterrows()])
            mp = profiles.mean(axis=0)
            stats.append({"Climate": climate, "Countries": len(grp),
 "Peak Hour": f"{np.argmax(mp):02d}:00",
 "Trough Hour": f"{np.argmin(mp):02d}:00",
 "Peak Factor": f"{mp.max():.3f}x",
 "Trough Factor": f"{mp.min():.3f}x",
 "Peak/Trough": f"{mp.max()/mp.min():.2f}x",
 "Night (00-05)": f"{mp[0:6].mean():.3f}x"})
        st.dataframe(pd.DataFrame(stats).set_index("Climate"), use_container_width=True)

    # ── All Countries ─────────────────────────────────────────────────────────
    else:
        st.caption(f"All {len(load_df)} countries — grey = background, colored = highlighted")
        fig = go.Figure()
        fig.add_hline(y=1.0, line_color="white", line_width=1, opacity=0.2)
        for _, row in load_df.iterrows():
            cname = str(row["Country"]).strip()
            if cname not in highlight:
                p = get_norm(row)
                fig.add_trace(go.Scatter(x=hour_labels, y=p, mode="lines",
                    line=dict(color="rgba(100,116,139,0.2)", width=1),
                    showlegend=False,
                    hovertemplate=f"{cname}<br>%{{y:.3f}}x<extra></extra>"))
        if show_mean:
            all_p = np.array([get_norm(row) for _, row in load_df.iterrows()])
            fig.add_trace(go.Scatter(x=hour_labels, y=all_p.mean(axis=0), name=" Global Mean",
                mode="lines", line=dict(color="#f59e0b", width=3)))
        hl_colors = px.colors.qualitative.Bold
        for i, c in enumerate(highlight):
            rows = load_df[load_df["Country"].str.strip() == c]
            if not rows.empty:
                p = get_norm(rows.iloc[0])
                fig.add_trace(go.Scatter(x=hour_labels, y=p, name=c, mode="lines",
                    line=dict(width=2.5, color=hl_colors[i % len(hl_colors)])))
        fig.update_layout(**dark_layout(520, f"All {len(load_df)} Country Load Profiles (Normalized)", ytitle="Load Factor (x avg)"))
        fig.update_layout(legend=dict(bgcolor="#1e293b", bordercolor="#334155"))
        fig.update_yaxes(range=[0.6, 1.55])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Heatmap — All Countries x 24 Hours")
        hm_df = load_df.copy()
        hm_df["Country"] = hm_df["Country"].str.strip()
        hm_df = hm_df.sort_values("Climate")
        z = np.array([get_norm(row) for _, row in hm_df.iterrows()])
        fig_hm = go.Figure(go.Heatmap(
            z=z, x=hour_labels, y=hm_df["Country"].tolist(),
            colorscale=[[0,"#1d4ed8"],[0.45,"#0f172a"],[0.55,"#0f172a"],[1,"#ef4444"]],
            zmid=1.0,
            colorbar=dict(title=dict(text="Load Factor", font=dict(color="white")), tickfont=dict(color="white")),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.3f}x<extra></extra>",
        ))
        fig_hm.update_layout(
            height=max(600, len(load_df)*14),
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            xaxis=dict(gridcolor="#1e293b", title="Hour"),
            yaxis=dict(tickfont=dict(size=8)),
            margin=dict(l=130, r=20, t=10, b=40),
        )
        st.plotly_chart(fig_hm, use_container_width=True)


st.sidebar.divider()
st.sidebar.caption("© 2026 GOAL Lab Undergraduate Research Team")
st.sidebar.caption("Solar: PVWatts V8 (pvlib)\nLoad: Country load profile dataset")
