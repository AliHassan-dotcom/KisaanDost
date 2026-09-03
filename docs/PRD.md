# Kisaan Dost — Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | Kisaan Dost — Crop-Risk Intelligence Platform |
| **Version** | 1.0 (consolidated from: Project Description, PRD, Competitor Analysis, Tech Stack docs) |
| **Date** | 2026-08-28 |
| **Status** | Approved for MVP build |
| **Positioning** | *Pakistan's most practical crop-risk assistant.* |

---

## 1. Product Overview

Kisaan Dost is an AI-powered **crop-risk intelligence platform** for Pakistani farmers. It combines:

- Weather forecasts & alerts
- Satellite-based crop health monitoring (NDVI / NDWI via Google Earth Engine)
- Disease risk scoring
- Mandi (market) prices
- Agriculture news & advisories

…into **one simple dashboard** whose output is not data, but a decision.

### Product Principle (non-negotiable)

> **Do not show raw satellite data to farmers. Show decisions.**
>
> Every screen must answer three things: **Risk level (low/high)** — **Reason kya hai** — **Next action kya hai** (irrigate, spray, wait, or sell).

---

## 2. Problem Statement

Pakistani farmers make farming decisions on **scattered information**:

- Weather updates in one place, market rates in another, disease advisories from a separate source.
- Field-level crop health visibility is almost entirely missing.
- Fragmentation → **late decisions** → delayed response to crop stress/disease → **lost yield and profit**.

Farmers already receive plenty of information. What they lack is a simple answer to **"ab kya karna chahiye?"** (what should I do now?). Kisaan Dost replaces information overload with a **single decision layer**.

---

## 3. Target Users & Feature Mapping

### 3.1 User Segments

| # | Segment | Profile | Primary Pain | Priority |
|---|---------|---------|--------------|----------|
| 1 | **Small farmer** | ≤ 12 acres (≈5 ha), 1 plot, low-end Android, 2G/3G, Urdu-first, variable literacy | Needs quick, trustworthy answers; low tolerance for complex apps | **P0 — Primary** |
| 2 | **Medium farmer** | 12–100 acres, multiple plots, may hire labor, data-aware | Tracking several fields at once; disease & price timing | **P0 — Primary** |
| 3 | **Agri advisor** | Advises 20–200 farmers, smartphone/laptop | Needs overview of many client farms, not one | P1 (Phase 2) |
| 4 | **Farm manager** | Manages operations across farms | Multi-farm view, history, exports | P1 (Phase 2) |
| 5 | **Input seller** | Sells seed/fertilizer/pesticide | Wants regional outbreak & demand signals | P2 |
| 6 | **Cooperative / group operator** | Manages alerts for member farmers | Bulk alerts, aggregated area risk | P2 |

**Primary focus: small and medium farmers** — they need quick decision support the most and are underserved by feature-heavy competitors.

### 3.2 Persona Snapshots (build targets)

**Ahmed — Small farmer, Punjab (primary persona)**
- 6 acres of wheat/cotton, Android phone on 3G, reads Urdu comfortably, English barely.
- Opens app ~1×/day in the morning. Wants: "Aaj paani dena hai ya nahi? Koi khatra hai?"
- Success = one screen tells him today's risk + action in under 10 seconds.

**Fatima — Medium farmer, Sindh**
- 45 acres, 4 plots (wheat, sugarcane), tracks mandi rates weekly.
- Wants per-field health comparison, disease alerts before spread, best-time-to-sell signals.

**Bilal — Agri advisor**
- 80 client farmers across a district; uses the **web dashboard**.
- Wants a ranked list: which client farms have high risk today, and why — so he can call the right farmer first.

### 3.3 Feature-to-User Matrix (what to build, for whom)

