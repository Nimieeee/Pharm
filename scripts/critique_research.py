import os
import sys
from dotenv import load_dotenv
from mistralai import Mistral

# Load environment
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    print("❌ Error: MISTRAL_API_KEY not found in environment.")
    sys.exit(1)

client = Mistral(api_key=api_key)

report_text = """
Artemisinin for Cancer research
Executive Summary

Artemisinin, a natural compound derived from the plant Artemisia annua, has been widely used as an antimalarial agent. Recent studies have shown that artemisinin and its derivatives exhibit potent anticancer activities, inducing apoptosis, autophagy, and cell cycle arrest in various cancer cell lines. This review aims to summarize the current state of knowledge on the use of artemisinin for cancer research, highlighting its mechanisms of action, efficacy, and potential applications.

Background and Clinical Context

Cancer is a leading cause of death worldwide, with an estimated 9.6 million deaths in 2018 (Mirza et al., 2019). The current standard treatments for cancer, such as chemotherapy and radiation therapy, often have significant side effects and may not be effective for all patients. Therefore, there is a need for new and innovative approaches to cancer treatment. Artemisinin, with its proven safety profile and efficacy against malaria, has emerged as a promising candidate for cancer therapy.

Mechanisms of Action and Pharmacodynamics

Artemisinin and its derivatives have been shown to exhibit anticancer activities through various mechanisms, including:

Inducing apoptosis (programmed cell death) in cancer cells (Dai et al., 2021)
Triggering autophagy (cellular self-digestion) in cancer cells (Luo et al., 2019)
Inhibiting cell proliferation and inducing cell cycle arrest in cancer cells (Chen et al., 2020)
Generating reactive oxygen species (ROS) and inducing oxidative stress in cancer cells (Chen et al., 2020)

The mechanisms of action of artemisinin and its derivatives are complex and multifaceted, involving the modulation of various cellular pathways and signaling networks.

Mechanistic Summary Table
CompoundMechanism of ActionCell Line
ArtemisininInduces apoptosisBreast cancer cells
DihydroartemisininTriggers autophagyLung cancer cells
ArtesunateInhibits cell proliferationColon cancer cells
Comparative Analysis and Efficacy

Artemisinin and its derivatives have been compared to standard chemotherapeutic agents in various preclinical studies. The results have shown that artemisinin-based compounds can be as effective as or even more effective than traditional chemotherapies in inhibiting cancer cell growth and inducing cell death.

Comparative Efficacy Table
CompoundEfficacyCell Line
ArtemisininIC50: 10 μMBreast cancer cells
DihydroartemisininIC50: 5 μMLung cancer cells
ArtesunateIC50: 2 μMColon cancer cells
Safety Profiles and Adverse Events

Artemisinin and its derivatives have been generally well-tolerated in clinical trials, with minimal adverse events reported. However, high doses of artemisinin have been associated with neurotoxicity and cardiotoxicity in some studies.

Regulatory Framework and Approval Pathways

Artemisinin is currently approved by the US FDA for the treatment of malaria. However, its use as an anticancer agent is still experimental and requires further clinical trials to establish safety and efficacy.

Economic Impact and Market Access

The development of artemisinin-based cancer therapies could have significant economic implications, potentially reducing healthcare costs associated with traditional chemotherapies. However, the market access for these therapies is still uncertain, pending regulatory approvals and reimbursement decisions.

Conclusion and Future Directions

Artemisinin and its derivatives have shown promising anticancer activities in preclinical studies. Further research is needed to fully elucidate their mechanisms of action, optimize their dosing regimens, and establish their safety and efficacy in clinical trials. The development of artemisinin-based cancer therapies could provide new hope for patients with refractory or relapsed cancers.

Evidence Gap Analysis

There are several evidence gaps that need to be addressed in future studies:

Limited understanding of the mechanisms of action of artemisinin-based compounds in cancer cells
Lack of standardized dosing regimens for artemisinin-based compounds in cancer therapy
Limited clinical trial data on the safety and efficacy of artemisinins in cancer patients

Addressing these evidence gaps will be crucial to advancing the development of artemisinins as anticancer agents.

References
Mirza et al. (2019). Journal of Clinical Oncology. https://doi.org/10.1200/JCO.2019.37.15SUPPL.5505
Luo et al. (2019). Chinese medicine. https://doi.org/10.1186/s13020-019-0270-9
Dai et al. (2021). International journal of biological sciences. https://doi.org/10.7150/ijbs.50364
Chen et al. (2020). Cell death and differentiation. https://doi.org/10.1038/s41418-019-0352-3
"""

critique_prompt = f"""
You are the Benchside Quality Assurance AI. Your goal is to critique the following research report against the **Benchside Gold Standard** for deep research.

### Benchside Gold Standard Criteria:
1. **Prose Density & Depth**: Avoid 1-2 sentence paragraphs. Every claim must be substantiated with technical depth (e.g., specifying molecular pathways like NF-κB, ROS/p38 MAPK, Ferroptosis via GPX4 inhibition).
2. **Quantitative Precision**: Tables must contain specific, verified data (IC50 values, clinical trial IDs like NCT01234567, percentage improvements). Avoid "round" placeholder numbers like 10μM or 5μM unless verified.
3. **Citation Density**: Every factual claim should have an inline citation. Matches between text and reference list must be 100% accurate.
4. **Structural Completeness**: Must include all 10 standard sections (Executive Summary, Background, Mechanisms, Comparative Analysis, Safety, Regulatory, Economic, Conclusion, Evidence Gap, References).
5. **Molecular Mapping**: Explicitly link compounds to specific biomolecular targets or pathways.

### Report to Critique:
{report_text}

### Output Format:
Provide a detailed critique in Markdown format.
1. **Score (0-100)**: Based on the Gold Standard.
2. **Critical Failures**: List any specific placeholders or low-density sections.
3. **Molecular Audit**: Check if pathways are explicitly named or just generic (e.g., "programmed cell death" vs "Bax/Bak-mediated mitochondrial outer membrane permeabilization").
4. **Quantitative Audit**: Evaluate the IC50 values and trial references.
5. **Actionable Suggestions**: How to bring this report to "Elite" status.
"""

print(f"🚀 Sending critique request to Mistral Large...")

try:
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {{"role": "user", "content": critique_prompt}}
        ]
    )
    print("\n--- CRITIQUE RESULT ---\n")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"❌ Error during API call: {e}")
