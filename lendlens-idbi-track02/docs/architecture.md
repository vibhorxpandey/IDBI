# LendLens Architecture

LendLens is a multi-layered system designed for modularity, interpretability, and deterministic execution. Each component is a self-contained Python module that reads data from the previous stage and writes its output to disk. This makes the entire pipeline inspectable, testable, and easy to modify.

The architecture follows a logical flow from data ingestion to final lead presentation.

```
[ Data Layer ] -> [ Engine Layer ] -> [ Explainability & Fairness Layer ] -> [ Decisioning Layer ] -> [ Serving Layer ]
```

---

### 1. Data Layer

-   **Location:** `data/synthetic/`
-   **Components:** `generate.py`, `ingest_homecredit.py`
-   **Purpose:** To create a realistic, high-fidelity synthetic dataset that models the complexities of the target customer base. This layer is the foundation of the entire system.
-   **Justification:**
    -   **Deterministic:** The data generator (`generate.py`) is seeded (`RANDOM_STATE = 42`), ensuring that the exact same 5,001 customers and their associated transactions, behaviors, and ground-truth labels are created on every run. This makes the model training and evaluation perfectly reproducible.
    -   **Richness:** It generates not just customers, but also their monthly transactions, salary dates, life events (e.g., lease renewals), and web behavior (page visits). This rich feature set is crucial for the accuracy of the downstream engines.
    -   **Ground Truth:** Critically, this layer establishes a "true" income for each customer, distinct from their "declared" income, and a ground-truth default and conversion outcome. This allows us to rigorously validate the performance of our models against a known reality.
    -   **Optionality:** The `ingest_homecredit.py` script provides an optional path to blend the synthetic data with features from a real-world dataset, demonstrating how the system could be adapted to use external data sources.

---

### 2. Engine Layer

This is the core ML-driven layer where we derive key predictive insights. It's split into two distinct, parallel engines.

#### Engine A: Income & Repayment Capacity
-   **Location:** `engines/income_engine/`
-   **Purpose:** To solve the "documented income ≠ real income" problem and establish a safe affordability ceiling.
-   **Justification:**
    -   Standard affordability models that rely on declared income would incorrectly reject or under-serve a majority of gig-economy or self-employed workers.
    -   The `income_inference.py` module uses heuristics and time-series analysis on raw transaction data to estimate a customer's true, stable monthly income.
    -   The `features.py` module then calculates a maximum affordable EMI based on this inferred income, subject to a hard **50% Fixed Obligations to Income Ratio (FOIR)** cap defined in `config.py`.
    -   Finally, an XGBoost model (`train.py`, `infer.py`) predicts the probability of default, trained on features derived from the customer's real financial picture.

#### Engine B: Intent & Propensity + Uplift
-   **Location:** `engines/intent_engine/`
-   **Purpose:** To solve the "eligibility ≠ intent" problem by identifying not just who *can* take a loan, but who is *likely to want one* and will be *positively influenced* by an RM's outreach.
-   **Justification:**
    -   **Propensity:** A standard propensity model (`propensity.py`) predicts the likelihood of conversion. This is calibrated to provide a real-world probability.
    -   **Uplift (T-Learner):** This is the most critical part of the engine. A simple propensity model can't distinguish between "Sure Things" (will convert anyway), "Persuadables" (will convert *because* of outreach), and "Lost Causes" (will never convert). The `uplift.py` module implements a T-Learner (treatment-learner) model to explicitly isolate the causal impact of the RM's intervention. This allows us to focus RM effort exclusively on the "Persuadables," maximizing their efficiency.
    -   `features.py` generates behavioral features (e.g., page visits) and treatment/outcome flags needed for these models.

---

### 3. Explainability & Fairness Layer

-   **Location:** `explainability/`
-   **Purpose:** To build trust with the Relationship Manager and ensure the model's decisions are both transparent and equitable. A correct answer is useless if it's a black box.
-   **Justification:**
    -   **SHAP Reasons:** `shap_reasons.py` uses the SHAP (SHapley Additive exPlanations) library to generate reason codes for each lead. These are translated from model features into plain-English sentences that an RM can use to open a conversation (e.g., "I saw you recently visited our home loan page."). It also incorporates directly-detected life events for a hybrid approach that surfaces the most impactful drivers.
    -   **Fairness Gate:** `fairness_check.py` implements a critical compliance check using the `fairlearn` library. It calculates the disparate impact ratio for protected-class features (here, gender) and ensures it passes the **80% Rule**. If the model were to disadvantage a protected group, this gate would flag it, preventing biased leads from reaching the RM.

---

### 4. Decisioning Layer

-   **Location:** `decisioning/`
-   **Purpose:** To synthesize all the scores and predictions from the upstream layers into a final, actionable business decision.
-   **Justification:**
    -   **Uplift Suppression:** The first and most important gate. Any customer with a low uplift score (`< 0.02` in `config.py`) is suppressed from the lead list. This enforces the core strategy: do not waste RM time on customers who won't be influenced by outreach.
    -   **Tiering:** `lead_scorer.py` combines default risk, propensity, and uplift scores to segment the remaining leads into Gold, Silver, and Bronze tiers. This gives the RM a prioritized work queue.
    -   **Offer Engine:** `offer_engine.py` generates a concrete, pre-approved offer (Amount, Rate, Tenor, EMI) for each lead. It matches the customer to the best product (e.g., Home, Personal) based on their features and ensures the final EMI is strictly below their calculated affordability ceiling.

---

### 5. Serving Layer

-   **Location:** `api/` and `dashboard/`
-   **Purpose:** To deliver the generated leads to the end-user (the Relationship Manager) in a clean, interactive, and insightful format.
-   **Justification:**
    -   **API:** A `FastAPI` server (`api/main.py`) exposes the final `leads.json` file through a simple REST endpoint. It also includes mock endpoints for Account Aggregator, ULI, and OCEN to simulate the end-to-end data flow required in a production system. This decouples the backend pipeline from the frontend presentation.
    -   **Dashboard:** A modern frontend application built with **React, Vite, and TailwindCSS** (`dashboard/`) provides the RM interface. It's not just a list of names; it's a complete toolkit including a mock consent flow, a tiered lead queue, detailed customer views with reason codes, and portfolio-level analytics charts. This demonstrates the "last mile" of how the model's outputs translate into a usable business tool.