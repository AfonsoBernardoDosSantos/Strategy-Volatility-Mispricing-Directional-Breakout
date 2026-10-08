
# Code was produced with assistance of Claude
# Model inputs should match throughout all 3 sections. It's handy to search for mean and change mean to AR, Zero or Constant and add or remove "lags" based on what was observed on the LB and past returns section.

import warnings
import statsmodels.api as sm
from arch import arch_model
import itertools
from tqdm import tqdm
from arch.bootstrap import MCS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from arch.unitroot import VarianceRatio
from scipy.stats import norm

ticker = "MRNA"

df = yf.download(ticker, start="2021-09-04", end="2026-10-08", auto_adjust=False)

df_filter = df[["Adj Close"]].copy()
df_filter.rename(columns={"Adj Close": "price_t"}, inplace=True)
df_filter["returns"] = df_filter["price_t"].pct_change()
df_filter.dropna(inplace=True)
df_filter["log_returns"] = np.log(1 + df_filter["returns"])

# Running a Ljung-box test to test residual autocorrelation

max_lag = 10

lb_test = acorr_ljungbox(df_filter["log_returns"], lags=range(1, max_lag + 1), boxpierce=False)
acf_values = acf(df_filter["log_returns"], nlags=max_lag)[1:max_lag + 1]  # skip lag 0 (always 1.0)

lb_table = pd.DataFrame({
    "Lag": range(1, max_lag + 1),
    "Autocorrelation": acf_values,
    "Ljung-Box Stat": lb_test["lb_stat"].values,
    "p-value": lb_test["lb_pvalue"].values,
    "Significant (5%)": lb_test["lb_pvalue"].values < 0.05
})

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(f"\nLjung-Box Test for Residual Autocorrelation — {ticker} Log Returns")
print(lb_table.to_string(index=False))

# ACF / PACF plots

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

plot_acf(df_filter["log_returns"], lags=40, ax=axes[0])
axes[0].set_title(f"{ticker} Log Returns — ACF")

plot_pacf(df_filter["log_returns"], lags=40, ax=axes[1], method="ywm")
axes[1].set_title(f"{ticker} Log Returns — PACF")

plt.tight_layout()
plt.show()

avg_daily_return = df_filter["returns"].mean()
avg_daily_log_return = df_filter["log_returns"].mean()

print(f"\nAverage daily return ({ticker}, simple): {avg_daily_return:.4%}")
print(f"Average daily return ({ticker}, log): {avg_daily_log_return:.4%}")

# Defining the in-sample and out-of-sample period

total_obs = len(df_filter["log_returns"])
breakpoint = int(total_obs * 0.7)

returns = df_filter["log_returns"].astype(float).squeeze().dropna()

in_sample = returns.iloc[:breakpoint]
out_sample = returns.iloc[breakpoint:]  # RUN UNTIL HERE THEN STOP

# Applying the GARCH models (GARCH (p,q), GJR-GARCH(p,q), EGARCH(p,q), PGARCH(p,q), FIGARCH(p,q)) to the in-sample period

p_range = range(1, 4)
q_range = range(1, 4)
param_combinations = list(itertools.product(p_range, q_range))

model_specs = {
    "GARCH":      {"vol": "GARCH"},
    "GJR-GARCH":  {"vol": "GARCH", "o": 1},
    "EGARCH":     {"vol": "EGARCH", "o": 1},
    "APARCH":     {"vol": "APARCH", "o": 1},
    "FIGARCH":    {"vol": "FIGARCH"},
}

model_results = []
in_sample_scaled = in_sample * 100  # scale once, reuse across all fits

for model_name, spec in model_specs.items():
    for p, q in tqdm(param_combinations, desc=f"Fitting {model_name}"):
        try:
            garch_model = arch_model(
                in_sample_scaled,
                mean="Constant",# IF AUTOCORRLEATION IS FOUND, INPUT AR IN MEAN AND ADD A LINE BELOW, LAGS=X
                p=p,
                q=q,
                dist="Skewt",
                rescale=False,
                **spec
            )
            fitted_model = garch_model.fit(disp="off")

            model_results.append({
                "Model": model_name,
                "p": p,
                "q": q,
                "AIC": fitted_model.aic,
                "BIC": fitted_model.bic,
                "Log-Likelihood": fitted_model.loglikelihood
            })
        except Exception as e:
            print(f"{model_name} p={p}, q={q} failed: {e}")
            continue

