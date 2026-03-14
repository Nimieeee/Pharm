# ADMET Batch Analysis Report (Local Engine)

**Date:** 2026-03-13  
**Source File:** `top_20_mmgbsa.sdf`  
**Engine:** `admet-ai` v2 (Local Microservice)  
**Environment:** AWS Lightsail VPS (2 vCPUs, 8GB RAM)

## Executive Summary
This report summarizes the ADMET (Absorption, Distribution, Metabolism, Excretion, and Toxicity) profiles for 25 molecules processed using the local `admet-ai` machine learning engine. This approach provides a robust, high-performance alternative to external APIs, ensuring structural data remains private and analysis is available offline.

## Key Findings (Top 5 Molecules by QED)

| Molecule Name | MW | LogP | Lipinski | QED Score | PAINS Alert |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Compound 25014 | 270.33 | 3.48 | 4.0 | **0.91** | None |
| Compound 27651 | 286.33 | 3.13 | 4.0 | **0.94** | None |
| 135398522 | 307.31 | 2.35 | 4.0 | **0.83** | None |
| Compound 25575 | 286.28 | 2.56 | 4.0 | **0.83** | None |
| Compound 28330 | 256.26 | 2.55 | 4.0 | **0.77** | None |

## Technical Observations
- **Performance**: The batch of 25 molecules was processed in under 10 seconds locally.
- **Structural Alerts**: 5 molecules triggered PAINS alerts (Compound 28553, 25054, 28296, 25918, 28584). 
- **Interpretability**: The results include DrugBank percentiles, allowing for comparison against approved pharmaceuticals.

---

> [!NOTE]
> All predictions are based on Chemprop v2 models trained on Therapeutics Data Commons (TDC) datasets. QED (Quantitative Estimate of Drug-likeness) ranges from 0 to 1, with values > 0.5 generally considered drug-like.

## Full Data
The complete dataset with all 119 endpoints and DrugBank percentiles is available at: [admet_results.csv](file:///Users/mac/Desktop/phhh/research/results/admet_results.csv)
