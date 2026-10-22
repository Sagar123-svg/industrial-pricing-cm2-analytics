-- ============================================================
-- ANALYTICAL QUERIES — BATCH 1 (Queries 1-6)
-- Monthly trends, Top materials, Negative CM2, Lowest margin
-- ============================================================

-- ------------------------------------------------------------
-- Query 1: Monthly Revenue Trend
-- ------------------------------------------------------------
SELECT
    d.Year,
    d.Month_Name,
    SUM(f.Revenue) AS Total_Revenue
FROM Fact_Sales f
JOIN Dim_Date d ON f.Transaction_Date = d.Date
GROUP BY d.Year, d.Month, d.Month_Name
ORDER BY d.Year, d.Month;


-- ------------------------------------------------------------
-- Query 2: Monthly CM2 Trend (aggregate CM2%, not row-average)
-- ------------------------------------------------------------
SELECT
    d.Year,
    d.Month_Name,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Date d ON f.Transaction_Date = d.Date
GROUP BY d.Year, d.Month, d.Month_Name
ORDER BY d.Year, d.Month;


-- ------------------------------------------------------------
-- Query 3: Top 10 Materials by Revenue
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    SUM(f.Revenue) AS Total_Revenue,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
GROUP BY m.Material_ID, m.Material_Description, m.Material_Category
ORDER BY Total_Revenue DESC
LIMIT 10;


-- ------------------------------------------------------------
-- Query 4: Top 10 Materials by CM2 (absolute value)
-- Compare this result set to Query 3 to spot high-revenue /
-- low-profitability materials (Business Question #14).
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
GROUP BY m.Material_ID, m.Material_Description, m.Material_Category
ORDER BY Total_CM2 DESC
LIMIT 10;


-- ------------------------------------------------------------
-- Query 5: Materials with Negative CM2
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    COUNT(*) AS Negative_Transaction_Count,
    SUM(f.CM2) AS Total_Negative_CM2,
    ROUND(AVG(f.CM2_Percentage), 2) AS Avg_CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
WHERE f.Negative_CM2_Flag = 'Yes'
GROUP BY m.Material_ID, m.Material_Description, m.Material_Category
ORDER BY Total_Negative_CM2 ASC;   -- most negative (biggest loss) first


-- ------------------------------------------------------------
-- Query 6: Materials with Lowest CM2% (structural margin weakness)
-- Uses HAVING (not WHERE) because the filter is on an aggregate.
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    SUM(f.Revenue) AS Total_Revenue,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage,
    dt.Target_CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
JOIN Dim_Category_Target dt ON m.Material_Category = dt.Material_Category
GROUP BY m.Material_ID, m.Material_Description, m.Material_Category, dt.Target_CM2_Percentage
HAVING SUM(f.Revenue) > 1000   -- exclude tiny/noise transactions
ORDER BY CM2_Percentage ASC
LIMIT 10;