results_df = pd.DataFrame(model_results)
sorted_results = results_df.sort_values(by="BIC", ascending=True).reset_index(drop=True)
print(sorted_results)
best_per_model = results_df.loc[results_df.groupby("Model")["BIC"].idxmin()]
print(best_per_model.sort_values("BIC"))

# Rolling Backtest throughout the out of sample period, where forecasted volatility is compared with sqd daily returns

def rolling_forecast(returns_full, breakpoint, spec, p, q,
                      refit_every=5, dist="Skewt", desc="Rolling forecast"):
    forecasts = []
    n_total = len(returns_full)
    fitted_model = None

    for t in tqdm(range(breakpoint, n_total), desc=desc):
        if (t - breakpoint) % refit_every == 0 or fitted_model is None:
            window_data = returns_full.iloc[:t]
            try:
                garch_model = arch_model(
                    window_data,
                    mean="Constant",
                    p=p,
                    q=q,
                    dist=dist,
                    rescale=False,
                    **spec
                )
                fitted_model = garch_model.fit(disp="off")
            except Exception:
                forecasts.append(np.nan)
                continue

        try:
            fc = fitted_model.forecast(horizon=1, reindex=False)
            forecast_variance = fc.variance.values[-1, 0]
        except Exception:
            forecast_variance = np.nan

        forecasts.append(forecast_variance)

    return pd.Series(forecasts, index=returns_full.index[breakpoint:n_total])

# Run rolling backtest for each model, using its best (p,q) from the horse-race

returns_scaled = returns * 100  # full series, same scaling as earlier steps

backtest_results = {}
for idx, best_row in best_per_model.iterrows():
    model_name = best_row["Model"]  # correctly grab the actual name
    spec = model_specs[model_name]
    p, q = int(best_row["p"]), int(best_row["q"])

    print(f"Running rolling backtest for {model_name}(p={p}, q={q})...")
    backtest_results[model_name] = rolling_forecast(
        returns_scaled, breakpoint, spec, p, q,
        refit_every=1, desc=f"Rolling backtest: {model_name}"
    )

# Realized variance: squared daily out-of-sample returns
realized_variance = (returns_scaled.iloc[breakpoint:]) ** 2

comparison_df = pd.DataFrame({"Realized": realized_variance})
for model_name, forecast_series in backtest_results.items():
    comparison_df[model_name] = forecast_series

# Compute MSE per model
mse_results = {}
for model_name in backtest_results:
    valid = comparison_df[["Realized", model_name]].dropna()
    mse = np.mean((valid["Realized"] - valid[model_name]) ** 2)
    mse_results[model_name] = mse

mse_df = pd.DataFrame.from_dict(mse_results, orient="index", columns=["MSE"])
mse_df = mse_df.sort_values("MSE").reset_index().rename(columns={"index": "Model"})

print(mse_df)

# Choosing best models through model confidence set

print(best_per_model)
print(len(best_per_model))

losses = pd.DataFrame({
    model_name: (comparison_df["Realized"] - comparison_df[model_name]) ** 2
    for model_name in backtest_results
}).dropna()

mcs = MCS(losses, size=0.01)  # size = significance level, 0.10 is common in the literature
mcs.compute()

print("Models included in the Superior Set of Models (SSM):")
print(mcs.included)

print("\nModels excluded (statistically dominated):")
print(mcs.excluded)

print("\nP-values for each model:")
print(mcs.pvalues) # RUN UNTIL HERE THEN STOP!!!

# Extracting option data from Interactive brokers/Yahoo finance + IV calcs

# Choose model based on MCS results

chosen_model = "APARCH" # CHANGE THIS AS PER MCS AND MSE RESULTS

chosen_row = best_per_model[best_per_model["Model"] == chosen_model].iloc[0]
chosen_spec = model_specs[chosen_model]
chosen_p, chosen_q = int(chosen_row["p"]), int(chosen_row["q"])

print(f"Selected model: {chosen_model}(p={chosen_p}, q={chosen_q})")


# Risk-free rate

fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1"
rf_data = pd.read_csv(fred_url, parse_dates=["observation_date"]).rename(columns={"DGS1": "rate"}).dropna()
risk_free_rate = rf_data["rate"].iloc[-1] / 100
print(f"1Y Treasury yield: {risk_free_rate:.4%}")


# Spot price

ticker_symbol = ticker
stock = yf.Ticker(ticker_symbol)
spot_price = stock.history(period="1d")["Close"].iloc[-1]
print(f"{ticker} spot price: {spot_price:.2f}")

# Valid expiries (< 2 months)

today = datetime.now()
max_days = 60
all_expiries = stock.options

valid_expiries = [
    exp for exp in all_expiries
    if 0 < (datetime.strptime(exp, "%Y-%m-%d") - today).days < max_days
]
print(f"Valid expirations (<{max_days} days): {valid_expiries}")
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega


# ATM + OTM implied vol per expiry

n_otm_each_side = 2

atm_otm_results = []
for expiry in valid_expiries:
    opt_chain = stock.option_chain(expiry)
    T_days = (datetime.strptime(expiry, "%Y-%m-%d") - today).days
    T_years = T_days / 365.0

    for option_type, chain_df, flag in [("Call", opt_chain.calls, "c"), ("Put", opt_chain.puts, "p")]:
        chain_df = chain_df.copy().sort_values("strike").reset_index(drop=True)
        chain_df["dist_to_spot"] = (chain_df["strike"] - spot_price).abs()
        atm_idx = chain_df["dist_to_spot"].idxmin()

        if option_type == "Call":
            lower_bound = atm_idx
            upper_bound = min(len(chain_df) - 1, atm_idx + n_otm_each_side)
        else:
            lower_bound = max(0, atm_idx - n_otm_each_side)
            upper_bound = atm_idx

        selected = chain_df.iloc[lower_bound:upper_bound + 1]

        for _, row in selected.iterrows():
            strike = row["strike"]
            bid, ask = (row["bid"], row["ask"]) if row["bid"] > 0 else (row["lastPrice"], row["lastPrice"])

            if bid <= 0 or ask <= 0:
                continue

            mid_price = (bid + ask) / 2

            if row.name == atm_idx:
                moneyness = "ATM"
            elif option_type == "Call":
                moneyness = "OTM" if strike > spot_price else "ITM"
            else:
                moneyness = "OTM" if strike < spot_price else "ITM"

            try:
                iv = implied_volatility(
                    price=mid_price, S=spot_price, K=strike,
                    t=T_years, r=risk_free_rate, flag=flag
                )
                if np.isnan(iv) or iv <= 0:
                    print(f"Skipping {expiry} {option_type} strike {strike}: IV solver returned invalid value ({iv})")
                    continue
            except Exception as e:
                print(f"IV calc failed for {expiry} {option_type}, strike {strike}: {e}")
                continue
            atm_otm_results.append({
                "Expiry": expiry,
                "OptionType": option_type,
                "Strike": strike,
                "Spot": spot_price,
                "Moneyness": moneyness,
                "Bid": bid,
                "Ask": ask,
                "MidPrice": mid_price,
                "Volume": row["volume"],
                "OpenInterest": row["openInterest"],
                "T (days)": T_days,
                "T (years)": T_years,
                "ImpliedVol": iv
            })

iv_df = pd.DataFrame(atm_otm_results)

print(f"Rows before NaN filter: {len(iv_df)}")
iv_df = iv_df.dropna(subset=["ImpliedVol"])
iv_df = iv_df[iv_df["ImpliedVol"] > 0]
print(f"Rows after NaN filter: {len(iv_df)}")

print("\nATM + OTM Implied Volatilities (Calls & Puts):")
print(iv_df)


# Refit chosen GARCH-family model on sample

full_returns_scaled = returns * 100

final_model = arch_model(
    full_returns_scaled,
    mean="Constant",
    p=chosen_p, q=chosen_q,
    dist="Skewt",
    rescale=False,
    **chosen_spec
)
final_fit = final_model.fit(disp="off")
print(f"\nRefit {chosen_model} on full sample.")

# Multi-step-ahead GARCH forecast, matched to each option's TTM

