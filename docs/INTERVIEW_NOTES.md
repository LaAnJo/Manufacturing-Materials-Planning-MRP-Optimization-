# Interview walkthrough — MRP portfolio project

## 60-second pitch

"I built a 12-week MRP demonstration for concrete-material production planning. I started with an open research dataset of concrete ingredient quantities and strength measurements. I selected four illustrative 28-day mix designs and mapped each recipe into a per-m³ bill of materials. I then simulated 144 production orders, initial material inventory, supplier lead times and pricing. The Python pipeline performs BOM explosion and time-phased net requirements, respects MOQ/lot sizes, and dates purchase-order releases. It flags release dates that have already passed as of the planning date and moves the expected supply to feasible future weekly buckets. I used SQLite for analysis, Excel for planning review, and BI-ready DAX plus an interactive dashboard to surface proposed purchases, shortage risks and dates for supplier follow-up. This is a synthetic supply-chain scenario rather than actual plant performance." 

## Common questions and answers

**Why choose this dataset?** It contains real mixture quantities (kg/m³) that can be transformed into a BOM. It does NOT include factory work orders, stock or supplier information; those were explicitly simulated.

**What is gross vs net material requirement?** Gross is the required material before checking supply. Net demand is what needs to be ordered to satisfy expected demand and a safety-stock target after considering opening projected stock and scheduled receipts.

**Why do lead times matter?** An MRP receipt in the first week can be mathematically necessary but physically impossible to deliver if its release date has already passed. The model marks it for review and shifts the modeled delivery to the first standard-lead-time-feasible weekly bucket.

**What are your most important KPIs?** Total work-order volume, exploded ingredient demand, estimated purchase value, purchase release exceptions, shortage material-weeks under two scenarios, and backlog by material at a selected week.

**Why not total the backlog across weeks?** Backlog is the quantity still outstanding at week end. A 1,000 kg shortage left unresolved for two weeks should not be mislabeled as a 2,000 kg shortage.

**What could be improved?** Daily scheduling, supplier calendars, delivery reliability, alternate suppliers, rolling replenishment policies, variable demand, inventory carrying costs, scrap, production capacity and empirical strength/quality validation.

**What should you never claim?** No actual factory saved money or avoided a stockout. The source contains research samples, and all operating and financial information in this portfolio simulation is hypothetical.