| Feature | Small farmer | Medium farmer | Advisor | Farm mgr | Input seller | Co-op | Phase |
|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| Phone-number (OTP) onboarding | ● | ● | ● | ● | ● | ● | **1 (MVP)** |
| One-screen daily summary (risk + action) | ● | ● | ● | ● | ○ | ○ | **1 (MVP)** |
| Weather alerts (rain/heat/wind/frost, 48h) | ● | ● | ● | ● | ○ | ● | **1 (MVP)** |
| Farm profile + AOI (draw or pin location) | ● | ● | ● | ● | – | ● | **1 (MVP)** |
| Satellite crop health summary (NDVI/NDWI → status) | ● | ● | ● | ● | ○ | ○ | **1 (MVP)** |
| Risk score + one-action recommendation | ● | ● | ● | ● | ○ | ● | **1 (MVP)** |
| Mandi prices (district + crop, trend) | ● | ● | ○ | ○ | ● | ○ | **1 (MVP)** |
| Basic alerts (push + in-app) | ● | ● | ● | ● | ○ | ● | **1 (MVP)** |
| Disease risk scoring (KNN model) | ● | ● | ● | ● | ● | ○ | 2 |
| Crop-specific advisories (stage-aware) | ● | ● | ● | ○ | ○ | ○ | 2 |
| Historical trend charts (NDVI, prices) | ○ | ● | ● | ● | ○ | ○ | 2 |
| Multi-farm dashboard | – | ● | ● | ● | – | ● | 2 |
| Advisor portal (web, client list) | – | – | ● | – | – | – | 2 |
| AI explanations ("why is risk high") | ● | ● | ● | ○ | – | – | 3 |
| Voice alerts & summaries (Urdu) | ● | ○ | – | – | – | ○ | 3 |
| Advisory chat | ● | ● | ● | ○ | – | – | 3 |
| Yield / loss prediction | ○ | ● | ● | ● | – | – | 3 |

● = core need ○ = useful – = not a target user for that feature

---

## 4. MVP Scope (Phase 1)

**Only three things** — keeps the product focused and validation fast:

1. **Weather** — alerts & short forecast.
2. **Satellite crop health** — NDVI-based status per AOI.
3. **Mandi prices** — district/crop rates with "as of" time.

Plus the minimum platform around them: phone OTP auth, farm + AOI setup, risk score v1, basic alerts. Disease risk and news come **after** MVP validation.

### 4.1 Core Functional Requirements

#### F1 — Authentication & Onboarding
- F1.1 Login with phone number + OTP (SMS). No email required.
- F1.2 Language selection (Urdu default / English) at first launch, changeable in settings.
- F1.3 Onboarding under 90 seconds: phone → verify → name → first farm.
- F1.4 OTP rate limiting and generic failure messages (no user enumeration).

#### F2 — Farm & AOI Management
- F2.1 Create farm: name, crop, sowing date (optional), location.
- F2.2 AOI definition **two ways**: (a) draw boundary on map, (b) drop a pin + radius (for users uncomfortable with maps). **The map must never be mandatory.**
- F2.3 Backend validates polygon (self-intersection, min/max area 0.1–2,000 ha, single geometry).
- F2.4 Edit/delete farm; multiple farms per account (multi-farm UI only in Phase 2).

#### F3 — Weather
- F3.1 Current conditions + 48h forecast for farm location.
- F3.2 Alerts: heavy rain, high wind, heat wave, frost risk (crop-calendar aware where possible).
- F3.3 Weather shown *inside* the risk summary, not as a separate maze of screens.

#### F4 — Satellite Crop Health (GEE pipeline)
- F4.1 Backend sends AOI to Google Earth Engine via **service account only** (never from the client).
- F4.2 GEE computes NDVI mean, NDWI mean, and anomaly vs. multi-year baseline (`reduceRegion()` for single farm, `reduceRegions()` for batch).
- F4.3 Backend converts signals → crop health status (Good / Watch / Stress) + simple trend arrow.
- F4.4 Analysis is **asynchronous**: farmer sees last computed summary with its date; refresh happens in background ( Sentinel-2 revisit ≈ 5 days — no realtime expectation).
- F4.5 Raw raster/index values are **never** the primary UI — only status, reason, action.

#### F5 — Risk Engine & Recommendation (the differentiator)
- F5.1 Inputs: NDVI anomaly, NDWI (water stress), 7-day forecast (rain mm, temp extremes), crop type, season.
- F5.2 Output: **Risk level** (Low / Medium / High) + **up to 3 ranked reasons** + **one primary action** from: Irrigate / Spray / Wait / Harvest / Sell / Consult advisor.
- F5.3 Every output field bilingual (Urdu + English).
- F5.4 v1 is rules-based and explainable; ML (disease risk) layered on in Phase 2 without changing the output shape.

#### F6 — Mandi Prices
- F6.1 Prices by crop × district/mandi, latest rate + short trend (7-day).
- F6.2 Every price carries a visible "as of" timestamp; stale data (>48h) is labeled, never silently shown as fresh.
- F6.3 Prices feed the "Sell" recommendation signal.

