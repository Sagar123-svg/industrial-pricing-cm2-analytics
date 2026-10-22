-- ============================================================
-- ANALYTICAL QUERIES — BATCH 2 (Queries 7-12)
-- Customer discount/profitability, Category profitability,
-- Price & cost change tracking
-- ============================================================

-- ------------------------------------------------------------
-- Query 7: Customers with Highest Revenue
-- ------------------------------------------------------------
SELECT
    c.Customer_ID,
    c.Customer_Name,
    c.Customer_Segment,
    SUM(f.Revenue) AS Total_Revenue,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Customer c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name, c.Customer_Segment
ORDER BY Total_Revenue DESC
LIMIT 10;


-- ------------------------------------------------------------
-- Query 8: Customers with Lowest Profitability
-- Revenue floor via HAVING avoids low-volume noise dominating
-- the "worst customer" list.
-- ------------------------------------------------------------
SELECT
    c.Customer_ID,
    c.Customer_Name,
    c.Customer_Segment,
    SUM(f.Revenue) AS Total_Revenue,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Customer c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name, c.Customer_Segment
HAVING SUM(f.Revenue) > 5000
ORDER BY CM2_Percentage ASC
LIMIT 10;


-- ------------------------------------------------------------
-- Query 9: Customers with Highest Discounts
-- ------------------------------------------------------------
SELECT
    c.Customer_ID,
    c.Customer_Name,
    c.Customer_Segment,
    COUNT(*) AS Transaction_Count,
    ROUND(AVG(f.Discount_Percentage), 2) AS Avg_Discount_Percentage,
    SUM(f.Revenue) AS Total_Revenue,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage
FROM Fact_Sales f
JOIN Dim_Customer c ON f.Customer_ID = c.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name, c.Customer_Segment
ORDER BY Avg_Discount_Percentage DESC
LIMIT 10;


-- ------------------------------------------------------------
-- Query 10: Discount % vs CM2% Relationship (banded analysis)
-- CASE buckets a continuous variable into readable bands;
-- conditional SUM(CASE...) counts negative-CM2 rows per band.
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN Discount_Percentage < 10 THEN '0-10%'
        WHEN Discount_Percentage < 20 THEN '10-20%'
        WHEN Discount_Percentage < 30 THEN '20-30%'
        WHEN Discount_Percentage < 40 THEN '30-40%'
        ELSE '40%+'
    END AS Discount_Band,
    COUNT(*) AS Transaction_Count,
    ROUND(AVG(CM2_Percentage), 2) AS Avg_CM2_Percentage,
    SUM(CASE WHEN Negative_CM2_Flag = 'Yes' THEN 1 ELSE 0 END) AS Negative_CM2_Count
FROM Fact_Sales
GROUP BY Discount_Band
ORDER BY MIN(Discount_Percentage);


-- ------------------------------------------------------------
-- Query 11: Material Categories by Profitability (vs target)
-- ------------------------------------------------------------
SELECT
    m.Material_Category,
    COUNT(*) AS Transaction_Count,
    SUM(f.Revenue) AS Total_Revenue,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage,
    dt.Target_CM2_Percentage,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100 - dt.Target_CM2_Percentage, 2) AS Gap_vs_Target
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
JOIN Dim_Category_Target dt ON m.Material_Category = dt.Material_Category
GROUP BY m.Material_Category, dt.Target_CM2_Percentage
ORDER BY CM2_Percentage DESC;


-- ------------------------------------------------------------
-- Query 12: Price Changes Over Time (per material)
-- Uses Fact_Pricing event log, not Fact_Sales, to trace a clean
-- price-history timeline per material.
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    fp.Change_Date,
    fp.Previous_Price,
    fp.New_Price,
    fp.Price_Change_Percentage,
    fp.Reason_Code
FROM Fact_Pricing fp
JOIN Dim_Material m ON fp.Material_ID = m.Material_ID
WHERE fp.Change_Type = 'Price Change'
ORDER BY m.Material_ID, fp.Change_Date;
