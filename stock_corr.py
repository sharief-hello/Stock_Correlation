#!/usr/bin/env python3
"""
stock_corr.py - Plot the correlation between two stocks in your terminal workflow.

Pulls historical prices from Yahoo Finance via the `yfinance` library, prints
correlation statistics in the terminal and shows a 3-panel chart:
  1. Normalised price performance (both stocks rebased to 100)
  2. Rolling correlation of daily returns
  3. Scatter plot of daily returns with a regression line

Install dependencies:
    pip install yfinance pandas matplotlib
"""

import argparse
import sys
import textwrap

# --------------------------------------------------------------------------- #
# Catalogue shown by --stocks-available.
# This is only a convenience list: ANY valid Yahoo Finance ticker will work.
# --------------------------------------------------------------------------- #
STOCKS_AVAILABLE = {
    "US - Technology": {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet (Google)",
        "AMZN": "Amazon",
        "META": "Meta Platforms",
        "NVDA": "NVIDIA",
        "TSLA": "Tesla",
        "AMD": "Advanced Micro Devices",
        "INTC": "Intel",
        "NFLX": "Netflix",
    },
    "US - Finance": {
        "JPM": "JPMorgan Chase",
        "BAC": "Bank of America",
        "GS": "Goldman Sachs",
        "V": "Visa",
        "MA": "Mastercard",
    },
    "US - Energy & Consumer": {
        "XOM": "Exxon Mobil",
        "CVX": "Chevron",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "WMT": "Walmart",
    },
    "India - NSE (suffix .NS)": {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "SBIN.NS": "State Bank of India",
        "ITC.NS": "ITC",
        "LT.NS": "Larsen & Toubro",
        "BHARTIARTL.NS": "Bharti Airtel",
        "WIPRO.NS": "Wipro",
    },
    "Indices, ETFs & Crypto": {
        "^GSPC": "S&P 500 index",
        "^IXIC": "NASDAQ Composite",
        "^NSEI": "NIFTY 50",
        "^BSESN": "BSE SENSEX",
        "SPY": "S&P 500 ETF",
        "QQQ": "NASDAQ-100 ETF",
        "GLD": "Gold ETF",
        "BTC-USD": "Bitcoin (USD)",
        "ETH-USD": "Ethereum (USD)",
    },
}

VALID_PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
VALID_INTERVALS = ["1d", "5d", "1wk", "1mo", "3mo"]

EXAMPLES = """\
use case examples:

  1. Basic comparison of two US tech giants over the default 1 year:
       python stock_corr.py AAPL MSFT

  2. Do oil majors move together? Look at 5 years of data:
       python stock_corr.py XOM CVX --period 5y

  3. Indian banks, custom date range:
       python stock_corr.py HDFCBANK.NS ICICIBANK.NS --start 2023-01-01 --end 2024-12-31

  4. Diversification check - is gold really uncorrelated with equities?
       python stock_corr.py SPY GLD --period 10y --interval 1wk

  5. Crypto vs tech: does Bitcoin track the NASDAQ?
       python stock_corr.py BTC-USD QQQ --period 2y --window 30

  6. Pairs-trading research - use a tighter 20-day rolling window:
       python stock_corr.py KO PEP --period 3y --window 20

  7. Save the chart to a file without opening a window (servers / scripts):
       python stock_corr.py TCS.NS INFY.NS --period 3y --save tcs_infy.png --no-show

  8. Correlate price levels instead of returns (can be misleading - see notes):
       python stock_corr.py NVDA AMD --use-prices

  9. List the built-in ticker catalogue:
       python stock_corr.py --stocks-available

notes:
  * By default correlation is computed on periodic RETURNS, not raw prices.
    Price levels trend over time, which inflates correlation (spurious
    correlation); returns are the standard way to measure co-movement.
  * Correlation ranges from -1 (move in opposite directions) through 0
    (unrelated) to +1 (move in lock-step).
  * Any ticker that works on https://finance.yahoo.com is accepted, not only
    those listed by --stocks-available.
  * Past correlation does not guarantee future correlation. This tool is for
    education and research, not financial advice.
"""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock_corr.py",
        description=(
            "Plot and measure the correlation between two stocks using "
            "historical data pulled from Yahoo Finance (yfinance)."
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        metavar="TICKER",
        help="Exactly two Yahoo Finance tickers, e.g. AAPL MSFT",
    )
    parser.add_argument(
        "--stocks-available",
        action="store_true",
        help="Show the catalogue of ticker symbols that can be pulled, then exit",
    )
    parser.add_argument(
        "--period",
        default="1y",
        choices=VALID_PERIODS,
        help="Look-back period (default: 1y). Ignored if --start is given",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        help="Start date (overrides --period)",
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        help="End date (default: today). Only used with --start",
    )
    parser.add_argument(
        "--interval",
        default="1d",
        choices=VALID_INTERVALS,
        help="Data frequency (default: 1d)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=60,
        metavar="N",
        help="Rolling-correlation window in data points (default: 60)",
    )
    parser.add_argument(
        "--use-prices",
        action="store_true",
        help="Correlate raw prices instead of returns (not recommended)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save the chart to FILE (e.g. chart.png)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open a chart window (useful with --save)",
    )
    return parser


