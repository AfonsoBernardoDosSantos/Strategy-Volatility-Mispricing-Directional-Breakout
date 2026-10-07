[README.md](https://github.com/user-attachments/files/33180651/README.md)
# Volatility-Mispricing-Directional-Breakout
A simple options trading strategy based on finding underpriced options through volatility mispricings combined with a directional breakout.
# Volatility Mispricing Discovery and Directional Breakout

Afonso Bernardo dos Santos

## Thesis and results

This strategy attempts to generate P&L through two distinct, sequential drivers. The first is identifying statistically significant mispricing between implied and forecasted volatility, which determines trade selection and entry edge. The second is a directional breakout captured through positive gamma exposure once a position is on. The sections below address each in turn.

Volatility is a mathematical synonym of standard deviation which measures how far observations are spread out of the mean on average during a particular time period. For time series and markets purposes, usually the standard deviation of returns is analysed. The application is thus to understand how much returns have diverged from its mean, on average, over a particular time period. A 1 year realized volatility of 40% means returns have diverged around ±40% off its mean over the last year. Moreover, in this example, if we looked at a random observation, there would be a ≈68% probability that that return observation would be around ±40% off its mean. This figure comes from the normal distribution 1 standard deviation probability definition.

The 1 year realized volatility for a series of returns $x_{n}$, with mean $\mu$ is:

$$
\sigma = \sqrt{\frac{\sum_{n = 1}^{252}{(x_{n} - \mu)}^{2}}{252 - 1}}
$$

Implied volatility on the other hand, contrasting with realized volatility, is a market expectation of how much returns are expected to diverge around its mean over a future time period. Being an expectation from investors, implied volatility is unobservable and this brings some ambiguity to its truthfulness.

See the below example for a 30-day call option with IV of 40%:

$$\text{Expected Move} = IV \times \sqrt{\frac{\text{Days to expiration}}{365}}$$

$$\text{Expected Move} = 40\% \times \sqrt{\frac{30}{365}} = 11.5\%$$

The 11.5% figure means that the market expects that, with 68.27% probability (1 standard deviation of a normal distribution), the price of the stock will move 11.5% around its mean over a 30-calendar-day period. If the stock price is 10&#36;, the maximum expected price is 11.15&#36; and the minimum expected price is 8.85&#36;.

It is well documented that markets tend to overreact to bad news and underreact to good news, which causes the price discovery process in the short term to be chaotic and implied volatility expectations to follow suit. As such, it is not unreasonable to assume that the market might have wrong expectations about what asset returns are going to do over a particular time period.

A concrete example could be the following. Let’s say now Trump and the Iranian government announce a deal to end hostilities in the Strait of Hormuz. Peace will come and with it, free passage of ships in the Strait. The market skyrockets, uncertainty reduces and consequently volatility drops. In between the lines it is said that the U.S. will now start charging a toll of ships carrying oil through the Strait. This goes by unnoticed by most investors due to the euphoria of the end of the war. This toll will surely increase prices for all consumers and lead to inflationary pressures. Rates will rise, money accessibility will drop and volatility will spike.

An attentive investor could realize these ideas and try and capture some profits through acting on what he believes is mispriced implied volatility (buying cheap vol and selling expensive vol).

This could also be done in a systematic way, through econometric models rather than just market intuition. Volatility is mean reverting and, funnily enough, volatile. Being mean reverting means there is some relationship between past values and future values. Models allow us to capture this relationship and assess, through a mathematical approach what could be the correct implied volatility for a time period for that stock, given past information.

The main problem lies on how to assess what is the correct implied volatility under a reasonable confidence interval for a particular stock, identifying if there is a statistically significant mispricing and trading on a liquid enough option.

Moreover, it would be naïve to choose a single model for every stock. Some models do a better job at explaining the volatility of a particular stock and others explain better of others. This can be seen also through the model definitions. Some stocks tend to have particular long memory or momentum, while others do not. Having a strategy that lets the data dictate the most adequate model to forecast volatility allows the model best suited to that return series to be used.

Volatility mispricing capture can be best done through equity options. Option prices are extremely sensitive to implied volatility changes. IV has a positive relationship with the option price because options possess a non-linear payoff profile, having a capped downside and an unlimited upside. As such, even though higher IV implies higher moves to either the downside or the upside, the option owner can never lose more than the value of the option but stands to gain much more if price moves in the right direction. Therefore, volatility has this asymmetric payoff towards the value of the option.

Market expectations of implied volatility, for specific option strikes and time to maturity can be backed out from market prices. The difference between the Model IV and the BS IV is the trade’s edge.

While classic volatility arbitrage seeks to isolate vega through continuous delta-hedging, this strategy uses delta-neutral strangles at entry solely to remain direction-agnostic at inception. The engine of profitability is not simply pure volatility convergence, but the exploitation of underpriced options to capture directional breakout momentum with a convex payoff asymmetry.

Continuous delta-hedging is particularly hard to accomplish for a retail trader. The trader faces short-selling restrictions, high transaction costs, exchange rate fees (if investors are outside of the US) and time consumption.

As such, finding undervalued implied volatility in equity options combined with a directional breakout strategy can and has so far produced encouraging results in a small live sample.

Also, it allows to capture faster and more expressive profits. Volatility tends to take quite some time to converge to model expectations, but volatility combined with delta expansion can make the trade reach the desired level of return rather faster (also with more risk).

An example of a profitable long strangle on Boeing featuring mispriced volatility capture and momentum riding can be seen below. (Reported returns are based on actual executed fill prices, so the bid-ask spread is already embedded in entry and exit and they are net of commissions. Total return is calculated as final trade value over capital deployed

| **Option** | **Model**         | **Entry Date** | **Spot** | **Strike** | **TTM** | **Holding Period** | **BS IV** | **Model IV** | **Closing IV** | **Return** | **Total Return** |
|------------|-------------------|----------------|----------|------------|---------|--------------------|-----------|--------------|----------------|------------|------------------|
| Call       | AR(5)-EGARCH(1,1) | 17/08/26       | 231.67   | 250        | 25 days | 3 days             | 28.1%     | 35.0%        | 34.0%          | -92.1%     | **35.6%**        |
| Put        | AR(5)-EGARCH(1,1) | 17/08/26       | 231.67   | 215        | 25 days | 3 days             | 28.4%     | 35.0%        | 29.6%          | 134.3%     |                  |

*Total Trade Return was 35.6% which corresponds to an 11.85% daily return.*

This trade presents perfectly the main points of this strategy. Starting off with a volatility mispricing and a delta-neutral trade and letting the underlying run a directional breakout, taking advantage of our positive gamma exposure. The main driver of choice of position is the mispriced volatility and the main driver of final P&L is the directional breakout.

Please see below some other examples of profitable Strangles the strategy has produced:

| **Option** | **Stock** | **Model**          | **Entry Date** | **Spot** | **Strike** | **TTM (days)** | **Holding Period (days)** | **BS IV** | **Model IV** | **Closing IV** | **Return** | **Total Return** |
|------------|-----------|--------------------|----------------|----------|------------|----------------|---------------------------|-----------|--------------|----------------|------------|------------------|
| Call       | CMG       | APARCH(1,1)        | 17/08/26       | 33.5     | 37         | 25             | 5                         | 34.7%     | 48.4%        | **37.4%**      | 254.5%     | **69.5%**        |
| Put        | CMG       | APARCH(1,1)        | 17/08/26       | 33.5     | 30         | 25             | 5                         | 36.5%     | 48.4%        | **N/A**        | -91.5%     |                  |
| Call       | AAL       | AR(5)-APARCH(1,1)  | 17/08/26       | 14.8     | 15.5       | 25             | 15                        | 32.9%     | 54.8%        | **N/A**        | -98.0%     | **3.9%**         |
| Put        | AAL       | AR(5)-APARCH(1,1)  | 17/08/26       | 14.8     | 14.5       | 25             | 15                        | 38.4%     | 54.7%        | **32.8%**      | 73.4%      |                  |
| Call       | F         | APARCH(1,1)        | 24/08/26       | 14.4     | 15.5       | 32             | 25                        | 32.7%     | 39.5%        | **52.9%**      | 254.5%     | **5.3%**         |
| Put        | F         | APARCH(1,1)        | 24/08/26       | 14.4     | 13.5       | 32             | 25                        | 32.8%     | 39.5%        | **30.9%**      | -91.5%     |                  |
| Call       | NKE       | APARCH(1,1)        | 04/09/26       | 38.77    | 41         | 20             | 6                         | 32.5%     | 41.4%        | **38.8%**      | -63.8%     | **17.6%**        |
| Put        | NKE       | APARCH(1,1)        | 04/09/26       | 38.77    | 37         | 20             | 6                         | 31.9%     | 41.4%        | **35.0%**      | 56.3%      |                  |
| Call       | ADBE      | Const. EGARCH(1,1) | 21/09/26       | 249      | 260        | 25             | 7                         | 39.7%     | 51.9%        | **38.7%**      | -90.3%     | **24.0%**        |
| Put        | ADBE      | Const. EGARCH(1,1) | 21/09/26       | 249      | 240        | 25             | 7                         | 41.6%     | 51.9%        | **37.9%**      | 155.4%     |                  |

*Closing IV was not recorded for the CMG put and AAL call; Returns are computed from closing option prices*

It is observable that not all positions cleanly converge to the model’s forecast. In this particular period in time, volatility is low and has been sticking particularly hard to this low level. The graph below shows a clustering of the VIX. We are currently in the lowest cluster (green), even though there has been particular turmoil in geopolitics and global markets.

![K-means clustering of VIX history into four volatility regimes, with the current level in the lowest cluster]<img width="1592" height="412" alt="image1" src="https://github.com/user-attachments/assets/2d170bb7-46d8-40d9-ac07-171b178eb559" />


In the small sample I currently possess of the strategy, out of the 9 trades I made, 8 have had positive returns. The trade that lost money was due to poor risk management and position control, most likely due to my inexperience in trading short-dated options. This trade can be seen below:

| **Option** | **Stock** | **Model**   | **Entry Date** | **Spot** | **Strike** | **TTM (days)** | **Holding Period (days)** | **BS IV** | **Model IV** | **Closing IV** | **Return** | **Total Return** |
|------------|-----------|-------------|----------------|----------|------------|----------------|---------------------------|-----------|--------------|----------------|------------|------------------|
| Call       | GEV       | APARCH(1,1) | 24/08/26       | 958.9    | 1060       | 39             | 31                        | 49.7%     | 58.4%        | **45.6%**      | -98.2%     | **-95.0%**       |
| Put        | GEV       | APARCH(1,1) | 24/08/26       | 958.9    | 900        | 39             | 31                        | 47.7%     | 58.5%        | **42.3%**      | -93.5%     |                  |

If a stop loss had been placed, the maximum drawdown could have been stopped at around the 70% loss level, and this huge loss could have been avoided.

## Volatility forecasting models

**GARCH (p,q):** Forecasts next day’s volatility through p lags of past volatility and q lags of past random shocks or innovations. The GARCH (1,1) model equation is:

$$\sigma_{t}^{2} = \omega + \alpha_{1}\varepsilon_{t - 1}^{2} + \beta_{1}\sigma_{t - 1}^{2}$$

Which then turns into:

*  
*$$\sigma_{t} = \sqrt{\omega + \alpha_{1}\varepsilon_{t - 1}^{2} + \beta_{1}\sigma_{t - 1}^{2}}$$

With random shocks being calculated in several ways:

Constant mean: $R_{t} = \mu + \varepsilon_{t}$

Zero mean: $R_{t} = \varepsilon_{t}$

AR (1) model: $R_{t} = \mu + \varphi R_{t - 1} + \varepsilon_{t}$

And the random shock can be decomposed in the following way:

$$\varepsilon_{t} = Z_{t}\sigma_{t}$$

Where $Z_{t}$ is inherent to the chosen probability distribution.

**GJR-GARCH (p,q):** Forecasts next day’s volatility in the same way as a plain GARCH but adds an asymmetry term to account for the effect that negative random shocks have a higher effect on volatility than positive random shocks. The GJR-GARCH (1,1) model equation is:

$$\sigma_{t}^{2} = \omega + \alpha_{1}\varepsilon_{t - 1}^{2} + \beta_{1}\sigma_{t - 1}^{2} + \ \theta I_{t - 1}\varepsilon_{t - 1}^{2}$$

Where $I_{t - 1}$ is a dummy variable that takes the value of 1 if the innovation was negative and 0 otherwise.

**EGARCH (p,q):** Models log-variance, ensuring positive volatility in all states, which is an augmentation to GARCH that requires parameters constraints to do so.

$$\log(\sigma_{t}^{2}) = \omega + \alpha_{1}\left| \frac{\varepsilon_{t - 1}}{\sigma_{t - 1}} \right| + \beta_{1}\log\left( \sigma_{t - 1}^{2} \right) + \ \theta\frac{\varepsilon_{t - 1}}{\sigma_{t - 1}}$$

The $\theta$ is the leverage term, similar to GJR-GARCH, but without the need to add a dummy variable or a squared innovation (ensuring it is always positive). If the estimated leverage term is negative, and innovation is negative, this brings total volatility higher.

The parameter α is the magnitude effect, which is applied to the innovation scaled by volatility. It measures how much yesterday’s shock was large in units of volatility and how it should contribute to the next day’s log variance.

**APARCH (p,q):** Model’s volatility letting the exponent be estimated by MLE rather than squaring it.

$$\sigma_{t}^{\delta} = \omega + \alpha{(\left| \varepsilon_{t - 1} \right| + \theta\varepsilon_{t - 1})}^{\delta} + \beta\sigma_{t - 1}^{\delta}$$

The $\delta$ is the power term, and it is estimated by MLE, letting data the decide the right scale, rather than rigid squaring it.

The $\theta$ is the asymmetry term. Also accounts for the leverage effect in a modified way to EGARCH and GJR-GARCH.

If $\delta$ = 2 and $\theta$ = 0, the equation literally turns into a Plain GARCH.

**FIGARCH (p,q):** Fixes short-term lag memory but doesn’t account for asymmetry

$$\sigma_{t}^{2} = \omega + \left\lbrack 1 - \beta L - (1 - \varphi L){(1 - L)}^{d} \right\rbrack\varepsilon_{t}^{2} + \beta\sigma_{t - 1}^{2}$$

d is the fractional differencing factor. If d=0 the memory functions the same as in a GARCH model (short-memory) and if d=1, it functions the same as in an IGARCH model (infinite memory). With this it has an hyperbolic decay of memory compared to the GARCH’s geometric.

L is the lag operator, that shifts the time series back one period where $Lx_{t} = x_{t - 1}$ and $L^{2}x_{t} = x_{t - 2}$

The other Greek coefficients represent the coefficients associated with the number of lags the equation is taking into account. In a FIGARCH (1,1) there would be only one $\beta$ (which is associated with past std. dev) and one $\varphi$ (which is associated with past random shocks).

**Adding the AR (k) term:** When residual autocorrelation is found, an AutoRegressive term should be added to the model set. This ensures that the residuals which are fed into the models are pure random innovations rather than a partial product of past innovations. The AR (1) model equation is:

$$R_{t} = \alpha + \varphi R_{t - 1} + \ \varepsilon_{t}$$

A standard innovation calculation is: $\varepsilon_{t} = R_{t} - \mu$

The problem with this equation, if serial residual dependence is found, is that nothing related to the past observation is removed - only a constant is subtracted. Therefore, this equation says, today’s innovation is just the difference between today’s returns and the average returns.

When using the AR (1) equation instead, the innovation equation looks like:

$$\varepsilon_{t} = \ R_{t} - \ \alpha - \ \varphi R_{t - 1}$$

Now $\varepsilon_{t}$ is the component of $R_{t}$ that is completely orthogonal to $R_{t - 1}$. More formally, the AR term absorbs the covariance structure that was affecting the innovation. By using the AR equation, Cov ($\varepsilon_{t},\ R_{t - 1}$) = 0

## The Trading Strategy (Driver 1)

Step 1: Extract past return data from the desired stock. There is a trade-off between more data and less data. With a longer sample size, there are more observations to train the model on and hence, a more granular training of the model. However, return data from a while back might not be representative of the current reality of the company (NVDA for example). Shorter sample sizes might be more representative of the current reality of the company but introduce less observations for the models to be trained on.

Step 2: Convert the stock returns to log returns.

Step 3: Check for autocorrelation in the residuals through a Ljung-box test. One should take into account that the Ljung-box test analyses the autocorrelation of all lags up until lag X. As such, it is not unusual to find that the shorter lags are not significant while the more distant lags are significant. The ACF plot can make the difference here. (Please note that the ACF plot is qualitative – meaning the trader eyeballs the results, while the LB test is quantitative).

It is important to proceed with these tests, because for volatility forecasting purposes, we do not want to be feeding our models with innovations (or residuals) that are partially influenced by past residuals. This would cause problems when forecasting because the model would be overfit to a sequence of correlated residuals rather than having estimated parameters from a series of random shocks.

Step 4: If autocorrelation is found, an AR (k) term will have to be included for every GARCH-family model to ensure the innovations fed into the GARCH models are pure random shocks rather than a partial product of momentum.

Step 5: Take 70% of the observations (initial observations) as the in-sample period and the remaining 30% as the out-of-sample period.

Step 6: Estimate the parameters of all the GARCH-family models using p = 1, …, 5 and q = 1, … 5 during the in-sample period. The distribution chosen should be a leptokurtic, skewed distribution, such as the Skewed Student’s t.

(Stock returns tend to deviate from Gaussian assumptions. That’s the main reason for the volatility smile. Far tail events tend to be more likely than what the normal distribution states, hence OTM strikes are more richly priced, leading to higher implied volatilities. See below a couple of examples of prominent stocks:

![AMZN daily return distribution against a fitted normal curve, annotated with skewness and excess kurtosis]<img width="1000" height="600" alt="image2" src="https://github.com/user-attachments/assets/067393c5-f225-419e-8e2b-c16855e1e25e" />
![NKE daily return distribution against a fitted normal curve, annotated with skewness and excess kurtosis]<img width="1000" height="600" alt="image3" src="https://github.com/user-attachments/assets/87638e53-7d61-493a-8cd7-c1cf3615c2ea" />
![TSLA daily return distribution against a fitted normal curve, annotated with skewness and excess kurtosis]<img width="1000" height="600" alt="image4" src="https://github.com/user-attachments/assets/c0882a61-f3bb-4689-9832-7ea3e2b9fe2d" />
Some stocks exhibit left skew, others exhibit right skew, but most exhibit excess kurtosis, hence utilizing a distribution such as the Skewed Student’s t, with degrees of freedom and skewness being freely estimated by MLE, allows for a better fit to the time series.)

Step 7: Rank the winning models from each family by BIC. Take the best p,q from each model to the next step.

Step 8: On a daily rolling basis (parameters being estimated on an expanding window) throughout the out-of-sample period, forecast the daily forecast volatility given each of the best models.

Step 9: Compare that daily forecast volatility forecast with the squared daily log returns (can be a reasonable proxy for daily realized volatility)

Step 10: Given the forecasted values and the real values compute the MSE for each of the models.

Step 11: Evaluate the statistical significance of the differences in models through Model Confidence Set set at 1%. If there are several models tied or with p-values very close to 1, the MSE results should break the tie. If MSE and MCS point to the same 2 models, choose the simplest one.

Step 12: Extract IV and greeks from option chain data with the following characteristics: TTM smaller than 60 days (augmented Gamma), Strikes ATM and 2 OTM strikes on each side (calls and puts) – higher vega and gamma. The idea is to get augmented greeks from close to the money and short TTM options. The volatility skew in ATM or close to ATM options also tends to be depressed, which presents more trading opportunities.

Step 13: Forecast volatility into the future with the winning model for the time period for each of the selected options. If APARCH or EGARCH are the winning models it is impossible to apply the figures into the equation to get the forecasted volatility – this because it is needed to calculate the expectation of tomorrow’s innovation to plug that into the formula – with these models the expectation is in log-variance or power-transformed variance, hence recovering the plain variance requires taking an expectation of a non-linear transform, which has no closed form. For a GARCH (1,1) to get next day’s expectation of innovation is simple, it is just the variance itself, which is then plugged continuously into the following equations. To solve this, 10k monte carlo simulations are run, drawing from the Skewed Student’s t-distribution and averaging them out to get a standardized residuals value. This then is applied to the formula $\varepsilon_{t} = Z_{t}\sigma_{t}$ where the standard deviation is the one forecasted by the model. This monte carlo process is done every day until reaching the target expiration dates (getting the volatility figure at that day).

Step 14: Daily variances are summed and then converted back to standard deviations to get to the forecast volatility from time t to time t+x and compared to the BS IV figure

Step 15: Taking the Skewed Student’s t-distribution monte carlo’s from step 13 and the idea to annualize each volatility path from step 14, the goal is to check how many of the paths landed above the IV from BS for that specific option. This is a modified p-value calculation. If out of the 10000 paths, only 500 sat below the IV from BS, then this gives a p-value of 0.05. That volatility pricing will be statistically significant for a long position on that option. If only 500 paths sat above the IV, that volatility pricing will be statistically significant for a short position on that option.

Step 16: After having statistically significant options (for a long position) we need to find a call and a put for the same expiration date that have similar mirror deltas to ensure delta-neutrality at inception and conclude the long strangle/straddle. Moreover, both options should have considerable open interest and a tight bid-ask spread to limit execution losses.

Step 17: The expected return on each option is calculated as the difference in Model IV and BS IV multiplied by the vega of the option at time 0. A conservative way of calculating the expected return of the strangle / straddle can be to do a weighted average of the expected returns of both options. This is particularly conservative if a strangle is traded. When one of the options moves closer to ATM, the vega will expand, and the sensitivity of the trade’s value to IV changes will expand with it.

A more mathematically sound approach to calculate the expected return of the trade is to reuse the 10k Monte Carlo paths already generated at step 13 for the volatility forecast. Rather than using a single vega snapshot at inception, each simulated path is used to reprice the option at expiration, accounting for the evolution of IV throughout the life of the contract. Averaging the terminal payoff across all paths yields an expected value that captures the curvature of vega with respect to volatility (vomma). This causes the expected return calculation to not leave out all higher order terms.

## Momentum Riding (Driver 2)

With Driver 1 complete, trade selection is now statistically justified. Driver 2, capturing the directional breakout itself, begins here.

Step 18: Before relying on momentum as a signal, formal tests for serial dependence should be run first, namely the Lo-MacKinlay variance ratio test and standard time-series momentum tests. These are the theoretically correct tools for detecting genuine momentum or reversal effects.

In practice, at the short horizons relevant to this strategy's holding period, these tests almost always return no statistical significance, consistent with the broader literature, which documents momentum as a medium-horizon effect (3 to 12 months) rather than a short-horizon one.

Given this, the trader should default to an OLS regression of returns on 60 lags of past returns, with Newey-West (HAC) standard errors to account for heteroskedasticity and possible remaining serial autocorrelation inherent in lagged data. This should be treated explicitly as a lightweight screening heuristic rather than a statistically validated signal, it exists to get a broad read on whether the stock has shown some short-term return momentum over the sample analysed, not to formally prove it. When one of the options starts going ITM, we need enough confidence from this screen to ride the momentum until the position reaches the desired level of return. If the stock shows no such momentum, even at this lighter heuristic level, then the delta-neutral strategy should be ensured to capture solely the volatility convergence (Driver 1) rather than volatility convergence plus directional breakout (Driver 2).

PS: if momentum is particularly significant from days 0 to 30 under this regression, then the momentum riding strategy should be followed.

PS (2): after 3 or 4 days of momentum riding without the trade reaching the desired level of return, the trader should start paying attention to momentum wearing off. If it happens, hedging the delta skew by buying or selling shares of the underlying should be done.

## Position Sizing

Step 19: Position size should be directly proportional to the expected return of the trade. If one of the trades has a 20% expected return and another has 40%, then the 40% trade should have double the size. This ensures the trader tries to capture the largest edge with the largest bet.

## Risk Management

Step 20: In some cases, when trading OTM options, these will be considerably illiquid. This might cause a trader to enter into a position with an immediate loss, just due to the bid-ask spread. Taking this into account, a position should be seriously evaluated when the position is down 70% or more. The trader’s conviction and judgement are key here. Say if the call leg is ATM or slightly ITM, with 5 DTE and there has been strong buying volume over the last trading days, then the trader might have conviction there can be a large upswing in price that makes the trade profitable. If market indicators and conviction point to the opposite side, then the position should be closed and the loss booked.

Another exit that should be considered happens when the underlying re-crosses the initial entry spot price at closing after having expanded to either side. If this happened after half of the initial TTM has passed, the trade should be exited, as the remaining time no longer justifies holding for a renewed breakout. Before that point, the trade may be held.

## Limitations

1.  Small live sample

2.  No out-of-sample backtest of the combined strategy due to inaccessibility of past options data

3.  Momentum riding is heuristic

4.  Risk management approach is still loose and under development
