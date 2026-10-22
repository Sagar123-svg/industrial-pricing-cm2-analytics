# Pricing & CM2 Business Logic

| Metric | Formula | Example |
|---|---|---|
| Revenue | Quantity × Selling Price | 25 × 368 = 9,200 |
| Cost | Quantity × Standard Cost | 25 × 245.50 = 6,137.50 |
| CM2 (simplified) | Revenue − Cost | 9,200 − 6,137.50 = 3,062.50 |
| CM2 % | CM2 / Revenue × 100 | 3,062.50 / 9,200 = 33.29% |
| Discount % | (List Price − Selling Price) / List Price × 100 | (410−368)/410 = 10.24% |
| Price Change % | (New Price − Previous Price) / Previous Price × 100 | (410−390)/390 = 5.13% |
| Cost Change % | (New Cost − Previous Cost) / Previous Cost × 100 | (245.50−220)/220 = 11.59% |
| Recommended Price | Standard Cost / (1 − Target CM2%) | 245.50 / 0.68 = 361.03 |

## Flags

- **Negative CM2 Flag:** `CM2 < 0`
- **Low Margin Flag:** `CM2% < Target CM2%`
- **Price Revision Required Flag:**
  `Negative_CM2_Flag = Yes OR (Low_Margin_Flag = Yes AND Cost_Change% > Price_Change%)`

## Important Disclaimer

CM2 is simplified to **Revenue − Cost** for this project. In practice,
contribution margin hierarchies (CM1 → CM2 → CM3) typically include
additional variable costs such as freight, sales commissions, and customer
rebates. The exact CM2 formula and cost hierarchy used by any specific
company is internal/confidential and is not assumed or replicated here.

Similarly, **Recommended Price = Standard Cost / (1 − Target Margin)** is a
simplified analytical model. Real pricing decisions also factor in
competitor pricing, contract terms, customer relationship value, and market
conditions — this formula is a starting point for analysis, not a
final pricing decision.

## Pricing Review Tiers

| Tier | Condition | Action |
|---|---|---|
| 1 — Urgent | CM2 < 0 | Immediate review |
| 2 — High Priority | Below target AND cost outpaced price | Formal price revision |
| 3 — Monitor | Below target AND discount-driven | Review discount governance |
| 4 — Healthy | At/above target | No action |