#### F7 — Alerts & Notifications
- F7.1 Push (FCM) + in-app alert center.
- F7.2 Alert = level + reason + action + deep-link to the relevant farm screen. No long reports.
- F7.3 Quiet hours respectability (no pushes 10pm–6am unless risk = High).

### 4.2 User Flow (primary)

1. Farmer selects crop and location.
2. Creates/saves AOI (map draw **or** pin).
3. Backend enqueues AOI analysis to GEE.
4. GEE calculates NDVI, NDWI, anomaly signals.
5. Backend converts signals into a risk score + recommendation.
6. App shows plain-language recommendation.
7. History and alerts are saved for the user.

---

## 5. Phase 2 & 3 Roadmap

### Phase 2 — Intelligence
- **Disease risk scoring** — scikit-learn KNN on weather history + crop + region; upgrade path XGBoost / time-series.
- **Crop-specific advisories** — stage-aware (sowing, irrigation, fertilizer, harvest windows).
- **Historical trends** — NDVI history and price history charts per farm/crop.
- **Multi-farm dashboard** — mobile + web for medium farmers, managers.
- **Advisor portal (web)** — ranked client-farm risk list, advisory notes.

### Phase 3 — Assistance
- **AI explanations** — LLM-generated "why is the risk high" in Urdu/English.
- **Voice support** — spoken alerts and summaries.
- **Advisory chat** — conversational assistant.
- **Predictive yield / loss estimation.**

Future additions: farmer group management, multilingual expansion (Sindhi, Punjabi, Saraiki…).

---

## 6. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Language** | Urdu-first, fully bilingual UI (Urdu default, RTL-safe layouts). No hardcoded strings. |
| **Low bandwidth** | Dashboard usable on 2G/3G; alert payloads < 2 KB; lazy images; no video in core flows; graceful degradation. |
| **Performance** | Dashboard first paint < 3 s on 3G; API p95 < 500 ms (satellite analysis is async, never blocks a request). |
| **Offline tolerance** | Last known summary + prices cached with visible timestamps; app never shows a blank screen. |
| **Simplicity** | One-screen daily summary; map optional; ≤ 3 taps to any core feature. |
| **Security** | GEE credentials server-side only; OTP rate limits; AOI input validation; JWT expiry + refresh. |
| **Availability** | External-source failure (GEE/weather/prices) must degrade that module only — never the whole app. |
| **Explainability** | Every risk score must include human-readable reasons. No black-box output. |

---

## 7. Success Metrics

- Daily active users (DAU) & DAU/farm ratio
- AOIs monitored (total + per active user)
- Alert open rate
- **Recommendation action rate** — % of recommendations marked "done" / acted on within 24 h (the core product metric)
- Retention after one full crop cycle (Rabi → Kharif)

---

## 8. Competitive Landscape

| App | Strength | Gap Kisaan Dost exploits |
|---|---|---|
| BaKhabar Kissan | Broad ecosystem, weather stations, agri-store | Breadth → heavy, less focused decision experience |
| Kissan Madadgar | Practical alerts, market rates, pest advice | Advisory layer only; weak field-level satellite + explainable risk |
| Kissan Dost (existing app) | Prices, farm management, Q&A | Not risk-first, not decision intelligence |
| Khaity | AI sensing + satellite + marketplace | Feature-heavy → complexity risk for small farmers |
| **Kisaan Dost (us)** | **Risk-first decision copilot** | New product — needs validation (hence tight MVP) |

**Strategy:** do *not* become another broad agri super-app. Win on **simplicity, explainability, and action-first recommendations**.

---

## 9. Explicitly Out of Scope (v1)

- Marketplace / input e-commerce / input ordering
- Credit, loans, insurance sales
- IoT hardware / on-farm sensors
- Livestock management
- Direct GEE access from the client app
- Video streaming or heavy media features

---

## 10. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| GEE quota/cost & latency | Cache aggressively per farm+date; batch processing via `reduceRegions()`; async workers |
| Farmer trust in "AI" advice | Explainable reasons on every score; show data dates; conservative thresholds in v1 |
| Price data reliability | Multi-source ingestion; explicit "as of" timestamps; stale labeling |
| Push/SMS deliverability | FCM + in-app alert center as fallback |
| Urdu localization quality | Urdu-first copywriting, not translation afterthought; RTL-tested layouts |
| Feature creep toward super-app | This PRD's out-of-scope list is binding for MVP; new features require PRD amendment |
