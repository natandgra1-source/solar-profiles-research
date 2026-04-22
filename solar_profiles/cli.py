"""
cli.py — Command-line interface for solar-profiles.

Usage:
    solar-profiles countries
    solar-profiles profile "Germany"
    solar-profiles summary "Australia"
    solar-profiles top --n 10 --metric daily_energy
    solar-profiles compare "Germany" "France" "Japan"
    solar-profiles search "land"
    solar-profiles serve [--port 8000]
"""
from __future__ import annotations

import argparse
import json
import sys

from .core import SolarProfiles


def _banner():
    print("\033[93m" + "─" * 56)
    print("  🌞  Global Solar Profiles  │  Jan 1 │  197 Countries")
    print("─" * 56 + "\033[0m\n")


def cmd_countries(sp: SolarProfiles, args):
    countries = sp.countries
    print(f"  {len(countries)} countries available:\n")
    for i, c in enumerate(countries):
        print(f"  {i+1:>3}. {c}")


def cmd_profile(sp: SolarProfiles, args):
    country = " ".join(args.country)
    arr = sp.hourly_array(country)
    peak = arr.max()
    print(f"\n  📍 {country}  —  Jan 1 Local Solar Profile\n")
    for h in range(24):
        w = arr[h]
        bar_len = int(w / peak * 30) if peak > 0 else 0
        bar = "█" * bar_len
        print(f"  {h:02d}:00  {w:8.1f} W  \033[93m{bar}\033[0m")
    print(f"\n  Daily energy: {arr.sum():.0f} Wh")


def cmd_summary(sp: SolarProfiles, args):
    country = " ".join(args.country)
    s = sp.summary(country)
    print(f"\n  📍 {s['country']}\n")
    print(f"  Coordinates  :  {s['latitude']:.2f}°, {s['longitude']:.2f}°")
    print(f"  UTC offset   :  {s['utc_offset_h']:+d} h")
    print(f"  Daily energy :  {s['daily_energy_wh']:.0f} Wh")
    print(f"  Peak output  :  {s['peak_ac_w']:.0f} W  @ {s['peak_hour_local']:02d}:00")
    print(f"  Daylight hrs :  {s['daylight_hours']}")


def cmd_top(sp: SolarProfiles, args):
    df = sp.top_n(n=args.n, metric=args.metric)
    print(f"\n  🏆  Top {args.n} countries by {args.metric}\n")
    print(f"  {'Rank':<6} {'Country':<35} {'Value':>12}")
    print("  " + "─" * 55)
    for i, row in df.iterrows():
        country = row["Country"]
        val = row.iloc[1]
        print(f"  {i+1:<6} {country:<35} {val:>12.1f}")


def cmd_compare(sp: SolarProfiles, args):
    countries = args.countries
    df = sp.compare(countries)
    header = f"  {'Hour':<6}" + "".join(f"  {c[:14]:<14}" for c in countries)
    print(f"\n  ⚖️  Hourly comparison (W AC)\n")
    print(header)
    print("  " + "─" * (6 + 16 * len(countries)))
    for _, row in df.iterrows():
        h = int(row["Hour"])
        vals = "".join(f"  {row[c]:>14.1f}" for c in countries)
        print(f"  {h:02d}:00{vals}")


def cmd_search(sp: SolarProfiles, args):
    matches = sp.search(args.query)
    if matches:
        print(f"\n  Results for '{args.query}':\n")
        for m in matches:
            print(f"    • {m}")
    else:
        print(f"\n  No matches for '{args.query}'.")


def cmd_serve(sp: SolarProfiles, args):
    try:
        import uvicorn
    except ImportError:
        print("  uvicorn not installed. Run:  pip install uvicorn")
        sys.exit(1)
    print(f"\n  🚀  Starting API server on http://localhost:{args.port}")
    print(f"      Docs: http://localhost:{args.port}/docs\n")
    uvicorn.run("solar_profiles.api:app", host="0.0.0.0", port=args.port, reload=True)


def main():
    _banner()
    parser = argparse.ArgumentParser(
        prog="solar-profiles",
        description="Global PVWatts solar generation profiles CLI",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("countries", help="List all countries")

    p = sub.add_parser("profile", help="Print 24-hour chart for a country")
    p.add_argument("country", nargs="+", help="Country name (quote if multi-word)")

    p = sub.add_parser("summary", help="Summary stats for a country")
    p.add_argument("country", nargs="+")

    p = sub.add_parser("top", help="Top-N countries by metric")
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--metric", default="daily_energy",
                   choices=["daily_energy", "peak_ac", "daylight_hours"])

    p = sub.add_parser("compare", help="Compare multiple countries")
    p.add_argument("countries", nargs="+")

    p = sub.add_parser("search", help="Search country names")
    p.add_argument("query")

    p = sub.add_parser("serve", help="Start the REST API server")
    p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    sp = SolarProfiles()
    try:
        {
            "countries": cmd_countries,
            "profile": cmd_profile,
            "summary": cmd_summary,
            "top": cmd_top,
            "compare": cmd_compare,
            "search": cmd_search,
            "serve": cmd_serve,
        }[args.command](sp, args)
    except KeyError as e:
        print(f"\n  ❌  {e}\n")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
