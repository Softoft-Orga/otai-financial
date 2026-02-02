# Customer Acquisition Model (3 Channels)

We model **3 distinct inflow channels** that produce **leads** (HQ/LQ), which then flow through the funnel:
Website User → Lead → Free → Pro → Enterprise  
Plus optional Partner deals and Referral effects later.

---

## 1) Channel overview

```mermaid
flowchart TD
  LG["LeadGen / Direct Outreach<br/>cold contact via research tool"] --> L["Leads Pool<br/>HQ + LQ"]

  ADS["Paid Ads<br/>€ spend -> clicks"] --> W[Website Users]
  SEO["SEO + Social<br/>€ spend -> organic traffic"] --> W

  W --> WL["Website Leads<br/>(conv_web_to_lead)"]
  WL --> L

  L --> F[Free Users]
  F --> P[Pro Users]
  P --> E[Enterprise Users]
````

---

## 2) What each channel outputs

| Channel            | Input (decision)                  | Output (calculated)                             | Notes                         |
| ------------------ | --------------------------------- | ----------------------------------------------- | ----------------------------- |
| LeadGen / Outreach | `leadgen_hq[t]`, `leadgen_lq[t]`  | leads directly                                  | does not need website traffic |
| Ads                | `ads_spend[t]`, CPC               | `ads_clicks[t]` → website users → website leads | CPC is an assumption          |
| SEO / Social       | `seo_spend[t]`, `social_spend[t]` | `seo_stock[t]` → website users → website leads  | compounding stock + decay     |

---

## 3) Simple formulas (per month)

### 3.1 Ads → website users

* `ads_clicks[t] = ads_spend[t] / cpc`

### 3.2 SEO/Social → website users (stock)

* `seo_stock[t+1] = seo_stock[t] * (1 - seo_decay) + seo_spend[t] * seo_eff`

### 3.3 Total website users

* `website_users[t] = base_organic_users + seo_stock[t] + ads_clicks[t]`

### 3.4 Website users → website leads (split HQ/LQ)

* `website_leads[t] = website_users[t] * conv_web_to_lead`
* `website_leads_hq = website_leads * hq_share_website`
* `website_leads_lq = website_leads * (1 - hq_share_website)`

### 3.5 Total leads pool

* `leads_hq = website_leads_hq + leadgen_hq[t]`
* `leads_lq = website_leads_lq + leadgen_lq[t]`
* `leads_total = leads_hq + leads_lq`

```mermaid
flowchart TD
  %% Inputs (spend)
  SEO["seoSpend €/mo"] -->|content+links| DR[domainRating / DR]
  LI["linkedinSpend €/mo"] -->|content+distribution| F[linkedinFollowers]
  ADS["adsSpend €/mo"] --> AUC[adAuctions]

  %% Compounding growth (brand assets)
  DR -->|improves rank/CTR| SEOv[seoVisitors]
  F -->|improves reach| LIimp[linkedInImpressions]

  %% SEO funnel
  SEOv --> SEOleads[seoLeads]
  DR -->|trust boost| CR[siteTrust/Brand]
  CR -->|+seo conversion| SEOleads

  %% LinkedIn organic funnel
  LIimp --> LIclicks[linkedInClicks]
  LIclicks --> LIleads[linkedInLeads]
  CR -->|+LI conversion| LIleads

  %% Paid ads funnel (non-linear costs)
  AUC --> CPC[CPC]
  AUC --> CPA[CPA]
  ADS -->|more spend raises competition| CPC
  ADS -->|more spend raises CPA| CPA
  CPC --> AdClicks[adClicks = adsSpend/CPC]
  AdClicks --> AdLeads[adLeads]
  CR -->|+ads conversion| AdLeads

  %% Exponential cost curves (simplified)
  CPC -.->|"CPC = c0 * exp(kC*adsSpend)"| CPC
  CPA -.->|"CPA = a0 * exp(kA*adsSpend)"| CPA
  DR -.->|reduces effective CPA| CPA
  F -.->|reduces effective CPA| CPA

  %% Lead totals
  SEOleads --> Total[totalLeads]
  LIleads --> Total
  AdLeads --> Total
```
