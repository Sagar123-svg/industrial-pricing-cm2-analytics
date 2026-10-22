-- ============================================================
-- ANALYTICAL QUERIES — BATCH 3 (Queries 13-18)
-- Sales org performance, cost increases, margin-erosion CTE,
-- window-function ranking, high-revenue/low-margin, proposed price
-- ============================================================

-- ------------------------------------------------------------
-- Query 13: Sales Organization Performance
-- ------------------------------------------------------------
SELECT
    so.Sales_Org_ID,
    so.Sales_Org_Name,
    so.Country,
    COUNT(*) AS Transaction_Count,
    SUM(f.Revenue) AS Total_Revenue,
    SUM(f.CM2) AS Total_CM2,
    ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage,
    ROUND(AVG(f.Discount_Percentage), 2) AS Avg_Discount_Percentage
FROM Fact_Sales f
JOIN Dim_Sales_Organization so ON f.Sales_Org_ID = so.Sales_Org_ID
GROUP BY so.Sales_Org_ID, so.Sales_Org_Name, so.Country
ORDER BY CM2_Percentage DESC;


-- ------------------------------------------------------------
-- Query 14: Materials with Significant Cost Increases (>10%)
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    fp.Previous_Cost,
    fp.New_Cost,
    fp.Cost_Change_Percentage,
    fp.Change_Date,
    fp.Reason_Code
FROM Fact_Pricing fp
JOIN Dim_Material m ON fp.Material_ID = m.Material_ID
WHERE fp.Change_Type = 'Cost Change'
  AND fp.Cost_Change_Percentage > 10
ORDER BY fp.Cost_Change_Percentage DESC;


-- ------------------------------------------------------------
-- Query 15: Cost Increase NOT Matched by Price Increase
-- (the core "margin erosion" query)
-- Uses CTEs to separate mixed event types, LEFT JOIN + COALESCE
-- to catch materials with a cost hike and NO price change at all.
-- ------------------------------------------------------------
WITH price_changes AS (
    SELECT Material_ID, Change_Date, Price_Change_Percentage
    FROM Fact_Pricing
    WHERE Change_Type = 'Price Change'
),
cost_changes AS (
    SELECT Material_ID, Change_Date, Cost_Change_Percentage
    FROM Fact_Pricing
    WHERE Change_Type = 'Cost Change'
)
SELECT
    m.Material_ID,
    m.Material_Description,
    cc.Cost_Change_Percentage,
    COALESCE(pc.Price_Change_Percentage, 0) AS Price_Change_Percentage,
    ROUND(cc.Cost_Change_Percentage - COALESCE(pc.Price_Change_Percentage, 0), 2) AS Unrecovered_Cost_Gap
FROM cost_changes cc
JOIN Dim_Material m ON cc.Material_ID = m.Material_ID
LEFT JOIN price_changes pc ON cc.Material_ID = pc.Material_ID
WHERE cc.Cost_Change_Percentage > COALESCE(pc.Price_Change_Percentage, 0)
ORDER BY Unrecovered_Cost_Gap DESC;


-- ------------------------------------------------------------
-- Query 16: Materials Below Target CM2% — Ranked Within Category
-- Window function RANK() partitioned by category so comparisons
-- are peer-group aware, not global.
-- ------------------------------------------------------------
SELECT
    Material_ID,
    Material_Description,
    Material_Category,
    CM2_Percentage,
    Target_CM2_Percentage,
    RANK() OVER (PARTITION BY Material_Category ORDER BY CM2_Percentage ASC) AS Rank_Within_Category
FROM (
    SELECT
        m.Material_ID,
        m.Material_Description,
        m.Material_Category,
        ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage,
        dt.Target_CM2_Percentage
    FROM Fact_Sales f
    JOIN Dim_Material m ON f.Material_ID = m.Material_ID
    JOIN Dim_Category_Target dt ON m.Material_Category = dt.Material_Category
    GROUP BY m.Material_ID, m.Material_Description, m.Material_Category, dt.Target_CM2_Percentage
) AS material_summary
WHERE CM2_Percentage < Target_CM2_Percentage
ORDER BY Material_Category, Rank_Within_Category;

-- Bonus: simple headline KPI — % of all transactions below target CM2
SELECT
    ROUND(
        SUM(CASE WHEN Low_Margin_Flag = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
    2) AS Pct_Transactions_Below_Target
FROM Fact_Sales;


-- ------------------------------------------------------------
-- Query 17: High-Revenue but Low-Margin Materials
-- Combines a revenue RANK() with a CM2% threshold to find
-- materials that look good on a revenue report but are
-- quietly dragging down profitability.
-- ------------------------------------------------------------
WITH revenue_rank AS (
    SELECT
        m.Material_ID,
        m.Material_Description,
        SUM(f.Revenue) AS Total_Revenue,
        ROUND(SUM(f.CM2) / SUM(f.Revenue) * 100, 2) AS CM2_Percentage,
        RANK() OVER (ORDER BY SUM(f.Revenue) DESC) AS Revenue_Rank
    FROM Fact_Sales f
    JOIN Dim_Material m ON f.Material_ID = m.Material_ID
    GROUP BY m.Material_ID, m.Material_Description
)
SELECT
    Material_ID,
    Material_Description,
    Total_Revenue,
    CM2_Percentage,
    Revenue_Rank
FROM revenue_rank
WHERE Revenue_Rank <= 20
  AND CM2_Percentage < 20
ORDER BY Total_Revenue DESC;


-- ------------------------------------------------------------
-- Query 18 (Bonus): Proposed Price Analysis
-- Implements Recommended_Price = Standard_Cost / (1 - Target_CM2%)
-- Output maps almost directly to the Power BI Page 3 pricing
-- action table.
-- ------------------------------------------------------------
SELECT
    m.Material_ID,
    m.Material_Description,
    m.Material_Category,
    f.Standard_Cost,
    ROUND(AVG(f.Selling_Price), 2) AS Current_Avg_Selling_Price,
    dt.Target_CM2_Percentage,
    ROUND(f.Standard_Cost / (1 - dt.Target_CM2_Percentage/100), 2) AS Recommended_Price,
    ROUND(
        ROUND(AVG(f.Selling_Price), 2) - ROUND(f.Standard_Cost / (1 - dt.Target_CM2_Percentage/100), 2),
    2) AS Price_Gap,
    CASE
        WHEN ROUND(AVG(f.Selling_Price), 2) < ROUND(f.Standard_Cost / (1 - dt.Target_CM2_Percentage/100), 2)
        THEN 'Yes' ELSE 'No'
    END AS Price_Revision_Required
FROM Fact_Sales f
JOIN Dim_Material m ON f.Material_ID = m.Material_ID
JOIN Dim_Category_Target dt ON m.Material_Category = dt.Material_Category
GROUP BY m.Material_ID, m.Material_Description, m.Material_Category, f.Standard_Cost, dt.Target_CM2_Percentage
ORDER BY Price_Gap ASC;
