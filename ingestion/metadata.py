import os
import re
from pypdf import PdfReader


def extract_metadata(pdf_path: str) -> dict:
    """
    Automatically extracts metadata from a PDF.

    Priority:
    1. PDF metadata title
    2. First page title
    3. Filename

    Also detects:
    - Source organization
    - Disease category
    - Keywords
    - Publication year
    """

    filename = os.path.basename(pdf_path)
    filename_lower = filename.lower()

    reader = PdfReader(pdf_path)

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    title = None

    if reader.metadata and reader.metadata.title:
        title = reader.metadata.title.strip()

    if not title:

        first_page = reader.pages[0].extract_text() or ""

        lines = []

        for line in first_page.splitlines():

            line = line.strip()

            if len(line) > 3:
                lines.append(line)

            if len(lines) >= 3:
                break

        if lines:
            title = " ".join(lines)

    if not title:
        title = os.path.splitext(filename)[0]

    title = re.sub(r"\s+", " ", title).strip()

    title_lower = title.lower()

    # --------------------------------------------------
    # SOURCE ORGANIZATION
    # --------------------------------------------------

    source = "UNKNOWN"

    if (
        filename.startswith("978924")
        or "world health organization" in title_lower
        or "who" in title_lower
    ):
        source = "WHO"

    elif (
        "icmr" in filename_lower
        or "indian council of medical research" in title_lower
    ):
        source = "ICMR"

    elif (
        "mohfw" in filename_lower
        or "ministry of health" in title_lower
        or "government of india" in title_lower
    ):
        source = "MOHFW"

    elif "ntep" in filename_lower:
        source = "MOHFW"

    elif "npcdcs" in filename_lower:
        source = "MOHFW"

    elif "anemia" in filename_lower or "anaemia" in filename_lower:
        source = "MOHFW"

    # --------------------------------------------------
    # CATEGORY + KEYWORDS
    # --------------------------------------------------

    CATEGORY_MAPPING = {

        "Tuberculosis": [
            "tuberculosis",
            "tb",
            "ntep",
            "latent tb",
        ],

        "Diabetes": [
            "diabetes",
            "hba1c",
            "glucose",
            "insulin",
        ],

        "Stroke": [
            "stroke",
        ],

        "Hypertension": [
            "hypertension",
            "blood pressure",
        ],

        "Cardiovascular": [
            "heart",
            "cardiac",
            "cardiovascular",
        ],

        "Kidney Disease": [
            "kidney",
            "renal",
            "ckd",
            "nephrology",
        ],

        "COVID-19": [
            "covid",
            "covid-19",
            "coronavirus",
        ],

        "Malaria": [
            "malaria",
        ],

        "Dengue": [
            "dengue",
        ],

        "Anemia": [
            "anemia",
            "anaemia",
            "iron deficiency",
        ],

        "Maternal Health": [
            "pregnancy",
            "maternal",
            "antenatal",
            "postnatal",
            "obstetric",
        ],

        "Child Health": [
            "child",
            "newborn",
            "neonatal",
            "paediatric",
            "pediatric",
        ],

        "Cancer": [
            "cancer",
            "oncology",
            "tumour",
            "tumor",
        ],

        "Mental Health": [
            "mental",
            "depression",
            "anxiety",
            "psychiatric",
        ],

        "Nutrition": [
            "nutrition",
            "diet",
            "obesity",
            "micronutrient",
        ],

        "Public Health": [
            "public health",
            "health system",
            "sdg",
        ],
    }

    category = "General"

    keywords = []

    combined_text = (
        filename_lower + " " + title_lower
    )

    for disease, words in CATEGORY_MAPPING.items():

        if any(word in combined_text for word in words):

            category = disease

            keywords = words

            break

    # --------------------------------------------------
    # YEAR
    # --------------------------------------------------

    year = "Latest"

    years = re.findall(r"(20\d{2})", combined_text)

    if years:
        year = years[0]

    # --------------------------------------------------
    # DOCUMENT TYPE
    # --------------------------------------------------

    document_type = "Clinical Guideline"

    if "handbook" in combined_text:
        document_type = "Handbook"

    elif "manual" in combined_text:
        document_type = "Manual"

    elif "operational" in combined_text:
        document_type = "Operational Guideline"

    elif "report" in combined_text:
        document_type = "Report"

    # --------------------------------------------------

    return {

        "source_org": source,

        "doc_title": title,

        "doc_type": document_type,

        "version": year,

        "category": category,

        "keywords": keywords,
    }