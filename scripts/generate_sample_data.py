"""
Generates synthetic (non-copyrighted) clinical-guideline-style PDFs so the
pipeline can be demoed end-to-end without needing real WHO/ICMR source files.
Replace these with real guideline PDFs + .meta.json sidecars for production use.
"""
import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

SAMPLE_DOCS = [
    {
        "filename": "who_hypertension_2023.pdf",
        "meta": {
            "source_org": "WHO",
            "doc_title": "Guideline for the Pharmacological Treatment of Hypertension in Adults",
            "doc_type": "guideline",
            "version": "2023",
        },
        "pages": [
            "1. INTRODUCTION\n\nHypertension remains a leading modifiable risk factor "
            "for cardiovascular disease globally. This guideline provides "
            "evidence-based recommendations for pharmacological management in adults.",
            "2. FIRST-LINE THERAPY\n\nRecommendation: Initiate treatment with one of "
            "the following drug classes: thiazide or thiazide-like diuretics, ACE "
            "inhibitors, angiotensin receptor blockers, or long-acting calcium "
            "channel blockers, guided by patient comorbidities and tolerability.",
            "3. TREATMENT THRESHOLDS\n\nPharmacological treatment is recommended for "
            "adults with confirmed office blood pressure of 140 over 90 mmHg or "
            "higher, following lifestyle intervention where appropriate.",
        ],
    },
    {
        "filename": "icmr_diabetes_2022.pdf",
        "meta": {
            "source_org": "ICMR",
            "doc_title": "National Guidelines for Management of Type 2 Diabetes",
            "doc_type": "guideline",
            "version": "2022",
        },
        "pages": [
            "1. SCREENING\n\nOpportunistic screening for type 2 diabetes is "
            "recommended for adults above 30 years of age with one or more risk "
            "factors, including family history and elevated BMI.",
            "2. GLYCEMIC TARGETS\n\nFor most non-pregnant adults, an HbA1c target of "
            "below 7 percent is recommended, individualized based on comorbidity "
            "burden, hypoglycemia risk, and disease duration.",
            "3. FIRST-LINE PHARMACOTHERAPY\n\nMetformin is recommended as first-line "
            "pharmacotherapy in the absence of contraindications, alongside "
            "structured lifestyle modification counseling.",
        ],
    },
]


def make_pdf(path: str, page_texts: list[str]):
    c = canvas.Canvas(path, pagesize=A4)
    for text in page_texts:
        y = 800
        for line in text.split("\n"):
            # naive wrap so lines don't run off the page
            while len(line) > 95:
                c.drawString(50, y, line[:95])
                line = line[95:]
                y -= 18
            c.drawString(50, y, line)
            y -= 22
        c.showPage()
    c.save()


def main(output_dir: str = "data/raw_guidelines"):
    os.makedirs(output_dir, exist_ok=True)
    for doc in SAMPLE_DOCS:
        pdf_path = os.path.join(output_dir, doc["filename"])
        make_pdf(pdf_path, doc["pages"])
        with open(pdf_path.replace(".pdf", ".meta.json"), "w") as f:
            json.dump(doc["meta"], f)
    print(f"Generated {len(SAMPLE_DOCS)} sample guideline PDFs in {output_dir}")


if __name__ == "__main__":
    main()