def print_available() -> None:
    print("\nStocks available (built-in catalogue)")
    print("=" * 60)
    for group, items in STOCKS_AVAILABLE.items():
        print(f"\n{group}")
        print("-" * len(group))
        for ticker, name in items.items():
            print(f"  {ticker:<16}{name}")
    print(
        "\nTip: any ticker valid on Yahoo Finance also works, e.g. "
        "'python stock_corr.py ZOMATO.NS TSLA'.\n"
    )


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def fetch_prices(t1, t2, args):
    import pandas as pd
    import yfinance as yf

    kwargs = dict(
        tickers=[t1, t2],
        interval=args.interval,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )
    if args.start:
        kwargs["start"] = args.start
        if args.end:
            kwargs["end"] = args.end
    else:
        kwargs["period"] = args.period

    raw = yf.download(**kwargs)
    if raw is None or raw.empty:
        raise RuntimeError("No data returned from Yahoo Finance. Check tickers/dates.")

    close = raw["Close"]
    if isinstance(close, pd.Series):  # defensive: single column result
        close = close.to_frame()

    missing = [t for t in (t1, t2) if t not in close.columns or close[t].dropna().empty]
    if missing:
        raise RuntimeError(
            f"No data found for: {', '.join(missing)}. "
            "Check the ticker symbols (run --stocks-available for examples)."
        )

    close = close[[t1, t2]].dropna()
    if len(close) < 10:
        raise RuntimeError(
            f"Only {len(close)} overlapping data points - too few to compute a "
            "meaningful correlation. Try a longer period."
        )
    return close


# --------------------------------------------------------------------------- #
# Stats + plotting
# --------------------------------------------------------------------------- #
def strength_label(r: float) -> str:
    a = abs(r)
    if a >= 0.8:
        s = "very strong"
    elif a >= 0.6:
        s = "strong"
    elif a >= 0.4:
        s = "moderate"
    elif a >= 0.2:
        s = "weak"
    else:
        s = "negligible"
    direction = "positive" if r > 0 else "negative" if r < 0 else ""
    return f"{s} {direction}".strip()


