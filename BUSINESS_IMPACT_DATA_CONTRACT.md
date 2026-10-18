# Business impact attribution data contract

The project dataset has no post identifier, attributable conversion, sales value, variable cost, or media spend. Do not infer revenue or ROI from engagement proxies. This contract defines the row-level export needed to calculate them.

## File grain

One row per unique post for the same SUGAR account and reporting period. Each post must have deduplicated outcomes assigned by the same documented attribution model and window. Keep all monetary values in one currency per file. Use zero only for a verified zero; use a blank for unknown and correct missing values before upload.

## Required CSV columns

| Column | Definition | Validation |
|---|---|---|
| `post_id` | Stable platform post identifier | Required and unique; use the same ID in any social export used for reconciliation |
| `post_date` | Publication date | Parseable date; document timezone and use a consistent convention |
| `post_type` | Image, Reel, Story, Video, or source-defined value | Required; retain the raw source category |
| `campaign_type` | Source campaign label | Required; retain the raw source category |
| `eligible_opportunities` | Deduplicated denominator for attributed conversions, such as eligible sessions | Whole number, nonnegative; use one unit definition throughout. For randomized arm comparisons, this must be the pre-treatment assigned-unit denominator; post-treatment clicks or reach cannot be used for an intention-to-treat rate. |
| `attributed_conversions` | Deduplicated conversions in the chosen attribution window | Whole number, nonnegative, no greater than eligible opportunities |
| `attributed_net_revenue` | Revenue attributed to the post after discounts, cancellations, and refunds | Nonnegative amount in the file currency; document treatment of taxes |
| `variable_cost` | Product/fulfilment/payment costs attributable to those conversions | Nonnegative; use finance-approved cost definitions |
| `paid_media_cost` | Post-level paid distribution cost | Nonnegative; allocate campaign-level spend once across posts, never duplicate it |
| `currency_code` | ISO-style three-letter currency code | One code per upload |
| `attribution_window_days` | Days after eligible exposure included in attribution | Positive whole number; one window per upload |
| `attribution_method` | Approved rule such as last-click or position-based | One method per upload; document the actual implementation |

## Optional experiment columns

Provide both columns to compare a controlled test:

- `randomization_unit_id`: stable ID of the independently assigned unit (person, audience cluster, or content opportunity). Repeated posts for a unit are aggregated before resampling; allocate each eligible unit and each cost exactly once.
- `experiment_arm`: exactly `control` or `treatment`; a unit cannot appear in both arms.

Keep the preregistration, allocation list/seed, assignment date, eligibility rules, outcome definition, exposure window, stopping rule, and protocol owner outside this CSV in the experiment record. The CSV validator cannot prove random assignment or attribution correctness. Treatment-versus-control estimates should be interpreted causally only after the business owner verifies the protocol and execution. Every randomized unit must have a positive pre-treatment denominator; the arm analysis rejects zero-denominator units.

## Reported measures

- Conversion rate = attributed conversions / eligible opportunities.
- Customer acquisition cost = paid media cost / attributed conversions.
- Net ROAS = attributed net revenue / paid media cost.
- Contribution before paid media = attributed net revenue - variable cost.
- Net contribution = attributed net revenue - variable cost - paid media cost.
- ROI = net contribution / paid media cost.
- For an uploaded controlled test, the project estimates treatment-minus-control conversion-rate difference and net contribution per randomized unit with a unit-level bootstrap interval at the confidence level specified by the preregistered analysis. For the current illustrative three-test portfolio, the default interval is 98.33% (Bonferroni family-wise alpha 5%). The binary conversion sample-size planner does not power the continuous net-contribution comparison; calculate its sample size separately if it is a primary outcome.

Do not combine currencies or incompatible attribution windows/methods. Check paid-spend allocation and deduplicate conversions before upload. The blank [CSV template](data/business_impact_attribution_template.csv) is available for a source-system export; it contains column headers only, not fabricated outcomes.
