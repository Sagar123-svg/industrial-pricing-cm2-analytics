# Power BI Dashboard: Build Notes

How the 4-page dashboard in the README was built.

## Data model

1. Import the fact and dimension tables (see `sql/01_schema.sql`).
2. Create one-to-many, single-direction relationships from each dimension to
   the fact table: material, customer, sales organization, pricing condition
   and date to `fact_sales`; material and date to `fact_pricing`.
3. Mark `dim_date` as a Date Table. The time-intelligence measures
   (`DATEADD`) need this.
4. Add the `Month Start` calculated column and the measures from
   `powerbi/dax_measures.txt`.

## Page setup

All pages use a custom 1280-wide canvas. Four dropdown slicers (date,
material category, sales organization, customer segment) sit across the top,
copied between pages so they land in the same position.

## Page 1: Pricing Management Overview

- Nine KPI cards: revenue, cost, CM2, CM2%, average selling price, average
  discount, transactions, negative CM2%, target achievement.
- Monthly revenue line, CM2 combo chart (columns = CM2, line = CM2%) and
  discount trend line, all on `Month Start`.
- Revenue by sales organization, CM2% against target by category, and
  revenue by category.

## Page 2: Material Profitability

- Top 10 materials by revenue and by CM2, each a bar chart with a Top N filter
  applied to the material and ranked by the matching measure.
- Bottom 10 materials by gap to target (`CM2 Gap vs Target`), so materials are
  compared with their own category target and not with each other.
- A table of materials with negative CM2 transactions and the CM2 lost.

## Page 3: Customer Profitability

- Scatter of revenue (x) against CM2% (y) per customer, coloured by customer
  segment. Two constant reference lines (median revenue and 40% margin) divide
  it into four quadrants. The group of high-revenue, low-margin customers is
  the one to review first.
- Bar charts for the lowest-margin customers (Bottom N by CM2%) and the top
  customers by revenue.

## Page 4: Pricing Decisions

- A table with one row per material: current price, previous price, standard
  cost, discount%, CM2%, target CM2%, proposed price, price gap and the
  revision flag, sorted by price gap so the most underpriced materials come
  first.
- KPI cards: materials below proposed price, CM2 at risk, average price gap.
- A bar chart of materials below proposed price by category.
- Edit interactions are set to None between the table and the cards, so
  clicking a table row does not change the headline figures.

## Notes

- `CM2 %` is `SUM(CM2) / SUM(Revenue)`, not an average of row-level
  percentages, which would give a small transaction the same weight as a
  large one.
- The pricing table works on average prices per material. A material can
  average slightly above its proposed price and still contain discounted
  transactions below it, so this view is read alongside the transaction-level
  target achievement figure.
