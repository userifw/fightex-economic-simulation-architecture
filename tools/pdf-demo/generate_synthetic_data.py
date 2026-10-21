"""Generate the synthetic demonstration data used by build_case_study.py.

Everything here is invented for illustration. The numbers are NOT FIGHTEX audit results, customer parameters or
output of the private simulation engine. They only have plausible shapes so that the charts explain the analysis
methods (shared multi-account economy, marketplace liquidity, liquidation sensitivity, cash-flow modeling, one-factor
sensitivity). Seeded NumPy generators make the files reproducible: re-running this script rewrites identical CSVs.

Usage:  python generate_synthetic_data.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260101
DATA = Path(__file__).resolve().parent / "data"


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def marketplace(rng: np.random.Generator) -> None:
    """Daily listed supply, demand orders and executed trades for one card rarity over 180 days (synthetic)."""
    days = np.arange(1, 181)
    supply = 900 + 520 * (1 - np.exp(-days / 35)) + 70 * np.sin(days / 9) + rng.normal(0, 25, days.size)
    demand = 260 + 150 * (1 - np.exp(-days / 50)) + 45 * np.sin(days / 6 + 1) + rng.normal(0, 18, days.size)
    # a trade needs a matching buy order and a listed card at an acceptable price: only a fraction of the demand converts
    match = np.clip(0.42 + 0.06 * np.sin(days / 14) + rng.normal(0, 0.03, days.size), 0.2, 0.7)
    executed = np.minimum(np.round(demand * match), np.round(supply * 0.115))
    vwap = np.empty(days.size)
    price = 1.0
    for i in range(days.size):
        pressure = (demand[i] - supply[i] / 4.0) / 400.0
        price = max(0.5, price + 0.08 * (1.0 - price) + 0.05 * pressure + rng.normal(0, 0.012))
        vwap[i] = price
    write_csv("marketplace.csv", ["day", "listed_supply", "demand_orders", "executed_trades", "vwap", "floor_price"],
              [[int(d), round(float(s)), round(float(o)), int(e), round(float(p), 4), 0.5]
               for d, s, o, e, p in zip(days, supply, demand, executed, vwap)])


def liquidation_curve() -> None:
    """Liquidation-adjusted value of a residual inventory as a function of the liquidation window (synthetic).

    1,000 cards are marked at a floor price of 1.00 (notional units). The market can absorb `depth` sales per day.
    Selling into a thinner market (smaller depth) moves the achievable price more per day; the price slowly recovers,
    and a marketplace fee is deducted from every sale.
    """
    cards, floor, fee = 1000, 1.0, 0.05
    rows = []
    for depth in (10, 20, 40):
        daily_drop = 0.016 * (20 / depth) ** 0.8
        for window in range(0, 366, 5):
            remaining, proceeds, price = float(cards), 0.0, floor
            for _ in range(window):
                sold = min(depth, remaining)
                if sold <= 0:
                    break
                proceeds += sold * price * (1 - fee)
                remaining -= sold
                price = max(0.5 * floor, price - daily_drop * sold / depth)
                price += 0.04 * (floor - price)
            rows.append([depth, window, round(proceeds, 2), round(remaining, 1), round(cards * floor * (1 - fee), 2)])
    write_csv("liquidation_curve.csv", ["market_sales_per_day", "window_days", "liquidation_adjusted_value", "unsold_cards", "theoretical_value"], rows)


def botfarm_scenarios(rng: np.random.Generator) -> None:
    """Three valuation lenses for three illustrative entry routes (notional units per 100 accounts)."""
    rows = []
    for route, setup, realized, residual, depth in (
        ("Route A: buy on market", 100, 82, 215, 0.55),
        ("Route B: packs + craft", 100, 118, 160, 0.72),
        ("Route C: referral-style entry", 100, 64, 120, 0.8),
    ):
        theoretical = realized + residual
        liquidation_adjusted = realized + residual * depth + rng.normal(0, 2)
        rows.append([route, setup, realized, round(float(liquidation_adjusted), 1), theoretical])
    write_csv("botfarm_scenarios.csv", ["scenario", "cost", "realized_value", "liquidation_adjusted_value", "theoretical_value"], rows)


def multi_account(rng: np.random.Generator) -> None:
    """Per-account milestones for organic players and multi-account actors sharing the same daily economy (synthetic)."""
    n_org, n_bot = 400, 120
    org_first_entry = np.clip(rng.gamma(2.2, 9.0, n_org) + 3, 3, 120)
    bot_first_entry = np.clip(rng.gamma(4.0, 3.2, n_bot) + 7, 7, 70)       # coordinated, narrower window
    org_first_prize = org_first_entry + np.clip(rng.gamma(2.0, 22, n_org), 1, 300)
    bot_first_prize = bot_first_entry + np.clip(rng.gamma(2.6, 10, n_bot), 1, 150)
    org_net = rng.normal(-4, 9, n_org)
    bot_net = rng.normal(2, 12, n_bot) - 1.5 * np.clip(rng.normal(0, 1, n_bot), 0, None)
    rows = [["organic", round(float(a), 1), round(float(b), 1), round(float(c), 2)] for a, b, c in zip(org_first_entry, org_first_prize, org_net)]
    rows += [["multi_account", round(float(a), 1), round(float(b), 1), round(float(c), 2)] for a, b, c in zip(bot_first_entry, bot_first_prize, bot_net)]
    write_csv("multi_account.csv", ["actor_group", "first_tournament_day", "first_prize_day", "net_outcome"], rows)

    # bot accounts as a growing slice of the same market: share of daily buy orders by actor group
    days = np.arange(1, 181)
    organic_orders = 210 + 120 * (1 - np.exp(-days / 45)) + rng.normal(0, 8, days.size)
    farm_orders = np.where(days < 20, 0, 60 * (1 - np.exp(-(days - 20) / 25))) + rng.normal(0, 4, days.size)
    farm_orders = np.clip(farm_orders, 0, None)
    write_csv("order_flow.csv", ["day", "organic_orders", "multi_account_orders"],
              [[int(d), round(float(o)), round(float(f))] for d, o, f in zip(days, organic_orders, farm_orders)])


def finance(rng: np.random.Generator) -> None:
    """Monthly revenue and expense flows for a 24-month horizon (synthetic notional units, thousands)."""
    months = np.arange(1, 25)
    ramp = 1 - np.exp(-months / 6.0)
    packs = 210 * ramp + rng.normal(0, 5, months.size)
    slots = 70 * ramp * (1 + 0.012 * months) + rng.normal(0, 3, months.size)
    ads = 45 * ramp + rng.normal(0, 2, months.size)
    fees = 12 * ramp + rng.normal(0, 1, months.size)
    prizes = np.full(months.size, 150.0) + rng.normal(0, 2, months.size)
    marketing = np.where(months <= 2, 120.0, 55.0) + rng.normal(0, 3, months.size)
    operations = np.full(months.size, 95.0) + rng.normal(0, 1.5, months.size)
    revenue = packs + slots + ads + fees
    expenses = prizes + marketing + operations
    net = revenue - expenses
    rows = [[int(m), *[round(float(x), 1) for x in (p, s, a, f, pz, mk, op, r, e, n, c)]]
            for m, p, s, a, f, pz, mk, op, r, e, n, c in zip(months, packs, slots, ads, fees, prizes, marketing, operations, revenue, expenses, net, np.cumsum(net))]
    write_csv("finance_monthly.csv", ["month", "packs", "slots", "ads", "marketplace_fees", "prizes", "marketing", "operations", "revenue", "expenses", "net_cash_flow", "cumulative_cash_flow"], rows)


def sensitivity() -> None:
    """One-factor-at-a-time effects on a headline result (percent of the base case), generic driver names (synthetic)."""
    rows = [
        ("Paying-user conversion", -42.0, 38.0),
        ("Repeat-purchase willingness", -31.0, 27.0),
        ("Payment-channel payout rate", -24.0, 18.0),
        ("Daily activity level", -19.0, 16.0),
        ("Player retention", -15.0, 13.0),
        ("Marketing intensity", -9.0, 11.0),
        ("Prize-pool size", 14.0, -12.0),
        ("Marketplace fee", -4.0, 5.5),
        ("Onboarding bonus size", 3.0, -2.5),
    ]
    write_csv("sensitivity.csv", ["driver", "effect_at_low_pct", "effect_at_high_pct"], [list(r) for r in rows])


def seed_spread(rng: np.random.Generator) -> None:
    """Headline result of the unchanged base case across 25 seeds, as percent deviation from the mean (synthetic)."""
    values = rng.normal(0.0, 1.6, 25)
    write_csv("seed_spread.csv", ["seed_index", "deviation_pct"], [[i + 1, round(float(v), 2)] for i, v in enumerate(values)])


def main() -> None:
    rng = np.random.default_rng(SEED)
    marketplace(rng)
    liquidation_curve()
    botfarm_scenarios(rng)
    multi_account(rng)
    finance(rng)
    sensitivity()
    seed_spread(rng)
    print(f"synthetic data written to {DATA}")


if __name__ == "__main__":
    main()
