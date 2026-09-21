"""
app.py - Solar & Load Profile Explorer
Sidebar navigation | Load Profiles | Solar Profiles
Visualize and download data for any country.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Solar & Load Profile Explorer",
    page_icon="",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; max-width: 960px; }
    h1 { font-size: 1.8rem !important; }
    section[data-testid="stSidebar"] { background: #0f172a; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 1rem; padding: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)

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

SOLAR_COUNTRIES = sorted(solar_df["Country"].tolist())
LOAD_COUNTRIES  = sorted(load_df["Country"].tolist())
HOURS = [f"{h:02d}:00" for h in range(24)]

SEASONS = {
    "Winter (Jan 1)": "Winter_Jan1",
    "Spring (Apr 1)": "Spring_Apr1",
    "Summer (Jul 1)": "Summer_Jul1",
    "Autumn (Oct 1)": "Autumn_Oct1",
}

def dark_chart(fig, height=380, ytitle=""):
    fig.update_layout(
        height=height,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="white"),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
        xaxis=dict(gridcolor="#1e293b", title="Hour (local time)"),
        yaxis=dict(gridcolor="#1e293b", title=ytitle),
        margin=dict(t=30, b=40, l=60, r=20),
    )
    return fig

# ── SIDEBAR NAVIGATION ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Solar & Load Explorer")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Load Profiles", "Solar Profiles", "Compare Countries"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Solar: PVWatts V8 (pvlib)")
    st.caption("Load: Country load profile dataset")
    st.caption("GOAL Lab Undergraduate Research")

st.title("Solar & Load Profile Explorer")
st.caption("Hourly load and solar generation profiles for countries worldwide.")
st.divider()

# ── PAGE: LOAD PROFILES ───────────────────────────────────────────────────────
if page == "Load Profiles":
    st.subheader("Electricity Load Profile")
    st.caption(f"Normalized hourly demand profiles for {len(LOAD_COUNTRIES)} countries. "
               "Values represent load relative to daily average (1.0 = average demand).")

    country_load = st.selectbox("Select country", LOAD_COUNTRIES, key="load_country")
    row = load_df[load_df["Country"] == country_load].iloc[0]
    profile = np.array([row[f"Hour {h}"] for h in range(24)])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Climate",     str(row["Climate"]).strip())
    col2.metric("Peak Hour",   f"{np.argmax(profile):02d}:00", f"{profile.max():.2f}x avg")
    col3.metric("Trough Hour", f"{np.argmin(profile):02d}:00", f"{profile.min():.2f}x avg")
    col4.metric("Population",  f"{row['Population']/1e6:.1f}M")

    fig = go.Figure()
    fig.add_hline(y=1.0, line_color="rgba(255,255,255,0.2)", line_width=1.5,
                  annotation_text="Average", annotation_font_color="rgba(255,255,255,0.4)",
                  annotation_position="top right")
    fig.add_trace(go.Scatter(
        x=HOURS, y=profile,
        mode="lines+markers",
        line=dict(color="#60a5fa", width=2.5),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(96,165,250,0.1)",
        name=country_load,
    ))
    dark_chart(fig, 360, "Load Factor (x daily avg)")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("**Download this country**")
    out_df = pd.DataFrame({"Hour": HOURS, "Load_Factor": profile.round(6)})
    csv_bytes = out_df.to_csv(index=False).encode("utf-8")
    filename = f"{country_load.replace(' ', '_')}_load_profile.csv"
    st.download_button(
        label=f"Download {country_load} load profile (CSV)",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    st.markdown("**Download all countries**")
    all_load = pd.DataFrame({
        "Country": load_df["Country"],
        "Climate": load_df["Climate"].str.strip(),
        "Population": load_df["Population"],
        "GDP": load_df["GDP"],
        **{f"{h:02d}:00": load_df[f"Hour {h}"] for h in range(24)},
    })
    st.download_button(
        label=f"Download all {len(LOAD_COUNTRIES)} countries load profiles (CSV)",
        data=all_load.to_csv(index=False).encode("utf-8"),
        file_name="all_countries_load_profiles.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── PAGE: SOLAR PROFILES ──────────────────────────────────────────────────────
elif page == "Solar Profiles":
    st.subheader("Solar Generation Profile")
    st.caption(f"PVWatts-equivalent AC power output for {len(SOLAR_COUNTRIES)} countries. "
               "4 kW DC system, standard module, clear-sky model.")

    col_a, col_b = st.columns(2)
    with col_a:
        country_solar = st.selectbox("Select country", SOLAR_COUNTRIES, key="solar_country")
    with col_b:
        season_label = st.selectbox("Season", list(SEASONS.keys()))

    season_key = SEASONS[season_label]
    srow = solar_df[solar_df["Country"] == country_solar].iloc[0]
    solar_h = np.array([srow[f"{season_key}_Hour_{h:02d}_W"] for h in range(24)])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Daily Energy",   f"{solar_h.sum()/1000:.1f} kWh")
    col2.metric("Peak Output",    f"{solar_h.max():.0f} W")
    col3.metric("Peak Hour",      f"{int(np.argmax(solar_h)):02d}:00")
    col4.metric("Daylight Hours", f"{int((solar_h > 0).sum())} h")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=HOURS, y=solar_h,
        marker=dict(
            color=solar_h,
            colorscale=[[0, "#1e293b"], [0.3, "#f59e0b"], [1, "#fef08a"]],
            showscale=False,
        ),
        name=f"{country_solar} - {season_label}",
    ))
    dark_chart(fig2, 360, "AC Power Output (W)")
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("**Download this profile**")
    out_solar = pd.DataFrame({"Hour": HOURS, "AC_Power_W": solar_h.round(2)})
    filename_solar = f"{country_solar.replace(' ', '_')}_{season_key}_solar_profile.csv"
    st.download_button(
        label=f"Download {country_solar} {season_label} solar profile (CSV)",
        data=out_solar.to_csv(index=False).encode("utf-8"),
        file_name=filename_solar,
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    st.markdown("**Download all seasons for this country**")
    all_seasons = pd.DataFrame({"Hour": HOURS})
    for slabel, skey in SEASONS.items():
        vals = [srow[f"{skey}_Hour_{h:02d}_W"] for h in range(24)]
        all_seasons[slabel] = np.round(vals, 2)
    filename_all = f"{country_solar.replace(' ', '_')}_all_seasons_solar.csv"
    st.download_button(
        label=f"Download {country_solar} all seasons (CSV)",
        data=all_seasons.to_csv(index=False).encode("utf-8"),
        file_name=filename_all,
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    st.markdown("**Download all countries**")
    hour_cols = {f"{season_key}_{h:02d}:00_W": solar_df[f"{season_key}_Hour_{h:02d}_W"] for h in range(24)}
    all_solar = pd.DataFrame({
        "Country":   solar_df["Country"],
        "Latitude":  solar_df["Latitude"],
        "Longitude": solar_df["Longitude"],
        "Season":    season_label,
        "Daily_kWh": (solar_df[[f"{season_key}_Hour_{h:02d}_W" for h in range(24)]].sum(axis=1) / 1000).round(2),
        **hour_cols,
    })
    st.download_button(
        label=f"Download all {len(SOLAR_COUNTRIES)} countries - {season_label} (CSV)",
        data=all_solar.to_csv(index=False).encode("utf-8"),
        file_name=f"all_countries_solar_{season_key}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── PAGE: COMPARE COUNTRIES ───────────────────────────────────────────────────
elif page == "Compare Countries":
    st.subheader("Compare Solar Profiles")
    st.caption("Normalized profiles (0-1 scale) let you compare generation shape and timing "
               "between countries regardless of absolute output differences.")

    col_s = st.columns(1)[0]
    with col_s:
        season_label_cmp = st.selectbox("Season", list(SEASONS.keys()), key="cmp_season")
    season_key_cmp = SEASONS[season_label_cmp]

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        country_a = st.selectbox("Country A", SOLAR_COUNTRIES, key="cmp_a")
    with col_c2:
        default_b = min(SOLAR_COUNTRIES.index(country_a) + 1, len(SOLAR_COUNTRIES) - 1)
        country_b = st.selectbox("Country B", SOLAR_COUNTRIES, index=default_b, key="cmp_b")

    row_a = solar_df[solar_df["Country"] == country_a].iloc[0]
    row_b = solar_df[solar_df["Country"] == country_b].iloc[0]

    h_a_raw = np.array([row_a[f"{season_key_cmp}_Hour_{h:02d}_W"] for h in range(24)], dtype=float)
    h_b_raw = np.array([row_b[f"{season_key_cmp}_Hour_{h:02d}_W"] for h in range(24)], dtype=float)

    # Normalize to 0-1 by dividing each country by its own daily peak
    peak_a = h_a_raw.max()
    peak_b = h_b_raw.max()
    h_a_norm = h_a_raw / peak_a if peak_a > 0 else h_a_raw
    h_b_norm = h_b_raw / peak_b if peak_b > 0 else h_b_raw

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatter(
        x=HOURS, y=h_a_norm,
        name=f"{country_a}  (peak {peak_a:.0f} W)",
        mode="lines",
        line=dict(color="#f59e0b", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.12)",
    ))
    fig_cmp.add_trace(go.Scatter(
        x=HOURS, y=h_b_norm,
        name=f"{country_b}  (peak {peak_b:.0f} W)",
        mode="lines",
        line=dict(color="#60a5fa", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(96,165,250,0.12)",
    ))
    dark_chart(fig_cmp, 380, "Normalized Output (0 = none, 1 = peak)")
    st.plotly_chart(fig_cmp, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric(f"{country_a} daily energy", f"{h_a_raw.sum()/1000:.1f} kWh", f"Peak: {peak_a:.0f} W")
    col2.metric(f"{country_b} daily energy", f"{h_b_raw.sum()/1000:.1f} kWh", f"Peak: {peak_b:.0f} W")

    st.divider()
    st.markdown("**Download comparison CSV**")
    cmp_df = pd.DataFrame({
        "Hour":               HOURS,
        f"{country_a}_W":     h_a_raw.round(2),
        f"{country_b}_W":     h_b_raw.round(2),
        f"{country_a}_norm":  h_a_norm.round(4),
        f"{country_b}_norm":  h_b_norm.round(4),
    })
    fname_cmp = f"{country_a.replace(' ','_')}_vs_{country_b.replace(' ','_')}_{season_key_cmp}.csv"
    st.download_button(
        label="Download comparison CSV (raw + normalized)",
        data=cmp_df.to_csv(index=False).encode("utf-8"),
        file_name=fname_cmp,
        mime="text/csv",
        use_container_width=True,
    )

st.divider()
st.caption("2026 GOAL Lab Undergraduate Research Team  -  Solar: PVWatts V8 (pvlib)  -  Load: Country load profile dataset")
