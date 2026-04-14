# Trading Dashboard Design

## 0. Summary Panel Tab
**Goal:** Instant read of conditions

### Metrics
- IV − RV (short): `VIX9D − 9D RV`
- IV − RV (medium): `VIX − 30D RV`
- Spot vs Zero Gamma (ZGL distance)
- Spot vs key gamma levels (call wall / put wall)
- Volume condition (ES vs intraday avg)
- Expected Move:
  - `± SPX × (VIX9D / 100) × √(1/252)`
  - Display upper/lower range

### Table
- Key strikes:
  - Type (Call/Put)
  - Strike
  - GEX level

### Mini Chart
- SPX
- Fast MA
- Slow MA

### Data
- SPX
- VIX, VIX9D
- ES volume
- GEX calculations

---

## 1. Regime Panel Tab
**Goal:** Identify environment + stability

### Charts
- SPX candles (1m / 5m)
- Fast MA
- Slow MA
- ES volume (overlay or subpanel)

### Metrics
- SPX–VIX rolling correlation

### Data
- SPX
- VIX
- ES price + volume

---

## 2. Vol Panel
**Goal:** Evaluate vol pricing

### Charts
- VIX vs 30D realized vol
- VIX9D vs 9D realized vol

### Metric
- IV − RV spread

### Calculations
- Realized vol from SPX returns (rolling window)

### Data
- SPX historical prices
- VIX, VIX9D

---

## 3. Gamma Map Panel Tab
**Goal:** Positioning and key levels

### Charts
- Net GEX by strike (histogram)
- Spot price overlay

### Levels
- Largest call wall
- Largest put wall
- Zero gamma (ZGL)

### Data
- Options chain (multi-exp or selected)
- GEX calculations
- SPX price

---

## Core System

- **Regime** → direction + stability
- **Vol** → pricing for premium
- **Gamma** → positioning / structure
- **Summary** → compressed decision view

No redundant panels. All metrics map directly to decisions.