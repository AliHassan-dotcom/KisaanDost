# AMIS Punjab Source Access & Transport Validation Report

- **Source Name:** Agriculture Marketing Information Service (AMIS), Directorate of Agriculture (Economics & Marketing) Punjab, Lahore
- **Base Website:** `http://www.amis.pk/`
- **Verified Commodity Price URL Template:** `http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId={COMMODITY_ID}`
- **Generated At (UTC):** `2026-09-01T21:50:00+00:00`
- **Validation Status:** **VERIFIED / ACCESSIBLE**

---

## 1. Source Transport & Protocol Behavior

1. **Protocol Exception:**
   - AMIS serves pages over plain HTTP (`http://www.amis.pk/`).
   - Connecting via HTTPS triggers a transport error (`server gave HTTP response to HTTPS client`).
   - In accordance with the approved safety specification, standard HTTP GET requests are used strictly for backend-to-AMIS collection. Mobile-to-backend communication remains HTTPS.

2. **Robots Policy & Access Controls:**
   - `http://www.amis.pk/robots.txt` returned HTTP 404 Not Found (no explicit crawler restrictions or disallow directives).
   - No CAPTCHAs, bot challenges, JavaScript obfuscations, or private session cookies were encountered on public commodity view pages.

3. **Rate & Concurrency Controls:**
   - Max 1 request per allowlisted commodity per manual run.
   - User-Agent header: `KisaanDost-MarketConnector/1.0 (Agricultural Platform POC)`.
   - Outbound timeout: 10.0 seconds.
   - Zero automated background polling or cron scheduling.

---

## 2. Allowlisted Commodities Verified

| Commodity ID | Commodity Label on AMIS | Verified In HTML | Displayed Unit | URL Checked |
|---|---|---|---|---|
| **1** | Wheat | `<span>Wheat</span>` | `Rs/100Kg` (1 Quintal = 100 Kg) | `http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=1` |
| **21** | Potato Fresh | `<span>Potato Fresh</span>` | `Rs/100Kg` (1 Quintal = 100 Kg) | `http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=21` |
| **22** | Potato Store | `<span>Potato Store</span>` | `Rs/100Kg` (1 Quintal = 100 Kg) | `http://www.amis.pk/ViewPrices.aspx?searchType=0&commodityId=22` |

---

## 3. HTML Markup & Table Selectors

- **Page Form ID:** `aspnetForm`
- **Date Selector Input:** `ctl00_cphPage_DateTextBox`
- **Commodity Label Span:** `ctl00_cphPage_lblMsg`
- **Unit Note Span:** `ctl00_cphPage_lblquintal` (e.g. `[ All Prices are in Rs/100Kg specified otherwise ]`)
- **Price Grid Container:** `<td id="ctl00_cphPage_Grd"> <table ...>`
- **Header Row:** Contains `Dated:DD-MM-YYYY`, `Graph`, `Min`, `Max`, `FQP`, `Quantity`.
- **Data Rows:** Each market entry contains market ID/name, Graph link, Min price, Max price, FQP (Frequently Quoted Price), and Arrival Quantity.
- **Null Value Notation:** Unreported or non-trading markets display `-`, preserved strictly as `null` in parsed numerical fields.
