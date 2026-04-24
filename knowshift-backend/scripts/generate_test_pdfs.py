"""
KnowShift — Generate Demo Test PDFs
Uses reportlab to create realistic domain-specific PDFs locally.

Usage:
    pip install reportlab
    python scripts/generate_test_pdfs.py

Outputs 6 PDFs to ./demo_data/:
  medical_2021_guidelines.pdf
  medical_2024_guidelines.pdf
  finance_tax_2021.pdf
  finance_tax_2024.pdf
  ai_policy_draft_2022.pdf
  ai_policy_enacted_2024.pdf
"""

import io
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Content blocks (deliberately realistic but clearly synthetic)
# ---------------------------------------------------------------------------

MEDICAL_PAST = """
DIABETES TREATMENT GUIDELINES 2021
American Diabetes Association Standards of Care

FIRST-LINE TREATMENT FOR TYPE 2 DIABETES:
Metformin remains the preferred initial pharmacological
agent for type 2 diabetes due to its efficacy, safety,
and low cost.

RECOMMENDED DOSAGE:
- Start with 500mg twice daily with meals
- Increase gradually to 2000mg/day maximum
- Monitor renal function regularly

CONTRAINDICATIONS:
- eGFR < 30 mL/min/1.73m2
- Hepatic impairment
- Iodinated contrast procedures

NOTE: GLP-1 receptor agonists are second-line agents
for patients with established cardiovascular disease.

SOURCE: ADA Standards of Care 2021
PUBLISHED: January 2021
VALIDITY: 12 months
"""

MEDICAL_FRESH = """
DIABETES TREATMENT GUIDELINES 2024
American Diabetes Association Standards of Care

FIRST-LINE TREATMENT FOR TYPE 2 DIABETES (UPDATED 2024):
GLP-1 receptor agonists and SGLT2 inhibitors are now
recommended as FIRST-LINE therapy for patients with
established cardiovascular disease, heart failure, or
chronic kidney disease, regardless of HbA1c level.

UPDATED RECOMMENDATIONS 2024:
- Semaglutide (Ozempic/Wegovy): 0.5mg weekly, titrate to 2mg
- Tirzepatide (Mounjaro): Superior HbA1c reduction vs semaglutide
- Metformin: Still recommended for cost-sensitive patients
- SGLT2 inhibitors: Preferred in heart failure patients

KEY CHANGES FROM 2021:
- GLP-1 agonists ELEVATED to first-line status
- Weight management now PRIMARY treatment goal
- Cardiovascular risk drives drug selection, not HbA1c alone

SOURCE: ADA Standards of Care 2024
PUBLISHED: January 2024
VALIDITY: 12 months
"""

FINANCE_PAST = """
INCOME TAX RATES FY 2021-22
Government of India - Finance Ministry

OLD TAX REGIME - APPLICABLE RATES:

Income Slab           | Tax Rate
----------------------|----------
Up to Rs 2.5 lakhs   | Nil
2.5 to 5 lakhs        | 5%
5 to 7.5 lakhs        | 10%
7.5 to 10 lakhs       | 15%
10 to 12.5 lakhs      | 20%
12.5 to 15 lakhs      | 25%
Above 15 lakhs        | 30%

SURCHARGE:
- Income 50L-1Cr: 10% surcharge
- Income above 1Cr: 15% surcharge

NOTE: New tax regime is optional for FY 2021-22.
SOURCE: Income Tax Act, Finance Bill 2021
PUBLISHED: February 2021
"""

FINANCE_FRESH = """
INCOME TAX RATES FY 2024-25
Government of India - Finance Ministry

NEW TAX REGIME (DEFAULT FROM FY 2024-25):

Income Slab           | Tax Rate
----------------------|----------
Up to Rs 3 lakhs     | Nil
3 to 7 lakhs          | 5%
7 to 10 lakhs         | 10%
10 to 12 lakhs        | 15%  << REDUCED FROM 20%
12 to 15 lakhs        | 20%
Above 15 lakhs        | 30%

KEY CHANGES FROM BUDGET 2024:
- Standard deduction increased to Rs 75,000
- New regime is now DEFAULT regime
- Tax rebate limit raised to Rs 7 lakhs (was Rs 5L)
- Income 10-12 lakhs: Rate REDUCED from 20% to 15%

OLD REGIME: Still available by explicit opt-in.
SOURCE: Finance Bill 2024, Budget 2024-25
PUBLISHED: July 2024
"""

