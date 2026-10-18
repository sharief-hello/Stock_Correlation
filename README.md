# stock_corr

A small Python command-line app that measures and plots the correlation between two stocks. It pulls historical prices from Yahoo Finance using the [`yfinance`](https://github.com/ranaroussi/yfinance) library, prints a statistics report in the terminal and shows a 3-panel chart.

## Features

- Works with any ticker available on Yahoo Finance (US stocks, NSE/BSE stocks, indices, ETFs, crypto)
- Terminal report: Pearson correlation, Spearman rank correlation, R-squared, rolling-correlation range and a regression fit
- 3-panel chart:
  1. Price performance, both stocks rebased to 100
  2. Rolling correlation over time
  3. Scatter plot of returns with a regression line
- Preset look-back periods or a custom date range
- Save the chart to an image file, with optional headless mode (no window)
- Built-in ticker catalogue via `--stocks-available`

## Requirements

- Python 3.9 or newer
- Internet access to Yahoo Finance

## Installation

```bash
# (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Quick start

```bash
python stock_corr.py AAPL MSFT
```

Show the built-in list of tickers:

```bash
python stock_corr.py --stocks-available
```

Show help, including use-case examples:

```bash
python stock_corr.py --help
```

## Usage

```
python stock_corr.py TICKER1 TICKER2 [options]
```

Exactly two tickers are required (unless you use `--stocks-available`).

### Options

| Option | Description | Default |
|---|---|---|
| `--stocks-available` | Print the catalogue of ticker symbols, then exit | - |
| `--period` | Look-back period: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max` | `1y` |
| `--start YYYY-MM-DD` | Start date. Overrides `--period` | - |
| `--end YYYY-MM-DD` | End date. Only used together with `--start` | today |
| `--interval` | Data frequency: `1d`, `5d`, `1wk`, `1mo`, `3mo` | `1d` |
| `--window N` | Rolling-correlation window, in data points | `60` |
| `--use-prices` | Correlate raw prices instead of returns (not recommended) | off |
| `--save FILE` | Save the chart to a file, e.g. `chart.png` | - |
| `--no-show` | Do not open a chart window (useful with `--save`) | off |

## Use-case examples

```bash
# 1. Two US tech giants over the default 1 year
python stock_corr.py AAPL MSFT

# 2. Do oil majors move together? 5 years of data
python stock_corr.py XOM CVX --period 5y

# 3. Indian banks over a custom date range
python stock_corr.py HDFCBANK.NS ICICIBANK.NS --start 2023-01-01 --end 2024-12-31

# 4. Diversification check: gold vs equities, weekly data
python stock_corr.py SPY GLD --period 10y --interval 1wk

# 5. Does Bitcoin track the NASDAQ?
python stock_corr.py BTC-USD QQQ --period 2y --window 30

# 6. Pairs-trading research with a tighter 20-day rolling window
python stock_corr.py KO PEP --period 3y --window 20

# 7. Save the chart without opening a window (servers / scripts)
python stock_corr.py TCS.NS INFY.NS --period 3y --save tcs_infy.png --no-show

# 8. Correlate price levels instead of returns (can be misleading)
python stock_corr.py NVDA AMD --use-prices

# 9. List the built-in ticker catalogue
python stock_corr.py --stocks-available
```

## Ticker formats

Tickers follow Yahoo Finance conventions:

| Market | Format | Example |
|---|---|---|
| US stocks and ETFs | plain symbol | `AAPL`, `SPY` |
| NSE (India) | symbol + `.NS` | `RELIANCE.NS`, `TCS.NS` |
| BSE (India) | symbol + `.BO` | `RELIANCE.BO` |
| Indices | `^` prefix | `^GSPC`, `^NSEI` |
| Crypto | pair with currency | `BTC-USD`, `ETH-USD` |

The catalogue shown by `--stocks-available` is only a convenience list. Any ticker that works on [finance.yahoo.com](https://finance.yahoo.com) will work here.

## Reading the output

Example terminal report (values are illustrative):

```
============================================================
 Correlation report: AAA vs BBB
============================================================
 Date range         : 2025-10-01 -> 2026-09-15
 Data points        : 249 (1d, on returns)
 Pearson correlation: +0.6361  (strong positive)
 Spearman (rank)    : +0.6566
 R-squared          : 0.4046
 Rolling ( 60 pts)  : min +0.56 | mean +0.63 | max +0.70
 Regression         : BBB = -0.00037 + 0.6533 x AAA
============================================================
```

- **Pearson correlation** ranges from -1 (move in opposite directions) through 0 (unrelated) to +1 (move in lock-step).
- **Spearman** measures rank correlation and is less sensitive to outliers.
- **R-squared** is the share of one stock's variance explained by the other.
- **Rolling correlation** shows how stable the relationship is over time. A wide min-to-max range means the relationship changes a lot.
- **Regression** fits `stock2 = alpha + beta x stock1`, where beta is the slope of the fit.

### Why returns, not prices?

By default, correlation is computed on percentage returns. Price levels tend to trend upward over time, which makes almost any two stocks look correlated (spurious correlation). Returns are the standard way to measure whether two assets actually move together. `--use-prices` is available for comparison and prints a warning.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing dependency: yfinance` | Run `pip install -r requirements.txt` |
| `No data found for: XYZ` | Check the ticker on finance.yahoo.com. Indian stocks need `.NS` or `.BO` |
| `Only N overlapping data points` | Use a longer `--period`, or check that both tickers trade on overlapping dates |
| Rate-limit or connection errors | Wait a bit and retry. Yahoo Finance may throttle repeated requests |
| No window opens (server / SSH) | Add `--save chart.png --no-show` |

## Limitations

- Only daily and longer intervals are supported (no intraday).
- Data comes from Yahoo Finance via an unofficial library, so availability and accuracy are not guaranteed.
- Prices are adjusted for splits and dividends (`auto_adjust=True`).
- Correlation is not causation, and past correlation does not guarantee future correlation.

## Disclaimer

This tool is for education and research only and is not financial advice.