def garch_annualized_vol_distribution(fitted_model, horizon_days, trading_days_per_year=252, n_sims=10000):
    fc = fitted_model.forecast(
        horizon=horizon_days,
        method="simulation",
        simulations=n_sims,
        reindex=False
    )
    sim_variances = fc.simulations.variances[-1]
    total_variance_per_path = sim_variances.sum(axis=1)
    avg_daily_variance_per_path = total_variance_per_path / horizon_days
    annualized_vol_per_path = np.sqrt(avg_daily_variance_per_path * trading_days_per_year) / 100
    return annualized_vol_per_path

# Significance test + Greeks, for every strike/expiry/type

significance_results = []

for _, row in iv_df.iterrows():
    T_days_calendar = row["T (days)"]
    T_days_trading = max(1, int(round(T_days_calendar * 5 / 7)))
    T_years = row["T (years)"]
    observed_iv = row["ImpliedVol"]
    strike = row["Strike"]
    option_price = row["MidPrice"]
    option_type = row["OptionType"]
    flag = "c" if option_type == "Call" else "p"

    sim_vols = garch_annualized_vol_distribution(final_fit, T_days_trading, n_sims=10000)

    proportion_below = np.mean(sim_vols < observed_iv)

    if proportion_below <= 0.05:
        finding = "Option is undervalued"
    elif proportion_below >= 0.95:
        finding = "Option is overvalued"
    else:
        finding = "Not significant"

    significant = proportion_below <= 0.05 or proportion_below >= 0.95

    # Greeks
    option_delta = delta(flag=flag, S=spot_price, K=strike, t=T_years, r=risk_free_rate, sigma=observed_iv)
    option_gamma = gamma(flag=flag, S=spot_price, K=strike, t=T_years, r=risk_free_rate, sigma=observed_iv)
    option_theta = theta(flag=flag, S=spot_price, K=strike, t=T_years, r=risk_free_rate, sigma=observed_iv)
    option_vega  = vega(flag=flag,  S=spot_price, K=strike, t=T_years, r=risk_free_rate, sigma=observed_iv)

    difference = (sim_vols.mean() - observed_iv) * 100
    significance_results.append({
        "Expiry": row["Expiry"],
        "OptionType": option_type,
        "T (days)": T_days_calendar,
        "Strike": strike,
        "Moneyness": row["Moneyness"],
        "Bid": row["Bid"],
        "Ask": row["Ask"],
        "OptionPrice": option_price,
        "SpreadPct": (row["Ask"] - row["Bid"]) / option_price if option_price > 0 else np.nan,
        "Volume": row["Volume"],
        "OpenInterest": row["OpenInterest"],
        "ImpliedVol": observed_iv,
        "Delta": option_delta,
        "Gamma": option_gamma,
        "Theta": option_theta,
        "Vega": option_vega,
        "GARCH_MeanForecast": sim_vols.mean(),
        "ProportionBelow": proportion_below,
        "Significant": significant,
        "Finding": finding,
        "Difference": difference,
        "Vega*Difference": difference * option_vega,
        "Return": (difference * option_vega) / option_price
    })

significance_df = pd.DataFrame(significance_results)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(significance_df)

# Export to Excel
output_path = "garch_iv_significance_test.xlsx"
significance_df.to_excel(output_path, index=False)
print(f"\nExported results to: {output_path}")

# MOMENTUM CALCS

if "df_filter" in locals() and "log_returns" in df_filter.columns:
    returns_series = df_filter["log_returns"].squeeze().astype(float).dropna()
elif "returns" in locals():
    returns_series = returns.squeeze().astype(float).dropna()
else:
    raise NameError("Neither 'df_filter[\"log_returns\"]' nor 'returns' was found in memory. Please run the data download block first.")


# Build Lag Matrix (1 to 60 days)

n_lags = 60
momentum_df = pd.DataFrame({"r_t": returns_series})

for lag in range(1, n_lags + 1):
    momentum_df[f"r_t-{lag}"] = returns_series.shift(lag)

momentum_df = momentum_df.dropna()

X = momentum_df.drop(columns="r_t")
X = sm.add_constant(X)
y = momentum_df["r_t"]

# Fit OLS with HAC

hac_maxlags = int(np.ceil(4 * (len(y) / 100) ** (2 / 9)))

momentum_model = sm.OLS(y, X).fit(
    cov_type="HAC",
    cov_kwds={"maxlags": hac_maxlags}
)


