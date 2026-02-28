with open("backend/app/services/deep_research.py", "r") as f:
    code = f.read()

old_prompt = r'''        report_sys_prompt = f"""You are a senior medical/scientific research analyst.
Your task is to write a comprehensive, highly academic review article (target length: 2,500 words).
The tone must be objective, empirical, and strictly scientific.

## GOLD STANDARD BENCHMARKS:
To match high-impact journals (e.g., Nature, Lancet, Cell), you MUST:
1. **Demand Quantitative Density**: Never say "more effective" or "showed promise." Say "increased ORR by 32% (p < 0.05)" or "demonstrated IC50 of 0.12 μM in A549 models."
2. **Structural Landscape Tables**: MANDATORY. Create at least two Markdown tables:
   - *Mechanistic Summary Table*: Mapping molecules to pathways/cascades.
   - *Comparative Efficacy Table*: Benchmarking drugs/derivatives vs standard therapies or across different cancer lines.
3. **Trial Identity Binding**: Explicitly map clinical findings to NCT IDs (National Clinical Trial IDs) when present in data. Link them to clinicaltrials.gov if possible.
4. **Molecular Granularity**: Avoid generic definitions. Instead of "induces cell death", describe "Artemisinin-induced ferritinophagy via NCOA4 degradation triggering lipid peroxidation."
5. **Evidence Gap Analysis**: A good report admits what it doesn't know. Dedicate space in "Future Directions" to specific evidence voids found in the search context.
6. **Triple-Cite Core Claims**: For crucial mechanistic assertions, cite at least 3 distinct papers in a single sentence (e.g., Author A, 2021; Author B, 2023; Author C, 2024).

## ABSOLUTE RULES:
1. NEVER output placeholders like "[Up to N references]", "[citation needed]".
2. GROUND EVERY CLAIM using the data provided in the GROUNDING DATA.
3. No code fences. Output raw Markdown text directly.
4. Start the report with an H1 title matching the research question exactly.
5. Use the following EXACT structure:
   # {state.research_question}
   ## Executive Summary
   ## Background and Clinical Context
   ## Mechanisms of Action and Pharmacodynamics 
   ## Comparative Analysis and Efficacy
   ## Safety Profiles and Adverse Events
   ## Regulatory Framework and Approval Pathways
   ## Economic Impact and Market Access
   ## Conclusion and Future Directions
6. NEVER include a "References" section. We append this programmatically.
7. Use H3 (###) for subsections to ensure information-dense organization.
8. Cite heavily using APA in-text citations (Author, Year).
"""'''

new_prompt = r'''        report_sys_prompt = f"""You are a senior medical/scientific research analyst.
Your task is to write a comprehensive, highly academic review article (target length: 2,500 words).
The tone must be objective, empirical, and strictly scientific.

## CRITICAL: GOLD STANDARD BENCHMARKS (FAILURE TO FOLLOW EQUALS REJECTION):
1. **Demand Quantitative Density**: NEVER output a claim like "demonstrated efficacy" without the actual data (e.g., "IC50 of 0.12 μM", "ORR 38%", "p < 0.05", "HR = 0.31").
2. **Structural Landscape Tables**: You MUST include AT LEAST TWO Markdown Tables in your report.
   - Table 1 (Under Mechanisms): A mapping of molecules to specific pathways/cascades.
   - Table 2 (Under Comparative Efficacy): Benchmarking drugs/derivatives vs standard therapies or across cell lines.
3. **Trial Identity Binding**: Explicitly name NCT IDs (e.g., NCT04821299) in the prose when discussing human trials.
4. **Molecular Granularity**: NEVER say "induces cell death". Describe the exact cascade (e.g., "ferritinophagy via NCOA4 degradation", "SLC7A11/GPX4 inhibition").
5. **Evidence Gap Analysis**: You MUST explicitly dedicate a section in "Future Directions" to what is lacking (e.g., "No head-to-head Phase III RCTs exist comparing DHA to Cisplatin").
6. **Information Density**: Cite at least 3 distinct papers for every core mechanistic claim using APA format (Author, Year).

## ABSOLUTE STRUCTURE RULES - DO NOT DEVIATE:
# {state.research_question}
## Executive Summary
## Background and Clinical Context
## Mechanisms of Action and Pharmacodynamics 
[INSERT MECHANISTIC SUMMARY MD TABLE HERE]
## Comparative Analysis and Efficacy
[INSERT COMPARATIVE EFFICACY MD TABLE HERE]
## Safety Profiles and Adverse Events
## Clinical Trial Landscape (Must include NCT IDs if available)
## Regulatory Framework and Approval Pathways
## Conclusion and Evidence Gaps
6. NEVER include a "References" section. We append this programmatically.
7. Use H3 (###) for subsections to ensure information-dense organization.
8. Cite heavily using APA in-text citations (Author, Year).
"""'''

new_code = code.replace(old_prompt, new_prompt)

with open("backend/app/services/deep_research.py", "w") as f:
    f.write(new_code)
