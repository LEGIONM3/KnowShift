"""
Sample document text content for KnowShift tests.
Realistic text that mirrors the actual demo data.
"""

# ── Medical ───────────────────────────────────────────────────────────────────
MEDICAL_FRESH_TEXT = """
DIABETES TREATMENT GUIDELINES 2024
American Diabetes Association Standards of Care

FIRST-LINE TREATMENT FOR TYPE 2 DIABETES (UPDATED):
GLP-1 receptor agonists and SGLT2 inhibitors are now recommended as
first-line therapy for patients with established cardiovascular disease,
heart failure, or chronic kidney disease, regardless of HbA1c level.

KEY 2024 UPDATES:
- Semaglutide recommended for weight management
- Tirzepatide shows superior HbA1c reduction
- Cardiovascular outcomes drive drug selection
- Metformin remains cost-effective option

DOSING GUIDELINES:
Semaglutide: 0.5 mg weekly, titrate to 2 mg
Tirzepatide: 2.5 mg weekly, max 15 mg

SOURCE: ADA Standards of Care 2024
PUBLISHED: January 2024
"""

MEDICAL_STALE_TEXT = """
DIABETES TREATMENT GUIDELINES 2021
American Diabetes Association Standards of Care

FIRST-LINE TREATMENT FOR TYPE 2 DIABETES:
Metformin remains the preferred initial pharmacological agent for
type 2 diabetes due to its efficacy, safety, and low cost.

RECOMMENDED DOSAGE:
Start with 500 mg twice daily with meals.
Increase gradually to 2000 mg/day maximum.
Monitor renal function regularly.

CONTRAINDICATIONS:
eGFR < 30 mL/min
Hepatic impairment

SOURCE: ADA Standards of Care 2021
PUBLISHED: January 2021
"""

# ── Finance ───────────────────────────────────────────────────────────────────
FINANCE_FRESH_TEXT = """
INCOME TAX RATES FY 2024-25
New Tax Regime (Default from FY 2024-25)

Income Slabs and Rates:
0 to 3 lakhs: NIL
3 to 7 lakhs: 5 percent
7 to 10 lakhs: 10 percent
10 to 12 lakhs: 15 percent (REDUCED from 20%)
12 to 15 lakhs: 20 percent
Above 15 lakhs: 30 percent

KEY CHANGES BUDGET 2024:
Standard deduction increased to Rs 75,000
Tax rebate limit raised to Rs 7 lakhs
New regime is now DEFAULT
Income 10-12 lakhs: rate reduced to 15%

SOURCE: Finance Bill 2024
PUBLISHED: July 2024
"""

FINANCE_STALE_TEXT = """
INCOME TAX RATES FY 2021-22
Old Tax Regime

Income Slabs and Rates:
Up to 2.5 lakhs: NIL
2.5 to 5 lakhs: 5 percent
5 to 7.5 lakhs: 10 percent
7.5 to 10 lakhs: 15 percent
10 to 12.5 lakhs: 20 percent
12.5 to 15 lakhs: 25 percent
Above 15 lakhs: 30 percent

SOURCE: Finance Bill 2021
PUBLISHED: February 2021
"""

# ── AI Policy ─────────────────────────────────────────────────────────────────
AI_POLICY_FRESH_TEXT = """
EU AI ACT FINAL 2024
Regulation (EU) 2024/1689

HIGH-RISK AI SYSTEMS - MANDATORY OBLIGATIONS:
Article 9: Risk management system required throughout lifecycle
Article 10: Data governance and quality criteria
Article 11: Technical documentation maintenance
Article 13: Transparency to users mandatory
Article 14: Human oversight measures required
Article 15: Accuracy and robustness standards

COMPLIANCE DEADLINES:
GPAI models: August 2025
High-risk systems: August 2026
All other provisions: August 2025

PENALTIES:
Up to 35 million EUR or 7% global annual turnover

SOURCE: Official Journal of the EU — July 2024
"""

AI_POLICY_STALE_TEXT = """
EU AI ACT DRAFT 2022
Commission Proposal COM/2021/0206

PROPOSED HIGH-RISK AI REQUIREMENTS (DRAFT):
Risk management systems (proposed)
Data governance measures (under negotiation)
Technical documentation (draft requirements)
Human oversight (proposed framework)

NOTE: This is a DRAFT document.
Timeline: TBD (estimated 2025-2026)
Requirements subject to change.

SOURCE: EU Commission AI Act Proposal
PUBLISHED: April 2022
"""

# ── Reusable chunk lists ──────────────────────────────────────────────────────
SAMPLE_CHUNKS: dict[str, list[str]] = {
    "medical": [
        "GLP-1 agonists recommended as first-line for T2D with CVD",
        "Semaglutide dosage: 0.5 mg weekly titrated to 2 mg",
        "SGLT2 inhibitors preferred in heart failure patients",
        "HbA1c target below 7% for most non-pregnant adults",
        "Continuous glucose monitoring recommended for all T1D",
    ],
    "finance": [
        "Income 10-12 lakhs taxed at 15% under new regime 2024",
        "Standard deduction increased to Rs 75,000 from FY 2024-25",
        "New tax regime is default from FY 2024-25 onwards",
        "Tax rebate available for income up to Rs 7 lakhs",
        "Surcharge of 10% on income between 50L and 1Cr",
    ],
    "ai_policy": [
        "EU AI Act enacted July 2024 as Regulation 2024/1689",
        "High-risk AI providers must implement risk management",
        "GPAI models must comply by August 2025",
        "Violations can result in fines up to 35 million EUR",
        "Transparency obligations apply to all AI systems",
    ],
}