# Results Table

momentum_results = pd.DataFrame({
    "Ticker": ticker if "ticker" in locals() else "N/A",
    "Lag": ["const"] + [f"Lag {lag}" for lag in range(1, n_lags + 1)],
    "Coefficient": momentum_model.params.values,
    "HAC Std Error": momentum_model.bse.values,
    "HAC t-stat": momentum_model.tvalues.values,
    "HAC p-value": momentum_model.pvalues.values
})

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print(f"\n============================================================")
print(f"HAC Momentum Regression Results — {ticker if 'ticker' in locals() else 'Series'} (Lags 1 to {n_lags})")
print(f"Covariance Type: Newey-West HAC | Truncation Lag (maxlags): {hac_maxlags}")
print(f"============================================================")
print(momentum_results.to_string(index=False))

significant_lags = momentum_results[
    (momentum_results["HAC p-value"] < 0.05) & (momentum_results["Lag"] != "const")
]

print(f"\nStatistically significant lags under HAC (p < 0.05): {len(significant_lags)}")
if not significant_lags.empty:
    print(significant_lags.to_string(index=False))
else:
    print("None found.")


# Export to Excel

out_name = f"{ticker}_HAC_momentum_regression.xlsx" if "ticker" in locals() else "HAC_momentum_regression.xlsx"
momentum_results.to_excel(out_name, index=False)
print(f"\nExported HAC momentum regression results to {out_name}")


# LO-MACKINLAY VARIANCE RATIO TEST TRAILING 1-YEAR WINDOW

def run_variance_ratio_analysis(ticker_name, price_series, lookback_days=252, max_k=60, step=5):
    # Slice to trailing lookback window (252 trading days = 1 financial year)
    clean_prices = price_series.astype(float).dropna()
    if lookback_days is not None:
        clean_prices = clean_prices.iloc[-lookback_days:]

    start_date = clean_prices.index[0].strftime("%Y-%m-%d") if hasattr(clean_prices.index[0], "strftime") else "Start"
    end_date = clean_prices.index[-1].strftime("%Y-%m-%d") if hasattr(clean_prices.index[-1], "strftime") else "End"
    n_obs = len(clean_prices)

    log_prices = np.log(clean_prices)
    k_horizons = list(range(step, max_k + step, step))

    vr_records = []

    for k in k_horizons:
        # robust=True applies heteroskedasticity correction
        vr_test = VarianceRatio(log_prices, lags=k, trend="c", robust=True)

        vr_val = vr_test.vr
        stat = vr_test.stat
        p_val = vr_test.pvalue

        if p_val < 0.05:
            regime = "Persistent Momentum (Trending)" if vr_val > 1.0 else "Mean-Reverting"
        else:
            regime = "Random Walk (No Trend Edge)"

        vr_records.append({
            "Ticker": ticker_name,
            "Lookback Window": f"{n_obs} Days ({start_date} to {end_date})",
            "Horizon (k days)": k,
            "Variance Ratio VR(k)": vr_val,
            "Z2 Stat (Robust)": stat,
            "p-value": p_val,
            "Significant (5%)": p_val < 0.05,
            "Regime": regime
        })

    return pd.DataFrame(vr_records), k_horizons, start_date, end_date, n_obs


# Run test on trailing 1-year (252 trading days)
lookback_window = 252

vr_results, k_horizons, start_dt, end_dt, obs_count = run_variance_ratio_analysis(
    ticker_name=ticker,
    price_series=df_filter["price_t"],
    lookback_days=lookback_window,
    max_k=60,
    step=5
)

# Display output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(f"\n============================================================")
print(f"Lo-MacKinlay Variance Ratio Test (Trailing 1Y) — {ticker}")
print(f"Period: {start_dt} to {end_dt} | Sample Size: {obs_count} trading days")
print(f"============================================================")
print("H0: Random Walk (VR = 1) vs. H1: Trend/Momentum (VR > 1) or Mean-Reversion (VR < 1)")
print(vr_results.to_string(index=False))

# Plot VR(k) curve for trailing 1-year
plt.figure(figsize=(10, 5))
plt.plot(vr_results["Horizon (k days)"], vr_results["Variance Ratio VR(k)"], marker="o", color="navy",
         label=f"{ticker} 1Y VR(k)")