AI_POLICY_PAST = """
EU AI ACT - DRAFT PROVISIONS 2022
European Commission Proposal COM/2021/206

HIGH-RISK AI SYSTEMS - DRAFT OBLIGATIONS:
[DRAFT - NOT FINAL - Subject to legislative process]

Proposed requirements for high-risk AI providers:
1. Risk management systems (proposed)
2. Data governance measures (under negotiation)
3. Technical documentation (draft requirements)
4. Human oversight measures (proposed)
5. Accuracy and robustness (guidelines pending)

COMPLIANCE TIMELINE (estimated):
- Entry into force: TBD (estimated 2024)
- Full compliance: TBD (estimated 2025-2026)

NOTE: This is a DRAFT document. All requirements
subject to change through legislative process.
SOURCE: EU AI Act Proposal 2021/0106(COD)
PUBLISHED: April 2022
"""

AI_POLICY_FRESH = """
EU AI ACT - FINAL ENACTED TEXT 2024
Official Journal of the European Union

HIGH-RISK AI SYSTEMS - LEGAL OBLIGATIONS (FINAL):
[LEGALLY BINDING - Regulation (EU) 2024/1689]

MANDATORY requirements for high-risk AI providers:
1. RISK MANAGEMENT: Article 9 — Continuous assessment
   required throughout entire lifecycle.
2. DATA GOVERNANCE: Article 10 — Training data must
   meet quality criteria; bias monitoring mandatory.
3. TECHNICAL DOCUMENTATION: Article 11 — Must be
   maintained, updated before market placement.
4. TRANSPARENCY: Article 13 — Users must be informed
   of AI system capabilities and limitations.
5. HUMAN OVERSIGHT: Article 14 — Mandatory human
   review for high-risk decisions.
6. ACCURACY: Article 15 — Performance metrics must
   be declared and monitored continuously.

COMPLIANCE DEADLINES (LEGALLY BINDING):
- GPAI models: August 2025
- High-risk systems: August 2026
- All other provisions: August 2025

SOURCE: EU AI Act Regulation (EU) 2024/1689
PUBLISHED: July 2024 (Official Journal)
"""

# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def create_pdf(content: str) -> bytes:
    """Convert plain text to PDF bytes using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        raise SystemExit(
            "❌ reportlab not installed.\n"
            "   Run: pip install reportlab\n"
        )

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Courier", 10)

    y = 750
    for line in content.strip().splitlines():
        if y < 60:
            c.showPage()
            c.setFont("Courier", 10)
            y = 750
        c.drawString(50, y, line)
        y -= 14

    c.save()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

PDF_MAP = {
    "medical_2021_guidelines.pdf":  MEDICAL_PAST,
    "medical_2024_guidelines.pdf":  MEDICAL_FRESH,
    "finance_tax_2021.pdf":         FINANCE_PAST,
    "finance_tax_2024.pdf":         FINANCE_FRESH,
    "ai_policy_draft_2022.pdf":     AI_POLICY_PAST,
    "ai_policy_enacted_2024.pdf":   AI_POLICY_FRESH,
}


def generate_all_pdfs(output_dir: str = "demo_data") -> list[str]:
    """Generate all 6 demo PDFs and write to output_dir."""
    Path(output_dir).mkdir(exist_ok=True)

    generated = []
    for filename, content in PDF_MAP.items():
        path = Path(output_dir) / filename
        pdf_bytes = create_pdf(content)
        path.write_bytes(pdf_bytes)
        size_kb = round(len(pdf_bytes) / 1024, 1)
        print(f"  ✅ {filename}  ({size_kb} KB)")
        generated.append(str(path))

    print(f"\n✅ {len(generated)} demo PDFs written to ./{output_dir}/")
    return generated


if __name__ == "__main__":
    print("=" * 55)
    print("KnowShift — Demo PDF Generator")
    print("=" * 55)
    generate_all_pdfs()
