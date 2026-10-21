# FIGHTEX — Engineering Case Study

**Economic simulation, multi-account modeling, market liquidity and reproducible audit evidence.**

This is the public, non-confidential companion to the seven-page English PDF case study ([FIGHTEX_Architecture_Case_Study_EN.pdf](FIGHTEX_Architecture_Case_Study_EN.pdf)). It documents verified architectural decisions from the private implementation without disclosing source code, customer-specific parameters or financial audit results.

## Shared economy for organic and multi-account actors

The simulation models bot accounts inside the same daily economic state as organic players. The bot-farm analyzer selects their population slice and derives per-account milestones, external spending, tournament payouts, marketplace fees, withdrawals, and remaining inventory. This avoids an unrealistic standalone ROI spreadsheet that assumes unlimited buyers.

The implemented analysis distinguishes the day of acquiring three cards, first tournament entry, first prize, operating and setup expenses, market proceeds, and per-account outcome distributions. Scenario comparisons can explore entry routes and liquidation exposure without publishing proprietary behavioral coefficients.

## Three separate valuation lenses

| Lens | What it represents |
| --- | --- |
| **Realized profit** | Withdrawn cash less acquisition, setup and operating costs |
| **Theoretical residual value** | Remaining live cards marked at floor price, net of the modeled marketplace fee |
| **Liquidation-adjusted outcome** | Results after attempting to sell residual inventory during a finite liquidation window |

The marketplace analysis uses listed supply, demand orders, executed trades and volume-weighted prices. Market-wide demand is not assumed to be exclusively available to the bot farm.

**Illustration, not a FIGHTEX result:** 1,000 cards marked at $1 are notionally worth $1,000. If the market executes 20 sales per day, selling 900 cards takes at least 45 days **only if** the seller captures all those sales and demand remains stable. Fees and competition can reduce realized proceeds.

## One computation engine, multiple interfaces

CLI, Streamlit and MCP converge on `SimulatorService` and the shared Python runner. The engine is independent of presentation, transport and SQLite. AI assistants can interpret structured results, but the economic arithmetic belongs to the Python engine.

## Reproducibility and accounting

The source implementation uses named seeded NumPy random streams, parameter hashes, immutable configuration snapshots, result digests and a run ledger. The financial model distinguishes accrual P&L, actual cash movement and reserved obligations; reconciliation checks help detect inconsistent flows.

**Known limitation:** independent review identified a weekly aggregation issue that can omit the last two ordinary financial days in a 730-day horizon. Affected outputs require correction and revalidation before being presented as final. This document does not claim validated economic forecasts or a security certification.

## PDF

The seven-page PDF [`FIGHTEX_Architecture_Case_Study_EN.pdf`](FIGHTEX_Architecture_Case_Study_EN.pdf) contains architecture diagrams and charts for multi-account simulation, marketplace liquidity, bot-farm valuation lenses with liquidation sensitivity, financial modeling, one-factor sensitivity analysis and reproducibility. **Every chart is built from synthetic data and labelled as such**; none of them shows FIGHTEX audit results or customer parameters. The generator and the synthetic data are in [`tools/pdf-demo/`](../tools/pdf-demo/).

[Architecture overview](../README.md) · [Engine architecture](ENGINE.md) · [MCP integration](MCP.md) · [Reproducibility](REPRODUCIBILITY.md)