plt.axhline(1.0, color="red", linestyle="--", alpha=0.7, label="Random Walk (VR = 1.0)")
plt.title(f"{ticker} — Trailing 1-Year Variance Ratio ({start_dt} to {end_dt})")
plt.xlabel("Holding Horizon k (Trading Days)")
plt.ylabel("Variance Ratio VR(k)")
plt.xticks(k_horizons)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Export to Excel
vr_output_path = f"{ticker}_1Y_variance_ratio_test.xlsx"
vr_results.to_excel(vr_output_path, index=False)
print(f"\nExported 1-Year Variance Ratio results to: {vr_output_path}")

# ROLLING TIME-SERIES MOMENTUM

def compute_tsmom_z_scores(ticker_name, price_series, lookback_days=252, max_k=60, step=5, vol_window=60):
    if isinstance(price_series, pd.DataFrame):
        clean_prices = price_series.iloc[:, 0].astype(float).dropna()
    else:
        clean_prices = price_series.squeeze().astype(float).dropna()

    if lookback_days is not None:
        clean_prices = clean_prices.iloc[-lookback_days:]

    start_date = clean_prices.index[0].strftime("%Y-%m-%d") if hasattr(clean_prices.index[0], "strftime") else "Start"
    end_date = clean_prices.index[-1].strftime("%Y-%m-%d") if hasattr(clean_prices.index[-1], "strftime") else "End"
    n_obs = len(clean_prices)

    # Daily log returns and rolling daily volatility baseline
    daily_returns = np.log(clean_prices / clean_prices.shift(1))
    rolling_daily_vol = daily_returns.rolling(window=vol_window, min_periods=20).std()

    k_horizons = list(range(step, max_k + step, step))
    tsmom_records = []

    # Store full rolling z-score series
    rolling_z_df = pd.DataFrame(index=clean_prices.index)

    for k in k_horizons:
        # Cumulative k-day log return
        k_day_return = np.log(clean_prices / clean_prices.shift(k))

        # Standardized drift
        z_series = k_day_return / (rolling_daily_vol * np.sqrt(k))
        rolling_z_df[f"z_{k}d"] = z_series

        # Force extraction to scalar floats
        val_z = z_series.iloc[-1]
        val_ret = k_day_return.iloc[-1]
        val_vol = rolling_daily_vol.iloc[-1]

        current_z = float(val_z) if pd.notna(val_z) else np.nan
        current_ret = float(val_ret) if pd.notna(val_ret) else np.nan
        current_daily_vol = float(val_vol) if pd.notna(val_vol) else np.nan
        ann_vol = current_daily_vol * np.sqrt(252) if not np.isnan(current_daily_vol) else np.nan

        # Two-tailed p-value against standard normal null (H0: zero drift)
        p_val = 2 * (1 - norm.cdf(abs(current_z))) if not np.isnan(current_z) else np.nan

        # Regime classification
        if np.isnan(current_z):
            regime = "Insufficient Data"
        elif current_z >= 1.96:
            regime = "Strong Bullish Momentum (p < 0.05)"
        elif current_z >= 1.645:
            regime = "Moderate Bullish Drift (p < 0.10)"
        elif current_z <= -1.96:
            regime = "Strong Bearish Momentum (p < 0.05)"
        elif current_z <= -1.645:
            regime = "Moderate Bearish Drift (p < 0.10)"
        else:
            regime = "Neutral / Range-Bound (|z| < 1.65)"

        tsmom_records.append({
            "Ticker": ticker_name,
            "Lookback Window": f"{n_obs} Days ({start_date} to {end_date})",
            "Horizon (k days)": k,
            "Cumulative Return": current_ret,
            "Annualized Vol (60d)": ann_vol,
            "TSMOM z-Score": current_z,
            "p-value": p_val,
            "Significant (5%)": abs(current_z) >= 1.96 if not np.isnan(current_z) else False,
            "Regime": regime
        })

    summary_df = pd.DataFrame(tsmom_records)
    return summary_df, rolling_z_df, k_horizons, start_date, end_date


# Run on active ticker and 1-year lookback window
tsmom_summary, rolling_z_history, k_horizons, start_dt, end_dt = compute_tsmom_z_scores(
    ticker_name=ticker,
    price_series=df_filter["price_t"],
    lookback_days=lookback_window,  # matches the 252 days from the VR test
    max_k=60,
    step=5,
    vol_window=60
)