def analyse_and_plot(prices, t1, t2, args):
    import matplotlib

    if args.no_show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    series = prices if args.use_prices else prices.pct_change().dropna()
    basis = "prices" if args.use_prices else "returns"

    corr = series[t1].corr(series[t2])
    spearman = series[t1].corr(series[t2], method="spearman")
    window = max(5, min(args.window, len(series) - 1))
    rolling = series[t1].rolling(window).corr(series[t2]).dropna()

    # Linear regression (beta of t2 relative to t1 ... t2 = alpha + beta * t1)
    beta, alpha = np.polyfit(series[t1], series[t2], 1)

    # ---- terminal report -------------------------------------------------- #
    print("\n" + "=" * 60)
    print(f" Correlation report: {t1} vs {t2}")
    print("=" * 60)
    print(f" Date range         : {prices.index[0].date()} -> {prices.index[-1].date()}")
    print(f" Data points        : {len(series)} ({args.interval}, on {basis})")
    print(f" Pearson correlation: {corr:+.4f}  ({strength_label(corr)})")
    print(f" Spearman (rank)    : {spearman:+.4f}")
    print(f" R-squared          : {corr ** 2:.4f}")
    print(f" Rolling ({window:>3} pts)  : min {rolling.min():+.2f} | "
          f"mean {rolling.mean():+.2f} | max {rolling.max():+.2f}")
    print(f" Regression         : {t2} = {alpha:+.5f} + {beta:.4f} x {t1}")
    if args.use_prices:
        print("\n Warning: price-level correlation is often spurious because prices "
              "trend.\n Re-run without --use-prices for return-based correlation.")
    print("=" * 60 + "\n")

    # ---- chart ------------------------------------------------------------ #
    fig = plt.figure(figsize=(13, 8.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])
    ax_price = fig.add_subplot(gs[0, :])
    ax_roll = fig.add_subplot(gs[1, 0])
    ax_scat = fig.add_subplot(gs[1, 1])

    rebased = prices / prices.iloc[0] * 100
    ax_price.plot(rebased.index, rebased[t1], label=t1, linewidth=1.6)
    ax_price.plot(rebased.index, rebased[t2], label=t2, linewidth=1.6)
    ax_price.set_title("Price performance (rebased to 100)")
    ax_price.set_ylabel("Rebased price")
    ax_price.legend(loc="upper left")
    ax_price.grid(alpha=0.3)

    ax_roll.plot(rolling.index, rolling.values, color="tab:purple", linewidth=1.4)
    ax_roll.axhline(corr, color="tab:red", linestyle="--", linewidth=1,
                    label=f"Overall: {corr:+.2f}")
    ax_roll.axhline(0, color="grey", linewidth=0.8)
    ax_roll.set_ylim(-1.05, 1.05)
    ax_roll.set_title(f"Rolling {window}-point correlation of {basis}")
    ax_roll.legend(loc="lower left")
    ax_roll.grid(alpha=0.3)

    ax_scat.scatter(series[t1], series[t2], s=12, alpha=0.5)
    xs = np.linspace(series[t1].min(), series[t1].max(), 100)
    ax_scat.plot(xs, alpha + beta * xs, color="tab:red", linewidth=1.6,
                 label=f"fit (beta={beta:.2f})")
    ax_scat.set_xlabel(f"{t1} {basis}")
    ax_scat.set_ylabel(f"{t2} {basis}")
    ax_scat.set_title(f"Scatter of {basis} (r = {corr:+.3f})")
    ax_scat.legend(loc="upper left")
    ax_scat.grid(alpha=0.3)

    fig.suptitle(f"Correlation: {t1} vs {t2}", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    if args.save:
        fig.savefig(args.save, dpi=150)
        print(f"Chart saved to {args.save}")
    if not args.no_show:
        plt.show()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.stocks_available:
        print_available()
        return 0

    if len(args.tickers) != 2:
        parser.error(
            "exactly two tickers are required, e.g. 'python stock_corr.py AAPL MSFT' "
            "(use --stocks-available to see ticker examples)"
        )

    t1, t2 = (t.upper() for t in args.tickers)
    if t1 == t2:
        parser.error("please provide two different tickers")

    try:
        import yfinance  # noqa: F401
        import pandas  # noqa: F401
        import matplotlib  # noqa: F401
    except ImportError as exc:
        print(f"Missing dependency: {exc.name}\n"
              "Install with: pip install yfinance pandas matplotlib", file=sys.stderr)
        return 1

    print(f"Fetching {t1} and {t2} from Yahoo Finance...")
    try:
        prices = fetch_prices(t1, t2, args)
        analyse_and_plot(prices, t1, t2, args)
    except RuntimeError as exc:
        print(textwrap.fill(f"Error: {exc}", 78), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
