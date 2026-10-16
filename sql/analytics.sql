SELECT c.currency_code,
       c.currency_name,
       d.full_date AS rate_date,
       f.rate_pln
FROM fact_exchange_rate f
JOIN dim_currency c ON c.currency_key = f.currency_key
JOIN dim_date d ON d.date_key = f.date_key
WHERE f.date_key = (SELECT MAX(date_key) FROM fact_exchange_rate)
ORDER BY c.currency_code;


SELECT d.year,
       d.month,
       c.currency_code,
       ROUND(AVG(f.rate_pln), 4) AS avg_rate,
       ROUND(MIN(f.rate_pln), 4) AS min_rate,
       ROUND(MAX(f.rate_pln), 4) AS max_rate,
       COUNT(*) AS trading_days
FROM fact_exchange_rate f
JOIN dim_currency c ON c.currency_key = f.currency_key
JOIN dim_date d ON d.date_key = f.date_key
WHERE c.currency_code IN ('EUR', 'USD', 'GBP', 'CHF')
GROUP BY d.year, d.month, c.currency_code
ORDER BY c.currency_code, d.year, d.month;


WITH bounds AS (
    SELECT currency_key,
           MIN(date_key) AS first_key,
           MAX(date_key) AS last_key
    FROM fact_exchange_rate
    GROUP BY currency_key
)
SELECT c.currency_code,
       f_first.rate_pln AS first_rate,
       f_last.rate_pln AS last_rate,
       ROUND(100.0 * (f_last.rate_pln - f_first.rate_pln) / f_first.rate_pln, 2) AS change_pct
FROM bounds b
JOIN fact_exchange_rate f_first
  ON f_first.currency_key = b.currency_key AND f_first.date_key = b.first_key
JOIN fact_exchange_rate f_last
  ON f_last.currency_key = b.currency_key AND f_last.date_key = b.last_key
JOIN dim_currency c ON c.currency_key = b.currency_key
ORDER BY change_pct DESC;


SELECT c.currency_code,
       ROUND(AVG(f.rate_pln), 4) AS avg_rate,
       ROUND(100.0 * (MAX(f.rate_pln) - MIN(f.rate_pln)) / AVG(f.rate_pln), 2) AS range_pct
FROM fact_exchange_rate f
JOIN dim_currency c ON c.currency_key = f.currency_key
GROUP BY c.currency_code
ORDER BY range_pct DESC
LIMIT 10;


WITH daily AS (
    SELECT c.currency_code,
           d.full_date,
           f.rate_pln,
           LAG(f.rate_pln) OVER (PARTITION BY f.currency_key ORDER BY f.date_key) AS prev_rate
    FROM fact_exchange_rate f
    JOIN dim_currency c ON c.currency_key = f.currency_key
    JOIN dim_date d ON d.date_key = f.date_key
    WHERE c.currency_code IN ('EUR', 'USD')
)
SELECT currency_code,
       full_date,
       prev_rate,
       rate_pln,
       ROUND(100.0 * (rate_pln - prev_rate) / prev_rate, 3) AS day_change_pct
FROM daily
WHERE prev_rate IS NOT NULL
ORDER BY ABS(rate_pln - prev_rate) / prev_rate DESC
LIMIT 10;


SELECT c.currency_code,
       COUNT(f.date_key) AS days_with_rate,
       (SELECT COUNT(*) FROM dim_date) AS total_trading_days,
       (SELECT COUNT(*) FROM dim_date) - COUNT(f.date_key) AS missing_days
FROM dim_currency c
LEFT JOIN fact_exchange_rate f ON f.currency_key = c.currency_key
GROUP BY c.currency_code
HAVING missing_days > 0
ORDER BY missing_days DESC;