# Display output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(f"\n============================================================")
print(f"Rolling Time-Series Momentum (TSMOM) z-Scores — {ticker}")
print(f"Period: {start_dt} to {end_dt} | Trailing 1-Year Window")
print(f"============================================================")
print("H0: Zero Directional Drift (z = 0) vs. H1: Trend Expansion (|z| >= 1.65 / 1.96)")
print(tsmom_summary.to_string(index=False))


# Visualizations

fig, axes = plt.subplots(2, 1, figsize=(11, 9))

# 1. Term structure of z-scores across horizons k as of today
axes[0].plot(tsmom_summary["Horizon (k days)"], tsmom_summary["TSMOM z-Score"], marker="o", color="teal", linewidth=2,
             label=f"Current z-Score ({ticker})")
axes[0].axhline(0.0, color="black", linestyle="-", alpha=0.5)
axes[0].axhline(1.96, color="green", linestyle="--", alpha=0.8, label="Bullish 5% Bound (+1.96)")
axes[0].axhline(-1.96, color="red", linestyle="--", alpha=0.8, label="Bearish 5% Bound (-1.96)")
axes[0].axhline(1.645, color="green", linestyle=":", alpha=0.5, label="Bullish 10% Bound (+1.65)")
axes[0].axhline(-1.645, color="red", linestyle=":", alpha=0.5, label="Bearish 10% Bound (-1.65)")
axes[0].set_title(f"{ticker} — Current TSMOM z-Score Curve Across Horizons k")
axes[0].set_xlabel("Holding Horizon k (Trading Days)")
axes[0].set_ylabel("Standardized Drift z-Score")
axes[0].set_xticks(k_horizons)
axes[0].legend(loc="best")
axes[0].grid(True, alpha=0.3)

# Historical 1-year trajectory of the 20-day momentum z-score
z_20_series = rolling_z_history["z_20d"].dropna()
axes[1].plot(z_20_series.index, z_20_series, color="navy", label="20-Day TSMOM z-Score")
axes[1].axhline(0.0, color="black", linestyle="-", alpha=0.5)
axes[1].axhline(1.96, color="green", linestyle="--", alpha=0.8, label="+1.96 Bound")
axes[1].axhline(-1.96, color="red", linestyle="--", alpha=0.8, label="-1.96 Bound")
axes[1].fill_between(z_20_series.index, 1.96, z_20_series, where=(z_20_series >= 1.96), color="green", alpha=0.2)
axes[1].fill_between(z_20_series.index, -1.96, z_20_series, where=(z_20_series <= -1.96), color="red", alpha=0.2)
axes[1].set_title(f"{ticker} — Trailing 1-Year Evolution of 20-Day Momentum z-Score")
axes[1].set_xlabel("Date")
axes[1].set_ylabel("z-Score")
axes[1].legend(loc="best")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Export to Excel
tsmom_output_path = f"{ticker}_1Y_tsmom_z_score.xlsx"
tsmom_summary.to_excel(tsmom_output_path, index=False)
print(f"\nExported TSMOM z-score results to: {tsmom_output_path}")

# Greek monitoring

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# outstanding trades

positions = [
    {"ticker": "AAA",  "option_type": "Call", "strike": 1060, "expiry": "2026-10-02", "quantity": 1,  "entry_price": 21.855},
    {"ticker": "AAA",  "option_type": "Put",  "strike": 900, "expiry": "2026-10-02", "quantity": 1,  "entry_price": 42.306},
    {"ticker": "BBB", "option_type": "Call", "strike": 110, "expiry": "2026-10-16", "quantity": 1, "entry_price": 21.855},
    {"ticker": "BBB", "option_type": "Put", "strike": 90, "expiry": "2026-10-16", "quantity": 1, "entry_price": 42.306},
    {"ticker": "CCC", "option_type": "Call", "strike": 260, "expiry": "2026-10-16", "quantity": 1, "entry_price": 21.855},
    {"ticker": "CCC", "option_type": "Put", "strike": 240, "expiry": "2026-10-16", "quantity": 1, "entry_price": 42.306},

]


# Risk-free rate

fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS1"
rf_data = pd.read_csv(fred_url, parse_dates=["observation_date"]).rename(columns={"DGS1": "rate"}).dropna()
risk_free_rate = rf_data["rate"].iloc[-1] / 100

# Pull live data + compute Greeks per position

today = datetime.now()
dashboard_rows = []

spot_cache = {}

for pos in positions:
    tkr = pos["ticker"]
    if tkr not in spot_cache:
        spot_cache[tkr] = yf.Ticker(tkr).history(period="1d")["Close"].iloc[-1]
    spot_price = spot_cache[tkr]

    expiry = pos["expiry"]
    T_days = (datetime.strptime(expiry, "%Y-%m-%d") - today).days
    T_years = max(T_days, 0) / 365.0
    flag = "c" if pos["option_type"] == "Call" else "p"

    # Pull current bid/ask for this specific contract to get current mark
    stock = yf.Ticker(tkr)
    opt_chain = stock.option_chain(expiry)
    chain_df = opt_chain.calls if pos["option_type"] == "Call" else opt_chain.puts
    match = chain_df[chain_df["strike"] == pos["strike"]]

    if match.empty:
        print(f"Warning: no matching contract found for {tkr} {pos['option_type']} {pos['strike']} {expiry}")
        continue

    bid, ask = match["bid"].iloc[0], match["ask"].iloc[0]
    current_price = (bid + ask) / 2 if (bid > 0 and ask > 0) else np.nan

    try:
        current_iv = implied_volatility(
            price=current_price, S=spot_price, K=pos["strike"],
            t=T_years, r=risk_free_rate, flag=flag
        )
    except Exception:
        current_iv = np.nan

    if np.isnan(current_iv) or current_iv <= 0:
        print(f"Warning: could not compute IV for {tkr} {pos['option_type']} {pos['strike']} {expiry}, skipping Greeks")
        continue

    pos_delta = delta(flag=flag, S=spot_price, K=pos["strike"], t=T_years, r=risk_free_rate, sigma=current_iv)
    pos_gamma = gamma(flag=flag, S=spot_price, K=pos["strike"], t=T_years, r=risk_free_rate, sigma=current_iv)
    pos_theta = theta(flag=flag, S=spot_price, K=pos["strike"], t=T_years, r=risk_free_rate, sigma=current_iv)
    pos_vega  = vega(flag=flag,  S=spot_price, K=pos["strike"], t=T_years, r=risk_free_rate, sigma=current_iv)

    qty = pos["quantity"]
    unrealized_pnl = (current_price - pos["entry_price"]) * qty * 100  # *100 for standard contract multiplier

    dashboard_rows.append({
        "Ticker": tkr,
        "Type": pos["option_type"],
        "Strike": pos["strike"],
        "Expiry": expiry,
        "T (days)": T_days,
        "Qty": qty,
        "EntryPrice": pos["entry_price"],
        "CurrentPrice": current_price,
        "Spot": spot_price,
        "IV": current_iv,
        "Delta": pos_delta * qty,
        "Gamma": pos_gamma * qty,
        "Theta": pos_theta * qty,
        "Vega": pos_vega * qty,
        "UnrealizedPnL": unrealized_pnl
    })

dashboard_df = pd.DataFrame(dashboard_rows)


# Portfolio-level aggregation

portfolio_summary = pd.DataFrame({
    "Metric": ["Net Delta", "Net Gamma", "Net Theta", "Net Vega", "Total Unrealized P&L"],
    "Value": [
        dashboard_df["Delta"].sum(),
        dashboard_df["Gamma"].sum(),
        dashboard_df["Theta"].sum(),
        dashboard_df["Vega"].sum(),
        dashboard_df["UnrealizedPnL"].sum()
    ]
})

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("\n=== Position-Level Dashboard ===")
print(dashboard_df.to_string(index=False))

print("\n=== Portfolio Summary ===")
print(portfolio_summary.to_string(index=False))


# Export to Excel (summary on separate sheets)

with pd.ExcelWriter("greeks_dashboard.xlsx") as writer:
    dashboard_df.to_excel(writer, sheet_name="Positions", index=False)
    portfolio_summary.to_excel(writer, sheet_name="Portfolio Summary", index=False)

print("\nExported to greeks_dashboard.xlsx")


