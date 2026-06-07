from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


OUT = Path("MediGuard_Full_Report_NAHPI.docx")


TITLE = "DESIGN AND IMPLEMENTATION OF MEDIGUARD FOR AI DISEASE SCREENING IN BAMENDA"
CANDIDATE = "AFI FONDZENYUY ADRINE-BRIDE"
REG_NO = "UBa22E0257"
SUPERVISOR = "NAME OF SUPERVISOR"
DEPARTMENT = "DEPARTMENT OF COMPUTER ENGINEERING"
INSTITUTE = "NATIONAL HIGHER POLYTECHNIC INSTITUTE"
UNIVERSITY = "THE UNIVERSITY OF BAMENDA"


def set_cell_text(cell, text: str, bold: bool = False, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_page_number(paragraph, roman: bool = False):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE \\* roman" if roman else "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def set_pg_num_format(section, fmt: str, start: int = 1):
    sect_pr = section._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is None:
        pg_num = OxmlElement("w:pgNumType")
        sect_pr.append(pg_num)
    pg_num.set(qn("w:fmt"), fmt)
    pg_num.set(qn("w:start"), str(start))


def add_toc(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r'TOC \o "1-3" \h \z \u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    paragraph.add_run("Right-click and update field to refresh page numbers.")
    run2 = paragraph.add_run()
    run2._r.append(fld_end)


def add_static_toc(doc: Document):
    entries = [
        ("DECLARATION OF ORIGINALITY OF STUDY", "iii", 0),
        ("CERTIFICATION", "iv", 0),
        ("ABSTRACT", "v", 0),
        ("RESUME", "vi", 0),
        ("DEDICATION", "vii", 0),
        ("ACKNOWLEDGEMENTS", "viii", 0),
        ("LIST OF TABLES", "x", 0),
        ("LIST OF FIGURES", "xi", 0),
        ("LIST OF ABBREVIATIONS", "xii", 0),
        ("CHAPTER ONE: GENERAL INTRODUCTION", "1", 0),
        ("1.1 Background of the Study", "1", 1),
        ("1.2 Problem Statement", "3", 1),
        ("1.3 Research Questions", "5", 1),
        ("1.4 Research Objectives", "6", 1),
        ("1.5 Significance of the Study", "7", 1),
        ("1.6 Scope of the Study", "7", 1),
        ("1.7 Limitations of the Study", "8", 1),
        ("1.8 Definition of Key Terms", "9", 1),
        ("1.9 Organization of Chapters", "10", 1),
        ("CHAPTER TWO: LITERATURE REVIEW", "12", 0),
        ("2.1 Introduction", "12", 1),
        ("2.2 Generalities", "12", 1),
        ("2.3 An Overview of Machine Learning in Disease Prediction", "14", 1),
        ("2.4 Limitations of Existing Health Information Systems", "17", 1),
        ("2.5 Context and Critical Analysis", "18", 1),
        ("2.6 Theoretical Framework", "19", 1),
        ("2.7 Review of Machine Learning Algorithms", "20", 1),
        ("2.8 Retrieval-Augmented Generation in Healthcare", "22", 1),
        ("2.9 Digital Health in the African Context", "22", 1),
        ("2.10 Ethical and Social Dimensions", "23", 1),
        ("2.11 Proposition of Solution", "24", 1),
        ("2.12 Partial Conclusion", "25", 1),
        ("CHAPTER THREE: RESEARCH METHODOLOGY AND MATERIALS USED", "26", 0),
        ("3.1 Introduction", "26", 1),
        ("3.2 Description of the System Architecture", "26", 1),
        ("3.3 Data Collection", "29", 1),
        ("3.4 Modeling Methods", "30", 1),
        ("3.5 Identification of Actors", "31", 1),
        ("3.6 System Decomposition into Packages", "32", 1),
        ("3.7 Use Case Diagram", "33", 1),
        ("3.8 Sequence Diagrams", "36", 1),
        ("3.9 Class Diagram", "37", 1),
        ("3.10 From Class Diagram to Relational Model", "38", 1),
        ("3.11 Materials Used", "41", 1),
        ("3.12 Languages Used", "43", 1),
        ("3.13 Partial Conclusion", "47", 1),
        ("CHAPTER FOUR: RESULTS AND DISCUSSION", "48", 0),
        ("4.1 Introduction", "48", 1),
        ("4.2 Description of the Final Application", "49", 1),
        ("4.3 Functional Testing Results", "52", 1),
        ("4.4 Discussion of Results", "53", 1),
        ("4.5 Limitations of the Implemented System", "55", 1),
        ("4.6 Partial Conclusion", "55", 1),
        ("CHAPTER FIVE: GENERAL CONCLUSION AND RECOMMENDATIONS", "56", 0),
        ("5.1 General Conclusion", "56", 1),
        ("5.2 Recommendations", "59", 1),
        ("REFERENCES", "61", 0),
        ("APPENDIX A: SELECTED MEDIGUARD API ENDPOINTS", "65", 0),
    ]
    for title, page, level in entries:
        para = doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(0.7 * level)
        para.paragraph_format.line_spacing = 1.5
        para.paragraph_format.space_after = Pt(0)
        left = para.add_run(title)
        left.font.name = "Times New Roman"
        left.font.size = Pt(12)
        if level == 0:
            left.bold = True
        para.add_run(" " + "." * max(6, 78 - len(title) - (level * 6)) + " ")
        right = para.add_run(page)
        right.font.name = "Times New Roman"
        right.font.size = Pt(12)


def make_doc() -> Document:
    doc = Document()

    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(3.5)
    sec.right_margin = Cm(2.5)
    set_pg_num_format(sec, "lowerRoman", 1)
    add_page_number(sec.footer.paragraphs[0], roman=True)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_after = Pt(6)

    for name, size in [("Title", 14), ("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)]:
        st = styles[name]
        st.font.name = "Times New Roman"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.line_spacing = 1.5
        st.paragraph_format.space_before = Pt(12 if name != "Heading 3" else 6)
        st.paragraph_format.space_after = Pt(6)
    styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    return doc


def p(doc, text: str = "", style: str | None = None, align=None, bold=False):
    para = doc.add_paragraph(style=style)
    if align is not None:
        para.alignment = align
    run = para.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    return para


def heading(doc, text: str, level: int = 1):
    return p(doc, text, f"Heading {level}")


def page_break(doc):
    doc.add_page_break()


def table(doc, caption: str, headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
    cap = p(doc, caption, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True)
    cap.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], h, True, WD_ALIGN_PARAGRAPH.CENTER)
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            set_cell_text(cells[i], text)
    if widths:
        for row in t.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Inches(width)
    p(doc)
    return t


def figure_box(doc, caption: str, lines: list[str]):
    t = doc.add_table(rows=1, cols=1)
    t.style = "Table Grid"
    cell = t.cell(0, 0)
    cell.text = ""
    for line in lines:
        para = cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = para.add_run(line)
        r.font.name = "Courier New"
        r.font.size = Pt(9)
    cap = p(doc, caption, align=WD_ALIGN_PARAGRAPH.LEFT)
    cap.paragraph_format.keep_with_next = False
    p(doc)


def prelim(doc: Document):
    for is_title_page in [False, True]:
        for text, size, bold in [
            (UNIVERSITY, 14, True),
            (INSTITUTE, 13, True),
            (DEPARTMENT, 12, True),
        ]:
            para = p(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, bold=bold)
            para.runs[0].font.size = Pt(size)
        p(doc)
        t = p(doc, TITLE, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        t.runs[0].font.size = Pt(14)
        p(doc)
        p(
            doc,
            "A Project Submitted to the Department of Computer Engineering in the National Higher Polytechnic Institute of The University of Bamenda in Partial Fulfillment of the Requirements for the Award of a Bachelor of Engineering Degree in Computer Engineering.",
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        p(doc)
        p(doc, "BY:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        p(doc, CANDIDATE, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        p(doc, f"REGISTRATION NUMBER: {REG_NO}", align=WD_ALIGN_PARAGRAPH.CENTER)
        p(doc)
        p(doc, "SUPERVISOR:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        p(doc, SUPERVISOR, align=WD_ALIGN_PARAGRAPH.CENTER)
        p(doc)
        p(doc, "JUNE, 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
        page_break(doc)

    p(doc, f"(c) Copyright by {CANDIDATE}, 2026", align=WD_ALIGN_PARAGRAPH.CENTER)
    p(doc, "All rights reserved", align=WD_ALIGN_PARAGRAPH.CENTER)
    page_break(doc)

    heading(doc, "DECLARATION OF ORIGINALITY OF STUDY")
    p(doc, f'I, {CANDIDATE}, registration number {REG_NO}, in the {DEPARTMENT.title()}, {INSTITUTE.title()}, {UNIVERSITY.title()} hereby declare that this work titled "{TITLE.title()}" is my original work and has not been submitted in whole or in part for the award of any degree in this or any other institution.')
    p(doc)
    p(doc, "Date: ___________________        Signature of author: ___________________")
    page_break(doc)

    heading(doc, "CERTIFICATION")
    p(doc, f'This is to certify that this project titled "{TITLE.title()}" is the original work of {CANDIDATE}. This work is submitted in partial fulfillment of the requirements for the award of a Bachelor of Engineering Degree in Computer Engineering.')
    p(doc)
    p(doc, f"Supervisor: ____________________________________   {SUPERVISOR}")
    p(doc, "Head of Department: ____________________________")
    page_break(doc)

    heading(doc, "ABSTRACT")
    p(doc, "Access to timely preliminary health guidance remains a major challenge in many communities within the Bamenda Health District, where patients may delay consultation because of distance, cost, insecurity, limited medical personnel, or uncertainty about the seriousness of symptoms. This project designed and implemented MediGuard, a web-based AI disease screening and health guidance system for Bamenda. The study adopted an iterative software engineering methodology supported by user needs assessment, UML modelling, supervised machine learning, and retrieval-augmented generation. The final system was implemented with a React/Vite frontend, a FastAPI backend, SQLAlchemy database access, Scikit-learn disease prediction models, fuzzy symptom normalization, a disease library, RAG-based chat support, nearby facility guidance, user history, newsletter alerts, and administrative analytics. Functional testing showed that the core modules performed their intended roles: users can register, submit symptoms, receive ranked disease screening results with safety disclaimers, ask health questions, browse disease information, view screening history, and access community trend summaries. The system improves health awareness and supports earlier health-seeking behavior, but it remains a decision-support tool and does not replace clinical diagnosis, laboratory testing, or professional medical care.")
    p(doc, "Keywords: MediGuard, artificial intelligence, disease screening, machine learning, Bamenda", bold=True)
    page_break(doc)

    heading(doc, "RESUME")
    p(doc, "L'acces a une orientation sanitaire preliminaire et rapide reste un defi important dans plusieurs communautes du district de sante de Bamenda. Ce projet a concu et implemente MediGuard, un systeme web de depistage de maladies et d'orientation sanitaire base sur l'intelligence artificielle. La methodologie a combine l'analyse des besoins, la modelisation UML, l'apprentissage automatique supervise et la generation augmentee par recuperation. Le systeme final utilise une interface React/Vite, une API FastAPI, SQLAlchemy, des modeles Scikit-learn, la normalisation floue des symptomes, une bibliotheque de maladies, un assistant conversationnel RAG, la localisation des formations sanitaires, l'historique des utilisateurs, les alertes et l'analytique administrative. Les tests fonctionnels montrent que les principaux modules repondent aux objectifs. Le systeme soutient la sensibilisation sanitaire et l'orientation precoce, tout en restant un outil d'aide a la decision qui ne remplace pas le diagnostic clinique.")
    p(doc, "Mots-cles: MediGuard, intelligence artificielle, depistage, apprentissage automatique, Bamenda", bold=True)
    page_break(doc)

    heading(doc, "DEDICATION")
    p(doc, "This work is dedicated to God Almighty, to my family, and to all people who continue to seek safer and more accessible healthcare information in underserved communities.")
    page_break(doc)

    heading(doc, "ACKNOWLEDGEMENTS")
    p(doc, f"I sincerely acknowledge my supervisor, {SUPERVISOR}, for academic guidance, corrections, and encouragement throughout this project. I also acknowledge the Head of Department, lecturers, and staff of the National Higher Polytechnic Institute of The University of Bamenda for the training and support received during this programme.")
    p(doc, "I am equally grateful to healthcare workers, community members, classmates, friends, and family whose experiences and encouragement motivated the development of MediGuard.")
    page_break(doc)

    heading(doc, "TABLE OF CONTENTS")
    add_static_toc(doc)
    page_break(doc)

    heading(doc, "LIST OF TABLES")
    for num, title in [
        ("1.1", "Definition of Key Terms"),
        ("3.1", "MediGuard Four-Layer Architecture Overview"),
        ("3.2", "UML Diagram Types Used in MediGuard"),
        ("3.3", "MediGuard Use Case Inventory"),
        ("3.4", "Use Case Description — UC-05: Check Symptoms"),
        ("3.5", "Use Case Description — UC-08: Chat with AI"),
        ("3.6", "Hardware Resources"),
        ("3.7", "Software Tools and Versions"),
        ("3.8", "Python Libraries and Their Roles"),
        ("3.9", "Key Frontend Libraries"),
        ("4.1", "Functional Test Summary"),
        ("A.1", "Selected MediGuard API Endpoints"),
    ]:
        p(doc, f"Table {num}: {title}")
    page_break(doc)

    heading(doc, "LIST OF FIGURES")
    for num, title in [
        ("3.1", "MediGuard Four-Layer System Architecture"),
        ("3.2", "MediGuard System Package Decomposition Diagram"),
        ("3.3", "Sequence Diagram — Symptom Prediction Flow"),
        ("3.4", "Sequence Diagram — AI Chat (RAG) Flow"),
        ("3.5", "MediGuard Class Diagram (Data Model)"),
        ("4.1", "Main User Workflow of the Implemented Application"),
    ]:
        p(doc, f"Figure {num}: {title}")
    page_break(doc)

    heading(doc, "LIST OF ABBREVIATIONS")
    for abbr in [
        "AI: Artificial Intelligence",
        "API: Application Programming Interface",
        "CSS: Cascading Style Sheets",
        "DBMS: Database Management System",
        "HTTP: Hypertext Transfer Protocol",
        "JWT: JSON Web Token",
        "LLM: Large Language Model",
        "ML: Machine Learning",
        "NLP: Natural Language Processing",
        "ORM: Object-Relational Mapping",
        "RAG: Retrieval-Augmented Generation",
        "REST: Representational State Transfer",
        "SPA: Single-Page Application",
        "SQL: Structured Query Language",
        "UML: Unified Modeling Language",
    ]:
        p(doc, abbr)
    page_break(doc)


def bullet(doc, text, indent=1.0):
    para = p(doc, "•  " + text)
    para.paragraph_format.left_indent = Cm(indent)
    para.paragraph_format.first_line_indent = Cm(-0.5)
    return para


def bold_bullet(doc, bold_text, rest_text, indent=1.0):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(indent)
    para.paragraph_format.first_line_indent = Cm(-0.5)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.5
    r1 = para.add_run("•  " + bold_text)
    r1.bold = True
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r2 = para.add_run(rest_text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    return para


def chapter_one(doc: Document):
    heading(doc, "CHAPTER ONE: GENERAL INTRODUCTION")
    heading(doc, "1.1 Background of the Study", 2)
    p(doc, "The integration of machine learning and artificial intelligence in healthcare has shown significant promise in enhancing diagnostic accuracy and efficiency, particularly in resource-limited settings. Traditional healthcare delivery often relies on the physical availability of trained professionals and advanced diagnostic equipment — resources that are chronically scarce in many communities across Sub-Saharan Africa. This gap leads to delayed diagnoses, uninformed self-medication, and suboptimal patient outcomes. As many communities struggle with shortages of medical staff and resources (Britnell, 2019), AI-powered health tools can leverage technology to provide timely and accessible health information, improving healthcare delivery in these underserved regions.")
    p(doc, "Healthcare is universally recognized as a fundamental human right and a critical pillar of socio-economic development. The attainment of universal health coverage (UHC) — ensuring that all individuals receive quality health services without suffering financial hardship — remains one of the central goals of the United Nations Sustainable Development Goal 3 (SDG 3). Yet, in many low- and middle-income countries (LMICs), particularly in Sub-Saharan Africa, this goal remains unrealized. In Cameroon, these challenges are compounded by a complex interplay of historical, geographical, cultural, and socio-political factors that have collectively hampered the country's progress toward universal health coverage.")
    p(doc, "The World Health Organization (2023) has noted that while notable improvements have been recorded in several African health indicators over the past two decades — including reductions in child mortality and increased immunization coverage — significant disparities persist between urban and rural populations. The health system in Cameroon is characterized by widespread inequity in access: urban centers like Yaoundé and Douala boast relatively better-equipped hospitals and a higher density of healthcare professionals, while rural and semi-urban areas like many communities in the North-West Region continue to struggle with an acute shortage of medical personnel, facilities, and supplies.")
    p(doc, "The North-West Region of Cameroon, with Bamenda as its political and commercial capital, occupies a particularly precarious position in the country's health landscape. The region has, since 2016, been severely impacted by an ongoing socio-political crisis that arose from grievances over the marginalization of English-speaking Cameroonians. This crisis rapidly escalated into an armed conflict that has devastated communities and institutional infrastructure alike. According to the United Nations Office for the Coordination of Humanitarian Affairs (OCHA, 2023), approximately 18% of health facilities in the North-West and South-West Regions have been forced to permanently or temporarily close since April 2023. The consequences have been catastrophic: millions of people have been left without access to essential health services, and healthcare professionals who once staffed these facilities have been displaced or have fled the region entirely.")
    p(doc, "Against this backdrop of institutional fragility, the burden of communicable diseases continues to escalate. The epidemiological profile of Cameroon is dominated by infectious diseases, most notably malaria, typhoid fever, cholera, and respiratory tract infections. Malaria remains the single leading cause of morbidity and mortality in the country, accounting for over two million reported cases annually — a figure widely considered to be a significant underestimate (Iyaniwura, 2025). Research conducted in the North-West Region suggests that up to 70% of actual malaria cases may go unreported, largely because individuals resort to self-medication or seek care from traditional healers and informal drug vendors rather than formal health facilities.")
    p(doc, "Moreover, the application of machine learning in disease prediction can help mitigate the consequences of delayed and uninformed healthcare decisions that occur due to the ambiguous nature of overlapping symptoms and the complexity of tropical medical conditions. Studies have shown that machine learning algorithms can enhance diagnostic support accuracy by identifying patterns in symptom data that may be overlooked by lay individuals attempting to self-diagnose (El Oazzani, Fattah & Benamar, 2022). By utilizing algorithms that can analyze large amounts of symptom data, AI-powered health tools can provide evidence-based preliminary assessments that guide individuals toward timely and appropriate care.")
    p(doc, "It is within this context of healthcare fragility, high disease burden, and inadequate diagnostic infrastructure that the potential of digital health technologies emerges as a powerful and timely intervention. The rapid proliferation of mobile phones and internet connectivity across Cameroon — even in areas with limited fixed infrastructure — has created a new medium through which health information, education, and basic diagnostic support can be delivered directly to individuals. According to the International Telecommunication Union (ITU, 2023), Cameroon's mobile phone penetration rate exceeded 85% by the end of 2022, and smartphone usage is growing rapidly, particularly among younger and semi-urban populations. This digital infrastructure presents a unique opportunity to leverage AI and ML technologies to fill critical gaps in the healthcare delivery chain.")
    p(doc, "Recent advancements in machine learning, natural language processing, and the accessibility of cloud computing have made it feasible to develop sophisticated, lightweight, and user-friendly applications that can be deployed via standard web browsers on ordinary smartphones. These technologies can empower ordinary citizens — with no formal medical training — to perform a preliminary assessment of their symptoms, receive structured and evidence-based health information, and make more informed decisions about whether and when to seek professional care. This study, therefore, proposes to harness these capabilities to address the specific and urgent healthcare challenges of the Bamenda community through the development of MediGuard — an AI-powered community disease prediction and research system.")

    heading(doc, "1.2 Problem Statement", 2)
    p(doc, "Despite the potential benefits of machine learning in healthcare, the implementation of AI-powered health information tools for community use in Bamenda remains virtually non-existent. We remarked after investigation that there is currently no locally contextualized, AI-based community disease prediction system serving the North-West Region of Cameroon. Key challenges driving this gap include the lack of relevant digital health infrastructure, the absence of locally trained ML models, and the need for solutions that consider the unique epidemiological and socioeconomic characteristics of the Bamenda population.")
    p(doc, "The healthcare crisis in Bamenda is a complex, multilayered problem operating simultaneously at financial, geographical, social, and informational levels. At the financial level, the cost of healthcare represents an enormous barrier for the majority of households. According to Cheuyem (2025), Cameroonian citizens collectively spend approximately 475 billion XAF annually on healthcare, largely as out-of-pocket expenditure. This discourages timely health-seeking: individuals delay seeking care until symptoms are severe, by which point treatment is more complex, costly, and risky.")
    p(doc, "Geographically, Bamenda and its environs are characterized by difficult terrain, sparse road networks, and a security situation that has made travel between communities extremely dangerous. The International Committee of the Red Cross (ICRC, 2022) documented numerous incidents in which patients were unable to reach hospitals due to security restrictions, creating zones of near-total healthcare exclusion. In the face of these barriers, self-medication has become the de facto primary healthcare strategy for a large proportion of the population, with all the attendant risks of antimicrobial resistance and missed serious diagnoses (Al-Worafi, 2021).")
    p(doc, "Additionally, there is a significant gap in understanding how to effectively deliver health information through digital channels in this context. Much of the health information currently available online is poorly organized, medically inaccurate, overly technical for a lay audience, or entirely inappropriate for the local disease context. Existing digital health platforms, such as telemedicine services, primarily focus on connecting users with medical professionals — they require stable internet connectivity, carry consultation fees, and depend on doctor availability. They do not provide autonomous, immediate, and free access to preliminary disease prediction or structured health education. There are also ethical challenges surrounding patient data privacy and the risk of algorithmic bias if models are trained on non-representative datasets.")
    p(doc, "There is therefore an urgent and demonstrable need for a community-centered, AI-powered disease prediction and research system specifically designed for the healthcare context of Bamenda. Such a system must accept user-reported symptoms as input, apply machine learning algorithms trained on locally relevant disease data to generate probabilistic disease predictions, and provide evidence-based health information through an intelligent research assistant interface. By filling this pre-consultation gap, the system has the potential to transform health-seeking behavior and ultimately contribute to improved health outcomes for the community.")

    heading(doc, "1.3 Research Questions", 2)
    p(doc, "To realize this project, we examined several questions to better understand the topic and delimit it in space and in time. These questions are first general then specific.")
    heading(doc, "1.3.1 Main Research Question", 3)
    bullet(doc, "How can an AI-powered disease prediction and research system be designed and implemented to improve healthcare awareness and health-seeking behavior in the Bamenda community?")
    heading(doc, "1.3.2 Specific Research Questions", 3)
    for q in [
        "What are the specific healthcare needs and disease prediction challenges faced by the Bamenda community that machine learning and AI can address?",
        "How can machine learning algorithms be effectively trained and validated using locally contextualized symptom-disease data from the North-West Region of Cameroon?",
        "How can a Retrieval-Augmented Generation (RAG) framework be effectively implemented to provide reliable, structured, and context-sensitive health research information to non-medical users in a low-resource environment?",
        "What are the key barriers to implementing AI-based health information tools in a resource-constrained, conflict-affected setting like Bamenda, and what strategies can help overcome them?",
        "To what extent can an AI-driven pre-consultation tool meaningfully influence the health-seeking behavior of community members, and what factors determine user acceptance?",
    ]:
        bullet(doc, q)

    heading(doc, "1.4 Research Objectives", 2)
    p(doc, "The following objectives guide this study in exploring the design, implementation, and evaluation of the MediGuard system:")
    heading(doc, "1.4.1 General Objective", 3)
    bullet(doc, "To design, develop, and implement an AI-powered community disease prediction and research system that improves healthcare awareness, promotes early health-seeking behavior, and enhances accessibility to structured health information for residents of Bamenda, Cameroon.")
    heading(doc, "1.4.2 Specific Objectives", 3)
    for obj in [
        "To conduct a comprehensive epidemiological analysis of the most prevalent diseases in the North-West Region of Cameroon, cataloguing their associated symptoms, risk factors, and typical clinical presentations to inform dataset construction and model training.",
        "To develop, train, and rigorously evaluate machine learning classification models — including Random Forest, Decision Tree, and Naive Bayes — capable of predicting probable diseases from user-input symptom data, achieving a target accuracy of not less than 85% on the validation dataset.",
        "To design and implement a responsive, accessible, and intuitive web-based user interface using React.js and Tailwind CSS, optimized for use on low-bandwidth mobile connections and a wide range of device types.",
        "To integrate an AI-powered conversational health research assistant using a Retrieval-Augmented Generation (RAG) architecture — backed by a Pinecone vector database and a Large Language Model API — to provide evidence-based, structured health information in response to user queries.",
        "To conduct systematic usability testing and performance evaluation of the completed system with representative users from the Bamenda community, employing the System Usability Scale (SUS) and accuracy benchmarking metrics, and incorporating user feedback into iterative system refinement.",
    ]:
        bullet(doc, obj)

    heading(doc, "1.5 Significance of the Study", 2)
    p(doc, "An AI-powered disease prediction and research system of the type proposed in this study will benefit the community from a wide range of advantages that cannot be obtained when health information is sought through unguided internet searches or informal channels. In any healthcare context, timeliness is of great essence. The execution of symptom assessment and disease information retrieval activities can be complex and confusing for community members without medical training; therefore, the introduction of a system that provides structured, evidence-based guidance and requires as little prior knowledge as possible is most desirable.")
    p(doc, "This study aims to bridge the healthcare information gap in the Bamenda community by leveraging machine learning and AI technologies to enhance the accuracy and accessibility of disease awareness. As healthcare systems increasingly rely on digital tools, this research addresses key challenges and offers innovative solutions to improve health-seeking behavior. The findings will provide insights into how AI tools can be effectively tailored for a resource-constrained, conflict-affected community, ultimately reducing reliance on uninformed self-medication, improving early disease awareness, and optimizing the use of limited community resources.")
    p(doc, "Moreover, the study contributes to the body of knowledge on the practical application of artificial intelligence in healthcare in the African context, guiding policymakers, health administrators, and technology developers on how to implement AI-based solutions that are both impactful and sustainable. It also emphasizes the importance of inclusivity in technological innovation, ensuring that communities in the North-West Region are not left behind in the digital health revolution. The anonymized prediction data generated by the system can further serve as a community-level epidemiological surveillance resource for health authorities.")

    heading(doc, "1.6 Scope of the Study", 2)
    p(doc, "The scope of this study is designed to delineate the boundaries and focus areas related to the design and implementation of the MediGuard system. It encompasses various dimensions critical to understanding the complexities and challenges associated with AI-powered disease prediction in a community context.")
    p(doc, "This research focuses on a defined population — specifically the residents of the Bamenda urban and peri-urban community in the North-West Region of Cameroon — and covers the design, development, and implementation of an AI-powered community disease prediction and research system. The study covers the identification of locally prevalent diseases and their symptom profiles, the training and validation of ML models using locally contextualized disease data, and the evaluation of the system's impact on health awareness and usability. It will also investigate the specific diseases included in the system, covering but not limited to:")
    for item in [
        "Symptom-based assessment: Evaluation of user-reported symptoms through an intelligent symptom checker interface.",
        "Machine learning disease prediction: Probabilistic disease classification using trained Scikit-learn models.",
        "AI research assistant: Retrieval-Augmented Generation system grounded in the Gale Encyclopedia of Medicine.",
        "Community health trends: Anonymized epidemiological data visualization through a trends dashboard.",
    ]:
        bullet(doc, item)
    p(doc, "Geographically, the research is focused on the Bamenda community, and the disease categories examined are limited to those with high prevalence in the North-West Region, including malaria, typhoid fever, cholera, pneumonia, tuberculosis, meningitis, and common respiratory infections, among others. The system is web-based to ensure the broadest possible accessibility across device types and network conditions without requiring dedicated software installation.")

    heading(doc, "1.7 Limitations of the Study", 2)
    p(doc, "While this study on the MediGuard AI-powered disease prediction system aims to provide valuable insights and advancements in community health practices, it is essential to acknowledge several limitations that impact the findings and their applicability.")
    p(doc, "This study may encounter several limitations. One key constraint is the limited availability and quality of locally annotated medical symptom data from the Bamenda community, which may affect the training and accuracy of ML models. The disease prediction dataset used — while carefully curated with locally relevant disease prevalence — is synthetically generated to reflect epidemiological patterns rather than drawn from clinical records, which limits direct clinical validation. Additionally, the technical infrastructure in some areas of the North-West Region may not reliably support the full deployment of web-based AI tools due to intermittent internet connectivity and electricity supply.")
    p(doc, "There may also be resistance to technology adoption among community members due to limited digital literacy, unfamiliarity with AI health tools, or scepticism toward automated health information — factors identified by the Technology Acceptance Model (Davis, 1989) as barriers to adoption. The system also does not extend to clinical validation — that is, the formal assessment of its outputs against professional medical diagnosis through a regulated clinical trial — which would require institutional approval beyond the scope of this project. Finally, ethical and legal considerations around patient data privacy, algorithmic bias, and the communication of medical uncertainty must be carefully managed to ensure responsible deployment.")

    heading(doc, "1.8 Definition of Key Terms", 2)
    table(doc, "Table 1.1: Definition of Key Terms", ["Term", "Definition"], [
        ["Machine Learning (ML)", "A subfield of artificial intelligence focused on the development of algorithms and statistical models that enable computer systems to learn and improve from experience — specifically from data — without being explicitly programmed for each specific task. ML is the primary technology underlying the disease prediction component of MediGuard."],
        ["Artificial Intelligence (AI)", "The simulation of human cognitive processes — including learning, reasoning, problem-solving, and language understanding — by computer systems, enabling machines to perform tasks that typically require human intelligence."],
        ["Disease Prediction System", "A computational tool that accepts clinical data — in this case, user-reported symptoms — as input and applies mathematical models to generate a probabilistic assessment of the diseases most likely to explain the observed symptoms."],
        ["Community Health System", "A digital platform designed to serve the health information and awareness needs of a defined community, providing accessible health education, disease prediction, and guidance on health-seeking behavior."],
        ["Retrieval-Augmented Generation (RAG)", "An advanced AI technique that enhances the output of a large language model by first retrieving relevant information from an external knowledge base and incorporating that retrieved information into the model's response generation process, improving factual accuracy and reducing hallucination."],
        ["Pre-Consultation Phase", "The period of time between the onset of health symptoms and a patient's first contact with a formal healthcare provider, during which individuals typically attempt to understand their condition and decide on a course of action."],
        ["Health Literacy", "The degree to which individuals have the capacity to obtain, process, understand, and communicate basic health information and services needed to make appropriate health decisions."],
        ["Algorithm", "A set of rules or procedures followed by a computer in problem-solving operations, particularly in training machine learning models and generating disease predictions."],
        ["Accuracy", "A metric that measures the proportion of correct predictions made by the machine learning model out of all predictions made on the test dataset."],
        ["Vector Database", "A specialized type of database optimized for storing and retrieving high-dimensional vector embeddings, enabling efficient semantic similarity search. In MediGuard, Pinecone is used as a vector database to store and retrieve health information for the RAG-based research assistant."],
    ], [2.0, 4.3])

    heading(doc, "1.9 Organization of Chapters", 2)
    for ch in [
        "Chapter One — entitled \"General Introduction\" — introduces the report and presents the background of the study, problem statement, research questions, objectives (general and specific), significance and scope of the study, limitations, definition of key terms, and organization of chapters.",
        "Chapter Two — entitled \"Literature Review\" — serves as a foundational component of this report, providing a comprehensive overview of existing and related studies and developments in the field of machine learning and AI for healthcare applications, specifically disease prediction and health information systems. It aims to identify gaps in current knowledge, highlight trends, and establish the importance of the study within the broader context of healthcare and technology.",
        "Chapter Three — entitled \"Research Methodology and Materials Used\" — explains the methodology applied in this report. It presents the system architecture, data collection methods, modeling methods, the use of UML diagrams, materials used, and programming languages and tools employed in development. It also presents a detailed description of the system design, including use case, sequence, and class diagrams.",
        "Chapter Four — entitled \"Results and Discussion\" — is mainly concerned with the presentation and discussion of the results obtained during implementation. It describes the functioning of the final application, including all system interfaces and features for each user role.",
        "Chapter Five — entitled \"General Conclusion and Recommendations\" — summarizes the work from beginning to end, discusses key findings, presents difficulties encountered, and offers recommendations and suggestions for future research and improvement.",
    ]:
        bullet(doc, ch)
    page_break(doc)


def chapter_two(doc: Document):
    heading(doc, "CHAPTER TWO: LITERATURE REVIEW")
    heading(doc, "2.1 Introduction", 2)
    p(doc, "The integration of machine learning (ML) into healthcare has transformed disease diagnosis and health information delivery, enabling improved patient outcomes through enhanced accuracy and efficiency. As medical data volumes surge and communities increasingly seek health information through digital channels, traditional manual methods often fall short, making ML a valuable tool for identifying patterns and making predictions that can guide health-seeking behavior.")
    p(doc, "This literature review examines the current state of research on machine learning applications in disease prediction and community health information systems. It covers foundational concepts of machine learning techniques, highlights successful applications in predicting diseases such as malaria, typhoid, and respiratory infections, and emphasizes the critical role of locally relevant data. A systematic review by Choudhury (2025) illustrates how AI significantly enhances diagnostic support accuracy in various medical fields.")
    p(doc, "Additionally, the review addresses challenges including limitations and ethical considerations associated with ML deployment in community health settings. By identifying research gaps and future directions, this review provides a solid foundation for understanding the potential of machine learning in community disease prediction and health information delivery, particularly in the context of Bamenda, Cameroon.")

    heading(doc, "2.2 Generalities", 2)
    heading(doc, "2.2.1 Concept of Machine Learning in Disease Prediction", 3)
    p(doc, "Machine learning is revolutionizing health information and disease prediction by enabling faster and more accurate identification of probable medical conditions. By analyzing symptom datasets, ML algorithms can detect patterns that may be missed by individuals attempting to self-diagnose or by general-purpose internet search tools. For example, studies have demonstrated that ML models trained on symptom-disease datasets can classify common tropical diseases with accuracy comparable to clinical screening tools (Sayed & Smith, 2020). These algorithms process large amounts of data quickly, improving the speed and quality of health information delivery to community members.")
    p(doc, "The goal of machine learning in community health information systems is not to replace physicians but to empower individuals with better preliminary information — reducing uninformed self-medication and enabling earlier, more targeted engagement with the formal healthcare system. However, challenges remain, such as data privacy, algorithmic bias when models are trained on non-representative populations, and the need for interpretability of AI outputs in a community health context. Addressing these issues is essential for the successful integration of ML into community-facing health tools.")
    p(doc, "As research advances, the potential for machine learning to enhance health information accuracy and accessibility continues to grow, paving the way for innovative community health solutions like MediGuard that are specifically tailored to the epidemiological and socioeconomic realities of the communities they serve.")

    heading(doc, "2.2.2 Goals of Machine Learning in Community Disease Prediction", 3)
    p(doc, "According to a study by Maguluri (2024), the primary goals of machine learning in disease prediction include the following key objectives:")
    for item in [
        "Improved Prediction Accuracy: ML aims to reduce misinformation about probable conditions by analyzing complex symptom datasets and identifying patterns that may be overlooked by lay individuals or general web searches.",
        "Speeding Up Health Information Access: By automating the analysis of symptom data, ML can significantly shorten the time required for a community member to obtain structured and relevant health information, allowing for earlier treatment-seeking decisions.",
        "Personalized Health Guidance: ML facilitates the delivery of tailored health information by analyzing individual user-reported symptom data to generate condition-specific predictions and guidance.",
        "Scalability: ML systems can process large volumes of symptom data efficiently, making it possible to apply advanced prediction techniques across diverse community settings, including underserved and conflict-affected areas.",
        "Continuous Learning: ML models can be updated over time as they are exposed to more data, allowing for ongoing enhancements in prediction capabilities and adaptation to new or emerging disease patterns in the community.",
    ]:
        bullet(doc, item)

    heading(doc, "2.3 An Overview of Machine Learning in Disease Prediction", 2)
    heading(doc, "2.3.1 The Emergence of Machine Learning in Healthcare Information Systems", 3)
    p(doc, "The emergence of machine learning in healthcare is transforming how medical information is delivered and how disease patterns are identified. Recent advancements in computational power and data availability have enabled the integration of ML into various health applications ranging from clinical decision support systems in hospitals to community-facing symptom checkers and telemedicine platforms.")
    p(doc, "According to Obermeyer and Emanuel (2016), ML algorithms can analyze vast datasets from electronic health records and medical literature, uncovering patterns that enhance decision-making and personalized health information delivery. Notably, ML has shown remarkable success in supporting the identification of conditions like malaria, respiratory infections, and cardiovascular diseases, often matching or exceeding human accuracy in structured diagnostic tasks. ML also supports predictive analytics, allowing health systems to anticipate community disease trends based on aggregated data, improving resource allocation and public health response.")

    heading(doc, "2.3.2 Types of Machine Learning Health Systems", 3)
    for bold, rest in [
        ("Web-Based Systems: ", "Web-based systems utilize machine learning algorithms to analyze health data through online platforms. These systems provide accessible health information, symptom checking, and disease prediction tools through browsers, without requiring software installation. MediGuard is a web-based system that enables community members to input symptoms and receive AI-generated disease predictions through any web browser, making it accessible on mobile phones across a range of network conditions."),
        ("Mobile Applications: ", "Mobile applications leverage machine learning to provide health-related services directly on smartphones and tablets. These apps can track symptoms, offer health recommendations based on user data, and connect users with telemedicine services. Platforms like Babylon Health (Babyl) in Rwanda exemplify this approach, achieving significant community uptake by designing for mobile-first, feature-phone-compatible interfaces."),
        ("Hospital Clinical Decision Support Systems: ", "These systems are designed for use by trained healthcare professionals, integrating ML algorithms into clinical workflows to support diagnosis, treatment planning, and medication management. While powerful, these tools are designed for clinical staff rather than for community lay users and therefore do not address the pre-consultation information gap that MediGuard targets."),
        ("Manual and Hybrid Systems: ", "Traditional manual systems involve healthcare processes without advanced technological integration, relying on human expertise for diagnosis and information delivery. Hybrid systems combine manual professional judgment with basic automated support. These systems often lack the efficiency and scalability that machine learning-powered platforms offer, particularly in resource-constrained settings."),
    ]:
        bold_bullet(doc, bold, rest)

    heading(doc, "2.3.3 Recent Developments of Machine Learning in Health Information Systems", 3)
    p(doc, "Machine learning is transforming community health information delivery through several significant advancements. One development is predictive analytics — ML algorithms that anticipate disease occurrence based on symptom patterns and community-level data, enabling earlier interventions and improved health awareness. In the field of natural language processing, NLP is increasingly being used to power conversational health assistants that can respond to open-ended health questions in natural language, providing accessible health information beyond simple symptom checkers.")
    p(doc, "Moreover, the Retrieval-Augmented Generation (RAG) framework — combining vector database retrieval with generative language models — is emerging as a particularly promising approach for health information systems. RAG-powered assistants can provide responses grounded in authoritative medical sources, significantly reducing the risk of factually incorrect information that plagues purely generative chatbots (Lewis et al., 2020). Clinical decision support systems are also being extended into patient-facing tools, helping individuals make more informed decisions about when and how to seek care. MediGuard integrates both ML-based disease prediction and RAG-based health research assistance, representing the convergence of these recent developments into a single community-facing platform.")

    heading(doc, "2.3.4 Existing Health Information Platforms in Cameroon", 3)
    p(doc, "Cameroon is witnessing a gradual shift in health information delivery, with several platforms and institutions beginning to embrace digital health services to enhance accessibility and patient awareness. Notable examples include:")
    for item in [
        "WASPITO: Cameroon's pioneering telemedicine platform connects patients with licensed medical professionals through video and audio consultations via smartphone. It has achieved significant adoption in urban areas but is primarily a consultation facilitation tool, requiring stable connectivity, consultation fees, and doctor availability.",
        "Yaoundé Central Hospital: Provides online health information and telemedicine consultations for patients in urban Yaoundé.",
        "Douala General Hospital: Offers online appointment scheduling and limited telehealth services for urban populations.",
        "Buea Regional Hospital: Implements telemedicine for follow-up consultations, primarily serving populations in the South-West Region.",
        "CBC Health Services: Provides telemedicine consultations, allowing patients in mission hospital networks to access healthcare remotely.",
    ]:
        bullet(doc, item)
    p(doc, "Notably, none of these platforms provides a free, autonomous, AI-powered symptom checker and disease prediction tool designed for lay community use in the North-West Region. MediGuard is designed to fill precisely this gap.")

    heading(doc, "2.4 Limitations of Existing Health Information Systems", 2)
    p(doc, "While existing digital health platforms in Cameroon have the potential to improve access and convenience, several limitations hinder their effectiveness, particularly for the Bamenda community. Understanding these challenges is crucial for positioning MediGuard as a targeted solution.")
    p(doc, "One significant barrier is limited internet access and connectivity. Many areas in the North-West Region suffer from unreliable connectivity, making it difficult for community members to access online health platforms that require stable broadband connections for video consultations or heavy data usage. Additionally, a considerable portion of the population lacks digital literacy, which can prevent effective use of complex telemedicine platforms.")
    p(doc, "Cost represents another significant limitation. Most existing telemedicine platforms charge consultation fees, making them inaccessible to the majority of low-income households in the Bamenda community. Data privacy concerns also pose a challenge, as community members may be reluctant to share personal health information with digital platforms whose data governance practices are unclear. Furthermore, the absence of locally trained ML models means that existing global symptom checkers systematically underweight the tropical diseases dominant in Bamenda — such as malaria, typhoid, and cholera — in favor of conditions more prevalent in Western populations.")
    p(doc, "Cultural factors also play a role: some community members may prefer traditional face-to-face consultations, particularly older populations or those with lower levels of formal education. The conflict situation in the North-West Region further compounds all of these barriers, restricting both physical and digital access to health services. MediGuard is designed to address these limitations by providing a free, mobile-optimized, locally contextualized, and culturally appropriate alternative for health information access.")

    heading(doc, "2.5 Context and Critical Analysis", 2)
    heading(doc, "2.5.1 Context", 3)
    p(doc, "Looking at the health information and disease awareness practices in the Bamenda community, it is clear that the majority of community members currently navigate health decisions without reliable digital support. No computerized, AI-powered community disease prediction system exists to serve this community. When individuals experience symptoms, they typically resort to uninformed self-medication, consultation with neighbors or traditional healers, or unguided internet searches that return results calibrated for entirely different disease contexts. It is on this basis that we decided to design and implement MediGuard — a locally contextualized, AI-powered community disease prediction and research system — to provide structured, evidence-based health information to the Bamenda community in a free, accessible, and culturally appropriate format.")
    heading(doc, "2.5.2 Critical Analysis", 3)
    p(doc, "Disease awareness in communities like Bamenda often relies on a combination of traditional knowledge, informal advice networks, and unguided digital searches. While advancements in technology — such as AI and machine learning — enhance the accuracy and speed of health information delivery, challenges remain in ensuring that these tools are locally relevant, accessible, and trustworthy. In many resource-constrained settings, limited access to appropriate health information tools leads to delays in seeking care and a heavy reliance on self-medication, with all the attendant risks of antimicrobial resistance and missed serious diagnoses. Additionally, the reliance on globally developed AI tools introduces systematic biases that disadvantage populations in tropical regions where disease prevalence patterns differ markedly from those of Western populations. Overall, while the global digital health ecosystem has improved significantly, ongoing disparities and technological barriers continue to hinder optimal health outcomes for communities like Bamenda. A locally designed, community-centered solution is therefore both necessary and justified.")

    heading(doc, "2.6 Theoretical Framework", 2)
    p(doc, "The design and development of MediGuard is informed by several interconnected theoretical frameworks that provide both conceptual grounding and practical guidance for its implementation.")
    heading(doc, "2.6.1 Information Processing Theory", 3)
    p(doc, "The Information Processing Theory, originally developed in the cognitive sciences as a model of human problem-solving and decision-making, provides a foundational framework for understanding the diagnostic process (Neisser, 1967). The theory conceptualizes cognition as a sequential system involving the stages of input, processing, storage, and output — a structure that maps directly onto computational models of disease prediction. In the proposed AI system, user-reported symptoms constitute the input, the machine learning algorithm performs the processing by comparing symptom patterns against trained disease models, and the ranked list of probable diseases represents the output. This alignment between the theoretical model of human diagnostic reasoning and the computational architecture of the system reflects a genuine design philosophy that aims to replicate the core logic of clinical reasoning in a mathematically rigorous and interpretable way.")
    heading(doc, "2.6.2 Decision Support System Theory", 3)
    p(doc, "Decision Support Systems (DSS) are information systems designed to assist decision-makers in complex, semi-structured, or unstructured decision environments by providing relevant data, analytical tools, and structured recommendations (Power, 2002). MediGuard belongs to the patient-facing category of DSS: it is designed not to replace clinical judgment but to provide individuals with the structured information and analytical support they need to make better-informed decisions about when and where to seek professional care. This positions the system as a complement to — rather than a substitute for — the formal healthcare system, a distinction that is both ethically important and practically necessary in the Cameroonian regulatory context.")
    heading(doc, "2.6.3 Technology Acceptance Model (TAM)", 3)
    p(doc, "The Technology Acceptance Model, originally formulated by Davis (1989), provides the most widely validated theoretical account of the factors that determine whether individuals will adopt and use a new information technology. TAM identifies two primary determinants of technology acceptance: perceived usefulness — the degree to which a user believes the system will enhance their ability to perform a task — and perceived ease of use — the degree to which a user believes the system can be operated without significant effort. For MediGuard, perceived usefulness will be determined by the accuracy and relevance of disease predictions and health information provided, while perceived ease of use will be shaped by the quality of the user interface design and the clarity of the language used. TAM mandates equal attention to technical performance and user experience design.")
    heading(doc, "2.6.4 Health Belief Model (HBM)", 3)
    p(doc, "The Health Belief Model (Rosenstock, 1974) provides a framework for understanding the health behavior dimension of the proposed system's impact. The HBM posits that an individual's likelihood of adopting a health behavior is determined by their perceived susceptibility to a health threat, their perceived severity of that threat, their perceived benefits of taking action, and the perceived barriers to taking that action. MediGuard addresses several of these determinants directly: by providing users with a probabilistic assessment of their probable disease, the system makes abstract health risks concrete and personally relevant, potentially increasing perceived susceptibility and severity. By making health information freely and immediately accessible, it reduces one of the most significant perceived barriers to health-seeking behavior — the cost and inconvenience of obtaining reliable information.")

    heading(doc, "2.7 Review of Machine Learning Algorithms", 2)
    p(doc, "The selection of appropriate machine learning algorithms is critical in the development of a disease prediction system. This section provides a comparative analysis of the major algorithms implemented and evaluated in MediGuard.")
    heading(doc, "2.7.1 Naive Bayes Classifier", 3)
    p(doc, "The Naive Bayes classifier is a probabilistic model based on Bayes' theorem. Its probabilistic output provides users with a ranked list of diseases ordered by probability — a format well-suited to the clinical reality that a given set of symptoms may correspond to multiple possible conditions. It trains efficiently on relatively small datasets and handles high-dimensional feature spaces well. Studies by Kononenko (2001) and Witten and Frank (2011) have confirmed the competitive performance of Naive Bayes on medical diagnosis benchmarks, often outperforming computationally more complex alternatives when training data is limited.")
    heading(doc, "2.7.2 Decision Tree Classifier", 3)
    p(doc, "Decision tree algorithms construct a hierarchical tree structure in which each internal node represents a binary decision based on a single symptom variable. The primary advantage of decision trees is their interpretability: the tree structure can be visualized and understood by non-technical users, and the path from the root to a leaf node represents a clear, auditable chain of reasoning. However, individual decision trees are prone to overfitting — learning specific characteristics of the training data in excessive detail — a limitation substantially mitigated by ensemble methods.")
    heading(doc, "2.7.3 Random Forest Classifier", 3)
    p(doc, "The Random Forest algorithm, introduced by Breiman (2001), addresses the overfitting problem by constructing a large ensemble of decision trees, each trained on a random bootstrap sample and using a random subset of features at each split. A systematic review by Fernández-Delgado et al. (2014) found that Random Forests ranked among the top-performing algorithms across 179 classification datasets, including several medical benchmarks. In MediGuard, Random Forest achieved 99.8% accuracy on the held-out test set of 440 samples, confirming its suitability as the primary prediction engine.")
    heading(doc, "2.7.4 Algorithm Selection", 3)
    p(doc, "MediGuard implements and evaluates all three algorithms — Naive Bayes, Decision Tree, and Random Forest — and selects the best-performing model based on cross-validated accuracy, precision, recall, and F1-score metrics. The ensemble approach of Random Forest is hypothesized to achieve the highest overall accuracy, while Naive Bayes is expected to be the most robust when the training dataset is small. The final deployed model achieves the optimal balance of accuracy, calibration quality, and interpretability for the specific characteristics of the available locally-contextualized training data.")

    heading(doc, "2.8 Retrieval-Augmented Generation in Healthcare", 2)
    p(doc, "The AI research assistant component of MediGuard employs a Retrieval-Augmented Generation (RAG) framework — a hybrid approach combining information retrieval and generative language models to produce responses that are both fluent and factually grounded. The RAG framework was formally described by Lewis et al. (2020), who demonstrated that combining a retrieval module with a generative module significantly improved factual accuracy on knowledge-intensive tasks.")
    p(doc, "In the context of community health information delivery, RAG offers critical advantages over pure generative approaches. By grounding the model's responses in specific, curated health documents — extracted from the Gale Encyclopedia of Medicine, 3rd Edition — rather than relying solely on knowledge embedded in the model's parameters, RAG substantially reduces the risk of AI \"hallucination\" and ensures that information provided reflects authoritative health guidance. Xiong et al. (2024) found that RAG-enhanced medical chatbots significantly outperformed standard LLM-based chatbots on factual accuracy benchmarks. In MediGuard, the knowledge base comprises 453 chunked passages extracted from 19 disease articles in the Gale Encyclopedia, stored in a Pinecone vector database and retrieved via semantic similarity search to ground every assistant response.")

    heading(doc, "2.9 Digital Health in the African Context", 2)
    p(doc, "The application of digital health technologies in Africa presents a distinctive landscape characterized by extraordinary challenges and equally extraordinary opportunities. The ITU (2023) reports that mobile broadband subscriptions in Sub-Saharan Africa grew from approximately 200 million in 2015 to over 500 million by 2022, representing a fundamental shift in digital accessibility. This mobile-first reality shapes the design requirements for health systems intended for African populations: they must be optimized for mobile interfaces, function effectively on low-bandwidth connections, and minimize data consumption.")
    p(doc, "Several digital health platforms provide important precedents. WASPITO in Cameroon, Babyl in Rwanda, Ada Health globally, and mPharma in Ghana each address different dimensions of the healthcare access problem. A significant limitation of globally deployed symptom checkers like Ada is their development using predominantly Western population data, which may not accurately reflect disease prevalence patterns of African populations. In Bamenda, where malaria, typhoid, and cholera are dominant, a symptom checker trained primarily on temperate-climate data will systematically underweight these conditions. MediGuard directly addresses this gap by training its prediction model on a locally contextualized dataset of 2,200 records covering 20 diseases with regional prevalence weighting.")

    heading(doc, "2.10 Ethical and Social Dimensions", 2)
    p(doc, "The deployment of AI-based community health tools raises important ethical and social questions. Health data is among the most sensitive categories of personal information, and any system collecting health-related data must implement robust safeguards. MediGuard adopts a data minimization principle, collecting only the specific symptom data necessary to generate predictions and not requiring identifying information for basic functionality. Where user accounts are created, data is encrypted using industry-standard protocols.")
    p(doc, "Algorithmic bias is also a critical concern: machine learning models trained on non-representative data may produce systematically different prediction accuracy for different demographic groups (Obermeyer et al., 2019). MediGuard addresses this through the use of a locally curated training dataset weighted for the disease prevalence patterns of the North-West Region. All system outputs are clearly labelled as probabilistic estimates rather than definitive diagnoses, with prominent medical disclaimers communicating the system's limitations and consistently recommending consultation with a qualified healthcare professional. This approach aligns with Topol's (2019) recommendation that AI in healthcare function as augmentation of — rather than replacement for — human clinical judgment.")

    heading(doc, "2.11 Proposition of Solution", 2)
    p(doc, "To address the health information and disease awareness gaps identified in the Bamenda community, MediGuard proposes a targeted, locally-designed AI-powered solution. The system integrates two complementary components: a machine learning disease prediction engine that maps user-reported symptoms to probable diseases with probability scores, and a RAG-based health research assistant that provides evidence-grounded answers to natural language health questions.")
    for bold, rest in [
        ("Locally Contextualized Prediction: ", "Train machine learning models on a dataset of 2,200 records reflecting the disease prevalence patterns of the North-West Region, covering 20 diseases most relevant to Bamenda."),
        ("Encyclopaedia-Grounded RAG Assistant: ", "Extract and embed 453 passages from the Gale Encyclopedia of Medicine covering 19 locally relevant diseases, ingesting them into a Pinecone vector database for semantic retrieval and LLM-grounded response generation."),
        ("Mobile-First Web Interface: ", "Design a responsive React.js web interface optimized for low-bandwidth mobile connections, with a multi-step symptom checker, ranked results page, chat interface, disease library, and community trends dashboard."),
        ("Trust and Transparency: ", "Embed medical disclaimers, source citations, and explicit AI labelling throughout the system to ensure users understand the limitations of the tool and are consistently directed toward professional care for serious conditions."),
        ("Free and Accessible: ", "Deploy as a free, web-based tool requiring no software installation, accessible via any modern smartphone browser, with anonymous use supported for the core prediction and research functions."),
    ]:
        bold_bullet(doc, bold, rest)
    p(doc, "By combining these elements, MediGuard aims to transform the health information landscape of the Bamenda community — reducing uninformed self-medication, improving early health-seeking behavior, and providing a scalable, replicable model for community-centered AI health tools across the North-West Region and beyond.")

    heading(doc, "2.12 Partial Conclusion", 2)
    p(doc, "For a better understanding and realization of this project, it was necessary to gather significant insights from previous work on machine learning, AI in healthcare, digital health in Africa, and the specific challenges faced by the Bamenda community. The literature clearly demonstrates that machine learning holds substantial promise for improving health information access and disease prediction accuracy in resource-constrained settings — but that realizing this promise requires careful attention to local epidemiological context, digital infrastructure constraints, algorithmic fairness, and community trust.")
    p(doc, "Existing platforms — including global symptom checkers, telemedicine services, and general-purpose chatbots — each address aspects of the problem but fail to provide the comprehensive, locally calibrated, free, and autonomous solution that the Bamenda community requires. Access to locally relevant disease prediction tools and structured health information remains a critical issue, impacting the quality of health decisions made by community members every day. While telemedicine and technological innovations hold promise for improving access, their effectiveness is often limited by infrastructure, cost, and contextual relevance constraints. MediGuard is designed precisely to address these gaps, and future research should focus on evaluating the real-world impact of this and similar community-centered AI health tools.")
    page_break(doc)


def chapter_three(doc: Document):
    heading(doc, "CHAPTER THREE: RESEARCH METHODOLOGY AND MATERIALS USED")
    heading(doc, "3.1 Introduction", 2)
    p(doc, "This chapter describes the research methodology adopted in the design and implementation of MediGuard — a machine learning-based intelligent health assistant tailored for the Bamenda Health District, Cameroon. It outlines the architectural blueprint of the system, the methods employed to collect and process data, the modeling approach used to represent system behaviour, and the tools, languages, and frameworks that underpin the implementation.")
    p(doc, "MediGuard is a web-based platform that integrates three complementary intelligence layers: a supervised machine learning classifier for symptom-based disease prediction, a Retrieval-Augmented Generation (RAG) conversational AI engine for health queries, and a curated relational disease knowledge base. The system is designed to overcome the barriers of healthcare accessibility in resource-limited settings — providing citizens with preliminary clinical guidance, disease information, and nearest facility discovery — before, and not in replacement of, a professional clinical visit.")
    p(doc, "The development followed an iterative, user-centred methodology, with the system continuously refined based on domain requirements gathered from healthcare professionals and community users in the Bamenda area. Unified Modelling Language (UML) was selected as the formal notation to represent system structure and behaviour, following its widespread acceptance in academic and industrial software design.")

    heading(doc, "3.2 Description of the System Architecture", 2)
    p(doc, "MediGuard adopts a Client-Server Layered Architecture, organised into four distinct horizontal tiers that communicate through well-defined interfaces. This architectural style was chosen because it separates concerns cleanly, enables independent scaling of each tier, and simplifies maintenance and testing of individual components.")
    p(doc, "The four layers are summarised in Table 3.1 below:")
    table(doc, "Table 3.1: MediGuard Four-Layer Architecture Overview", ["Layer", "Role", "Technologies"], [
        ["Presentation Layer", "User Interface — renders pages and handles all user interaction", "React.js (Vite), JSX, Tailwind CSS"],
        ["API Layer", "REST API Gateway — receives HTTP requests, enforces authentication, routes to services", "FastAPI (Python), Uvicorn, JWT"],
        ["AI / ML Layer", "Intelligence Core — symptom normalisation, disease prediction, RAG chat", "scikit-learn, sentence-transformers, OpenAI, Pinecone"],
        ["Data Layer", "Persistent storage — relational data and vector embeddings", "PostgreSQL, SQLAlchemy ORM, Pinecone Vector DB"],
    ], [1.5, 2.5, 2.2])
    p(doc, "The architecture diagram (Figure 3.1) below shows the interaction between all four layers:")
    figure_box(doc, "Figure 3.1: MediGuard Four-Layer System Architecture", [
        "1. PRESENTATION LAYER  -- React.js SPA (Vite) running in user's web browser",
        "   Pages: Home | SymptomChecker | ChatAI | DiseaseLibrary | NearbyFacilities | Auth",
        "                         HTTPS / REST (JSON)",
        "2. API LAYER           -- FastAPI (Python 3.11) - Uvicorn ASGI server",
        "   Routers: /auth | /predict | /chat | /diseases | /history | /analytics | /newsletter",
        "   JWT Authentication  |  Input validation (Pydantic)",
        "3A. ML SUB-LAYER       -- fuzzy_match.py | predictor.py",
        "   RandomForest.pkl | DecisionTree.pkl | BernoulliNB.pkl",
        "3B. RAG SUB-LAYER      -- retriever.py + embeddings.py",
        "   Pinecone Vector DB  |  OpenAI GPT-4o-mini  |  sentence-transformers",
        "4. DATA LAYER          -- PostgreSQL 15 + SQLAlchemy 2.0 ORM + Alembic migrations",
        "   Tables: users | diseases | prediction_logs | chat_logs | chat_feedback | prediction_feedback",
    ])

    heading(doc, "3.2.1 Presentation Layer", 3)
    p(doc, "The presentation layer is a Single-Page Application (SPA) built with React.js (bundled with Vite). It communicates with the backend exclusively through RESTful HTTP calls, sending and receiving JSON payloads. React's component-based paradigm enables reusable UI elements (symptom tag chips, chat bubbles, disease cards) and efficient DOM updates via the virtual DOM diffing algorithm.")
    heading(doc, "3.2.2 API Layer", 3)
    p(doc, "The API layer is implemented using FastAPI, a modern Python web framework that generates OpenAPI documentation automatically, enforces type-safe request/response schemas through Pydantic, and supports asynchronous request handling via Python's asyncio. Authentication is implemented using JSON Web Tokens (JWT) — each protected endpoint validates the bearer token before processing the request.")
    heading(doc, "3.2.3 AI / ML Layer", 3)
    p(doc, "This layer comprises two sub-components:")
    bold_bullet(doc, "ML Sub-Layer: ", "A multi-model classifier pipeline. User-entered symptoms are first normalised by a fuzzy-matching module (fuzzy_match.py) that handles English, Cameroonian Pidgin English, and French symptom expressions, then converted to a binary feature vector aligned to a fixed symptom vocabulary. Three trained classifiers vote on the most probable diseases: Random Forest (primary), Decision Tree, and Bernoulli Naïve Bayes.")
    bold_bullet(doc, "RAG Sub-Layer: ", "The Retrieval-Augmented Generation engine augments the language model's response with disease-specific context retrieved from a Pinecone vector store. If Pinecone is unavailable, a local curated chunk library provides offline fallback. OpenAI GPT-4o-mini generates the final conversational response.")
    heading(doc, "3.2.4 Data Layer", 3)
    p(doc, "All relational data is persisted in a PostgreSQL database managed through SQLAlchemy ORM. Disease knowledge (symptoms, descriptions, treatments, prevention guidelines) is stored relationally. Prediction logs and chat logs are retained for analytics and personalised history. Vector embeddings for RAG are stored separately in Pinecone's cloud vector database.")

    heading(doc, "3.3 Data Collection", 2)
    p(doc, "Data collection for MediGuard followed both primary and secondary approaches, combining qualitative and quantitative strategies.")
    heading(doc, "3.3.1 Primary Data Collection", 3)
    p(doc, "Primary data was gathered through the following methods:")
    bold_bullet(doc, "Structured Interviews with Healthcare Professionals: ", "Interviews were conducted with nurses and community health workers at the Bamenda Regional Hospital and surrounding health centres. These interviews informed the symptom-disease mappings for diseases prevalent in the North West Region — including malaria, typhoid fever, respiratory infections, and waterborne diseases.")
    bold_bullet(doc, "Questionnaires and User Needs Assessment: ", "A structured questionnaire was administered to community members in Bamenda to assess health-seeking behaviour, digital literacy, and preferred languages of communication. Findings confirmed the need to support Cameroonian Pidgin English alongside English and French.")
    bold_bullet(doc, "Direct Observation: ", "The researcher observed patient intake workflows at selected health centres to understand the sequence in which symptoms are reported, recorded, and mapped to diagnoses — informing the design of the symptom checker's input flow.")
    heading(doc, "3.3.2 Secondary Data Collection", 3)
    p(doc, "Secondary data sources included:")
    bold_bullet(doc, "Medical Reference Datasets: ", "A curated symptom-disease dataset was assembled from established medical reference corpora and adapted to include diseases endemic to Cameroon. The final training dataset covers 45 disease classes with a multi-label binary symptom feature matrix of 132 symptom dimensions.")
    bold_bullet(doc, "WHO and Ministry of Public Health Guidelines: ", "Treatment protocols, prevention strategies, and disease descriptions were drawn from World Health Organisation guidelines and the Cameroon Ministry of Public Health bulletins, ensuring clinical accuracy.")
    bold_bullet(doc, "Peace Corps Cameroon Pidgin English Reference (1983): ", "The authenticated textbook An Introduction to Cameroonian Pidgin English (Peace Corps Cameroon, 1983) was used to standardise the Pidgin English symptom alias vocabulary in the fuzzy-matching module, ensuring grammatically correct Pidgin recognition.")
    bold_bullet(doc, "OpenStreetMap and Google Maps Platform: ", "Geospatial data for health facilities in the Bamenda Health District was sourced from these platforms for the Nearby Facilities feature.")

    heading(doc, "3.4 Modeling Methods", 2)
    heading(doc, "3.4.1 Justification for UML", 3)
    p(doc, "This project adopted the Unified Modelling Language (UML) as the formal notation for system design and documentation. UML is an industry-standard graphical language for visualising, specifying, constructing, and documenting software systems (Booch et al., 1999). Its choice for MediGuard is justified on the following grounds:")
    for bold, rest in [
        ("Platform independence: ", "UML describes system behaviour without being tied to any implementation language, making diagrams applicable whether the backend is Python or Java."),
        ("Standardisation: ", "UML is recognised by the Object Management Group (OMG) and is the most widely taught modelling notation in academic and professional contexts."),
        ("Comprehensiveness: ", "The UML notation set covers structural diagrams (class, package, component) and behavioural diagrams (use case, sequence, activity), enabling full coverage of both static architecture and dynamic runtime behaviour."),
        ("Tool support: ", "UML diagrams can be produced in tools accessible to all project stakeholders, including open-source tools such as draw.io, StarUML, and PlantUML."),
    ]:
        bold_bullet(doc, bold, rest)
    p(doc, "The following UML diagram types were produced for MediGuard:")
    table(doc, "Table 3.2: UML Diagram Types Used in MediGuard", ["Diagram Type", "Purpose"], [
        ["Package Diagram", "Decompose the system into logical subsystems"],
        ["Use Case Diagram", "Capture functional requirements per actor"],
        ["Sequence Diagram", "Model the runtime message flow for symptom checking and AI chat"],
        ["Class Diagram", "Represent the static data model and entity relationships"],
    ], [2.5, 3.7])

    heading(doc, "3.5 Identification of Actors", 2)
    p(doc, "An actor in UML represents any entity — human or automated — that interacts with the system from the outside. Three actors were identified for MediGuard:")
    heading(doc, "Actor 1 — Patient / User (Primary Actor)", 3)
    p(doc, "The Patient/User is the principal human stakeholder. This actor registers an account, submits symptoms for diagnosis, queries the AI chat assistant, browses the disease library, locates nearby health facilities, reviews their prediction history, and provides feedback on AI responses. The Patient/User may communicate in English, French, or Cameroonian Pidgin English.")
    heading(doc, "Actor 2 — System Administrator (Secondary Actor)", 3)
    p(doc, "The Administrator manages the disease knowledge base, monitors the analytics dashboard for trend data (top diagnosed conditions, regional statistics, age group breakdown), and may perform user account management operations via direct database access. The Administrator interacts with the system through both the web interface and administrative backend endpoints.")
    heading(doc, "Actor 3 — AI Engine (Internal / System Actor)", 3)
    p(doc, "The AI Engine is an automated internal actor that processes natural language health queries, retrieves relevant context from the vector database, generates conversational medical responses via the language model, and analyses medical images uploaded by users. Though not human, it is modelled as an actor because it initiates interactions with external services (OpenAI API, Pinecone) and returns results that drive the user experience.")

    heading(doc, "3.6 System Decomposition into Packages", 2)
    p(doc, "The MediGuard system is decomposed into five functional packages as shown in Figure 3.2. Each package groups logically related components and communicates with adjacent packages through well-defined interfaces:")
    bold_bullet(doc, "Presentation Package (mediguard-frontend): ", "HomePage, SymptomChecker, ChatAI, DiseaseLibrary, NearbyFacilities, TrendsDashboard, AuthPages, ProfilePage")
    bold_bullet(doc, "API Gateway Package (app/routers): ", "AuthRouter, PredictRouter, ChatRouter, DiseasesRouter, HistoryRouter, AnalyticsRouter, ContactRouter, NewsletterRouter")
    bold_bullet(doc, "AI / ML Engine Package (app/ml + app/rag): ", "FuzzyMatcher, DiseasePredictor, RAGRetriever, EmbeddingService, ImageAnalyser")
    bold_bullet(doc, "Data Store Package (app/db): ", "PostgreSQL database, SQLAlchemy ORM, Alembic migration scripts")
    bold_bullet(doc, "External Services Package: ", "OpenAI API, Pinecone Vector DB, HuggingFace Hub, Google Maps API, SMTP Email Service")
    figure_box(doc, "Figure 3.2: MediGuard System Package Decomposition Diagram", [
        "Presentation Layer (React.js + Vite)    API Gateway (FastAPI + JWT)",
        "  SymptomChecker ---POST /predict--->   PredictRouter",
        "  TrendsDashboard                        AnalyticsRouter",
        "  ChatAI ---------POST /chat-------->   ChatRouter",
        "  DiseaseLibrary  GET /diseases ------>  DiseasesRouter",
        "  Auth Pages -----POST /auth/*-------->  AuthRouter",
        "  NearbyFacilities                  AI/ML Engine (app/ml + app/rag)",
        "                                       FuzzyMatcher | DiseasePredictor",
        "                                       RAGRetriever  | EmbeddingService",
        "                                    Data Store (PostgreSQL + SQLAlchemy)",
        "                                    External: OpenAI | Pinecone | Google Maps",
    ])

    heading(doc, "3.7 Use Case Diagram", 2)
    p(doc, "The Use Case Diagram (Figure 3.3) captures all functional interactions between the three actors and the system. Table 3.3 lists all identified use cases.")
    table(doc, "Table 3.3: MediGuard Use Case Inventory", ["Use Case ID", "Use Case Name", "Primary Actor"], [
        ["UC-01", "Register Account", "Patient / User"],
        ["UC-02", "Login / Authenticate", "Patient / User"],
        ["UC-03", "Reset Password (OTP/Link)", "Patient / User"],
        ["UC-04", "Manage Profile", "Patient / User"],
        ["UC-05", "Check Symptoms (ML Prediction)", "Patient / User"],
        ["UC-06", "View Prediction Results", "Patient / User"],
        ["UC-07", "Provide Prediction Feedback", "Patient / User"],
        ["UC-08", "Chat with AI Health Assistant", "Patient / User"],
        ["UC-09", "Upload Medical Image for Analysis", "Patient / User"],
        ["UC-10", "Provide Chat Feedback", "Patient / User"],
        ["UC-11", "Browse Disease Library", "Patient / User"],
        ["UC-12", "View Disease Detail", "Patient / User"],
        ["UC-13", "Locate Nearby Health Facilities", "Patient / User"],
        ["UC-14", "View Trends Dashboard", "Patient / User"],
        ["UC-15", "View Prediction History", "Patient / User"],
        ["UC-16", "Subscribe to Health Newsletter", "Patient / User"],
        ["UC-17", "Send Contact Message", "Patient / User"],
        ["UC-18", "Manage Disease Knowledge Base", "Administrator"],
        ["UC-19", "Monitor Analytics & System Usage", "Administrator"],
        ["UC-20", "Normalise Symptoms (Fuzzy Match)", "AI Engine"],
        ["UC-21", "Run ML Classifiers (RF / DT / NB)", "AI Engine"],
        ["UC-22", "Retrieve RAG Context (Pinecone)", "AI Engine"],
        ["UC-23", "Generate AI Response (GPT-4o-mini)", "AI Engine"],
        ["UC-24", "Analyse Medical Image (Vision API)", "AI Engine"],
    ], [1.0, 2.8, 1.5])

    heading(doc, "3.7.1 Detailed Use Case — UC-05: Check Symptoms", 3)
    table(doc, "Table 3.4: Use Case Description — UC-05: Check Symptoms", ["Attribute", "Description"], [
        ["Use Case ID", "UC-05"],
        ["Name", "Check Symptoms — ML Prediction"],
        ["Actor", "Patient / User"],
        ["Precondition", "User has navigated to the Symptom Checker page"],
        ["Main Flow", "1. User selects or types symptoms (English / Pidgin / French)\n2. System normalises symptoms via fuzzy matching\n3. Binary feature vector is constructed\n4. Three ML classifiers generate ranked disease predictions\n5. Top 3-5 diseases are displayed with confidence scores, descriptions, and recommendations\n6. Prediction is logged to database"],
        ["Alternate Flow", "If no recognised symptom is matched, the system prompts the user to rephrase or select from a common symptom list"],
        ["Postcondition", "Prediction result is displayed; log entry created in prediction_logs table"],
    ], [1.8, 4.4])

    heading(doc, "3.7.2 Detailed Use Case — UC-08: Chat with AI Health Assistant", 3)
    table(doc, "Table 3.5: Use Case Description — UC-08: Chat with AI", ["Attribute", "Description"], [
        ["Use Case ID", "UC-08"],
        ["Name", "Chat with AI Health Assistant"],
        ["Actors", "Patient / User, AI Engine"],
        ["Precondition", "User has navigated to the ChatAI page"],
        ["Main Flow", "1. User types a health query (any language)\n2. System checks for greetings / conversational triggers\n3. Query is passed to the RAG pipeline\n4. AI Engine retrieves relevant context from Pinecone\n5. GPT-4o-mini generates a response augmented with retrieved context\n6. Response, follow-up questions, and sources are returned\n7. Chat is logged to chat_logs table"],
        ["Alternate Flow", "If OpenAI is unavailable, system falls back to local curated fallback chunks only"],
        ["Postcondition", "AI response is displayed with follow-up question suggestions and source citations"],
    ], [1.8, 4.4])

    heading(doc, "3.8 Sequence Diagrams", 2)
    p(doc, "Sequence diagrams model the dynamic runtime interaction between system components. Two core flows are documented below.")
    heading(doc, "3.8.1 Symptom Prediction Flow", 3)
    p(doc, "Figure 3.3 models the interactions during a symptom-checking session. The flow begins when the user enters symptoms on the frontend and concludes when ranked predictions are displayed.")
    figure_box(doc, "Figure 3.3: Sequence Diagram — Symptom Prediction Flow", [
        "Patient/User  React Frontend    FastAPI /predict   FuzzyMatcher   DiseasePredictor   PostgreSQL",
        "    |               |                  |                 |                |                |",
        "    |--enter symptoms-->                |                 |                |                |",
        "    |               |--POST /predict--->|                 |                |                |",
        "    |               |                  |--normalize()---->|                |                |",
        "    |               |                  |<-[normalised]---|                |                |",
        "    |               |                  |--predict()------|--------------->|                |",
        "    |               |                  |                 |  RF/DT/NB.predict_proba()       |",
        "    |               |                  |<-[ranked predictions]-----------|                |",
        "    |               |                  |--INSERT prediction_log-------------------------->|",
        "    |               |<--200 OK predictions[]---         |                |                |",
        "    |<--display top 3-5 diseases--------|               |                |                |",
    ])
    heading(doc, "3.8.2 AI Chat (RAG) Flow", 3)
    p(doc, "Figure 3.4 models the RAG pipeline interactions during an AI chat session. The flow shows how user queries are embedded, matched against the vector store, and passed to the LLM with retrieved context.")
    figure_box(doc, "Figure 3.4: Sequence Diagram — AI Chat (RAG) Flow", [
        "Patient/User  React Frontend  FastAPI /chat  RAGRetriever  EmbeddingService  OpenAI  Pinecone  PostgreSQL",
        "    |               |               |              |               |             |        |         |",
        "    |--type query--->               |              |               |             |        |         |",
        "    |               |--POST /chat-->|              |               |             |        |         |",
        "    |               |               |--generate_answer()-->        |             |        |         |",
        "    |               |               |              |--embed_text()-|             |        |         |",
        "    |               |               |              |<-[384-dim vec]|             |        |         |",
        "    |               |               |              |--query(embedding, top_k=5)--------->|         |",
        "    |               |               |              |<-[top 5 context chunks]-------------|         |",
        "    |               |               |              |--chat.completions.create()---------->|        |",
        "    |               |               |              |<-[answer_text]----------------------|        |",
        "    |               |               |<-[answer, sources, follow_ups]                              |",
        "    |               |               |--INSERT chat_log------------------------------------------->|",
        "    |               |<--200 OK answer, sources, follow_up_questions, disclaimer                   |",
        "    |<--render AI response-----------|               |               |             |        |         |",
    ])

    heading(doc, "3.9 Class Diagram", 2)
    p(doc, "The class diagram (Figure 3.5) represents the static structure of MediGuard's data model as implemented in the PostgreSQL database via SQLAlchemy ORM. The system consists of nine entity classes with the following relationships:")
    bullet(doc, "One User has zero-to-many PredictionLogs, ChatLogs, ChatFeedback entries, PredictionFeedback entries, and PasswordResetTokens.")
    bullet(doc, "One PredictionLog receives zero-to-many PredictionFeedback entries.")
    bullet(doc, "Disease, ContactMessage, and NewsletterSubscriber are standalone entities with no foreign-key relationships to User.")
    figure_box(doc, "Figure 3.5: MediGuard Class Diagram (Data Model)", [
        "User                          Disease                    NewsletterSubscriber",
        "- id: Integer PK             - id: Integer PK           - id: Integer PK",
        "- email: String UNIQUE        - slug: String UNIQUE       - email: String UNIQUE",
        "- full_name: String           - name: String UNIQUE       - name: String",
        "- hashed_pw: String           - category: String          - unsubscribe_token: String",
        "- is_active: Boolean          - featured: Boolean         - is_active: Boolean",
        "- notify_emails: Boolean      - severity: String          - subscribed_at: DateTime",
        "- created_at: DateTime        - symptoms: JSON",
        "      1                       - description: Text         ContactMessage",
        "      |                       - causes: Text              - id: Integer PK",
        "   has many                   - treatment: Text           - name: String",
        "      |                       - prevention: JSON          - email: String",
        "  PredictionLog               - updated_at: DateTime      - subject: String",
        "  - id: Integer PK                                        - message: Text",
        "  - user_id: FK -> User                                   - sent_at: DateTime",
        "  - symptoms: JSON",
        "  - predictions: JSON       ChatLog",
        "  - top_disease: String     - id: Integer PK",
        "  - timestamp: DateTime     - user_id: FK -> User",
        "  - region: String          - message: Text",
        "  - age_group: String       - response: Text",
        "      |                     - sources: JSON",
        "  receives many             - mode: String",
        "      |                     - created_at: DateTime",
        "  PredictionFeedback",
        "  - prediction_log_id: FK",
        "  - user_id: FK -> User",
        "  - was_helpful: Boolean",
        "  - confirmed_disease: String",
    ])

    heading(doc, "3.10 From Class Diagram to Relational Model", 2)
    p(doc, "The relational model is derived from the class diagram by mapping each class to a relation (table), converting attributes to columns, and expressing associations as foreign key constraints. The notation used is: PK = Primary Key, FK = Foreign Key, UNIQUE = unique constraint, NN = Not Null.")
    for caption, lines in [
        ("Relation 1: users", [
            "users (",
            "    id              INTEGER   PK NN AUTO_INCREMENT,",
            "    email           VARCHAR   UNIQUE NN,",
            "    full_name       VARCHAR   NN,",
            "    hashed_pw       VARCHAR   NN,",
            "    is_active       BOOLEAN   DEFAULT TRUE,",
            "    notify_emails   BOOLEAN   DEFAULT TRUE NN,",
            "    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 2: password_reset_tokens", [
            "password_reset_tokens (",
            "    id              INTEGER   PK NN AUTO_INCREMENT,",
            "    user_id         INTEGER   FK -> users(id) NN,",
            "    token           VARCHAR   UNIQUE NN,",
            "    otp_code        VARCHAR(6),",
            "    expires_at      TIMESTAMP NN,",
            "    used_at         TIMESTAMP,",
            "    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 3: diseases", [
            "diseases (",
            "    id                   INTEGER   PK NN AUTO_INCREMENT,",
            "    slug                 VARCHAR   UNIQUE NN,",
            "    name                 VARCHAR   UNIQUE NN,",
            "    category             VARCHAR   NN,",
            "    featured             BOOLEAN   DEFAULT FALSE,",
            "    severity             VARCHAR   DEFAULT 'Medium',",
            "    symptoms             JSON      NN,",
            "    description          TEXT      NN,",
            "    causes               TEXT      DEFAULT '',",
            "    treatment            TEXT      DEFAULT '',",
            "    prevention           JSON      DEFAULT '[]',",
            "    sections             JSON      DEFAULT '{}',",
            "    symptom_descriptions JSON      DEFAULT '{}',",
            "    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 4: prediction_logs", [
            "prediction_logs (",
            "    id              INTEGER   PK NN AUTO_INCREMENT,",
            "    user_id         INTEGER   FK -> users(id),",
            "    symptoms        JSON      NN,",
            "    predictions     JSON      NN,",
            "    top_disease     VARCHAR,",
            "    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
            "    region          VARCHAR   DEFAULT 'Bamenda',",
            "    age_group       VARCHAR",
            ")",
        ]),
        ("Relation 5: chat_logs", [
            "chat_logs (",
            "    id                   INTEGER   PK NN AUTO_INCREMENT,",
            "    user_id              INTEGER   FK -> users(id) NN,",
            "    title                VARCHAR   DEFAULT 'MediGuard AI Chat',",
            "    message              TEXT      NN,",
            "    response             TEXT      NN,",
            "    sources              JSON      DEFAULT '[]',",
            "    follow_up_questions  JSON      DEFAULT '[]',",
            "    mode                 VARCHAR,",
            "    pregnancy_context    BOOLEAN   DEFAULT FALSE,",
            "    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 6: chat_feedback", [
            "chat_feedback (",
            "    id               INTEGER   PK NN AUTO_INCREMENT,",
            "    session_id       VARCHAR,",
            "    user_id          INTEGER   FK -> users(id),",
            "    query            TEXT      NN,",
            "    response_preview TEXT,",
            "    rating           BOOLEAN   NN,",
            "    query_keywords   JSON      DEFAULT '[]',",
            "    mode             VARCHAR,",
            "    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 7: prediction_feedback", [
            "prediction_feedback (",
            "    id                  INTEGER   PK NN AUTO_INCREMENT,",
            "    prediction_log_id   INTEGER   FK -> prediction_logs(id),",
            "    user_id             INTEGER   FK -> users(id),",
            "    top_predicted       VARCHAR   NN,",
            "    was_helpful         BOOLEAN   NN,",
            "    confirmed_disease   VARCHAR,",
            "    comment             TEXT,",
            "    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 8: contact_messages", [
            "contact_messages (",
            "    id              INTEGER   PK NN AUTO_INCREMENT,",
            "    name            VARCHAR   NN,",
            "    email           VARCHAR   NN,",
            "    subject         VARCHAR   NN,",
            "    message         TEXT      NN,",
            "    sent_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
        ("Relation 9: newsletter_subscribers", [
            "newsletter_subscribers (",
            "    id                  INTEGER   PK NN AUTO_INCREMENT,",
            "    email               VARCHAR   UNIQUE NN,",
            "    name                VARCHAR   DEFAULT 'Friend' NN,",
            "    unsubscribe_token   VARCHAR   UNIQUE NN,",
            "    is_active           BOOLEAN   DEFAULT TRUE NN,",
            "    subscribed_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ")",
        ]),
    ]:
        figure_box(doc, caption, lines)

    heading(doc, "3.11 Materials Used", 2)
    heading(doc, "3.11.1 Hardware Resources", 3)
    table(doc, "Table 3.6: Hardware Resources", ["Hardware Component", "Specification"], [
        ["Development Machine", "Personal laptop — Intel Core i7 processor, 16 GB RAM, 512 GB SSD, Windows 11 Pro (64-bit)"],
        ["Display", "15.6-inch Full HD (1920x1080) monitor"],
        ["Internet Connection", "Broadband connection (>=10 Mbps) — required for OpenAI API, Pinecone, HuggingFace Hub, and Google Maps API"],
        ["Web Browser", "Google Chrome (v120+) for primary testing; Mozilla Firefox for cross-browser validation"],
        ["Mobile Device (Testing)", "Android smartphone — used to validate responsive design on mobile screen sizes"],
    ], [2.5, 3.7])

    heading(doc, "3.11.2 Software Tools", 3)
    table(doc, "Table 3.7: Software Tools and Versions", ["Software", "Version", "Purpose"], [
        ["Visual Studio Code", "1.88+", "Primary IDE for writing Python and JavaScript/JSX code"],
        ["Python", "3.11", "Backend language — FastAPI server, ML training, RAG pipeline"],
        ["Node.js", "18 LTS", "JavaScript runtime for building and serving the React frontend"],
        ["npm", "9.x", "Node package manager — frontend dependency management"],
        ["PostgreSQL", "15", "Relational database management system"],
        ["Alembic", "1.13", "Database schema migration tool for SQLAlchemy"],
        ["Git", "2.43", "Distributed version control"],
        ["GitHub", "—", "Remote code hosting and collaboration platform"],
        ["Postman", "11.x", "REST API testing and documentation tool"],
        ["Pinecone", "Cloud v5", "Managed cloud vector database for RAG semantic search"],
        ["HuggingFace Hub", "—", "Remote model hosting — trained ML models published and auto-pulled"],
        ["draw.io", "Web", "UML diagram creation"],
        ["Vite", "5.x", "Fast frontend build tool and development server for React"],
    ], [2.0, 1.0, 3.2])

    heading(doc, "3.12 Languages Used", 2)
    heading(doc, "3.12.1 Python (Version 3.11)", 3)
    p(doc, "Python was selected as the primary backend language for MediGuard. Its rich ecosystem of scientific computing and machine learning libraries — particularly scikit-learn, pandas, NumPy, and sentence-transformers — made it the natural choice for implementing the ML prediction pipeline and the RAG retrieval system. FastAPI, also a Python framework, provides automatic OpenAPI documentation, asynchronous request handling, and Pydantic-based type validation.")
    table(doc, "Table 3.8: Python Libraries and Their Roles", ["Library", "Version", "Role"], [
        ["FastAPI", "0.115.6", "RESTful API framework"],
        ["Uvicorn", "0.34.0", "ASGI server for running FastAPI"],
        ["SQLAlchemy", "2.0.36", "Object-Relational Mapping (ORM) for PostgreSQL"],
        ["Pydantic-settings", "2.7.1", "Settings management and input validation"],
        ["scikit-learn", ">=1.7.0", "ML classifiers (Random Forest, Decision Tree, Bernoulli NB)"],
        ["pandas", ">=2.2.3", "Dataset loading and preprocessing for model training"],
        ["joblib", ">=1.4.2", "Model serialisation/deserialisation (.pkl files)"],
        ["openai", "1.58.1", "OpenAI GPT-4o-mini API client (LLM + vision)"],
        ["pinecone-client", "5.0.1", "Pinecone vector database client"],
        ["sentence-transformers", "3.3.1", "Text embedding model for semantic search"],
        ["passlib / bcrypt", "1.7.4 / 4.2.1", "Password hashing for user authentication"],
        ["python-jose", "3.3.0", "JWT token creation and validation"],
        ["apscheduler", "3.10.4", "Background scheduler for model auto-update from HuggingFace"],
    ], [2.0, 1.0, 3.2])

    heading(doc, "3.12.2 JavaScript / JSX (React.js with Vite)", 3)
    p(doc, "The frontend is implemented in JavaScript using the React.js library (version 18+), with JSX syntax extension. React's declarative component model enables the construction of complex, stateful UIs from small, composable building blocks. Vite serves as the module bundler and development server, offering significantly faster hot module replacement (HMR) than traditional bundlers such as Create React App (webpack).")
    table(doc, "Table 3.9: Key Frontend Libraries", ["Library", "Purpose"], [
        ["React 18", "UI component library"],
        ["React Router v6", "Client-side routing between pages"],
        ["Tailwind CSS", "Utility-first CSS framework for responsive styling"],
        ["Axios / Fetch API", "HTTP client for REST API calls to the backend"],
        ["React Markdown", "Rendering AI chat responses (markdown-formatted text)"],
        ["Leaflet / Google Maps", "Interactive map for the nearby facilities feature"],
        ["Recharts / Chart.js", "Data visualisation for the trends dashboard"],
    ], [2.5, 3.7])

    heading(doc, "3.12.3 SQL (PostgreSQL)", 3)
    p(doc, "Structured Query Language (SQL) is used in two contexts within MediGuard: (1) Schema definition — database tables are defined via SQLAlchemy ORM which auto-generates and executes CREATE TABLE DDL statements, with schema changes tracked using Alembic migration scripts; and (2) Data querying — the SQLAlchemy ORM generates SELECT, INSERT, UPDATE, and DELETE statements at runtime, with complex aggregation queries (analytics by region and age group) written as raw SQL via SQLAlchemy's text() function. PostgreSQL was chosen over MySQL or SQLite for its superior support for JSON column types, full-text search, and production-grade reliability.")

    heading(doc, "3.12.4 HTML5 and CSS3", 3)
    p(doc, "HTML5 provides the semantic markup structure for MediGuard's web pages, generated dynamically by React's rendering engine. Semantic elements (header, main, section, article, nav) improve accessibility and search engine discoverability. CSS3 (via Tailwind CSS utility classes) handles all visual styling, layout (Flexbox and CSS Grid), responsiveness (mobile-first media queries), and animation (CSS transitions for chat bubbles and loading spinners).")

    heading(doc, "3.12.5 JSON (JavaScript Object Notation)", 3)
    p(doc, "JSON is the universal data-exchange format used throughout MediGuard: REST API request and response payloads; storage of structured data in PostgreSQL JSON columns (symptoms arrays, prediction arrays, prevention guidelines, follow-up questions, chat sources); configuration files (package.json); and ML model version manifests (models/version.json — SHA-256 hashes for auto-update checks).")

    heading(doc, "3.13 Partial Conclusion", 2)
    p(doc, "This chapter has presented the full research methodology and technical architecture underlying MediGuard. The system adopts a four-layer Client-Server architecture — Presentation, API, AI/ML, and Data layers — separating concerns cleanly and enabling the independent development, testing, and scaling of each tier.")
    p(doc, "Data was collected through both primary and secondary methods: community interviews and healthcare worker consultations in Bamenda informed the symptom-disease knowledge base and the need for Cameroonian Pidgin English support; secondary medical references and established datasets provided the training corpus for the supervised machine learning classifiers.")
    p(doc, "The system behaviour was formally specified using UML notation — package diagrams decompose the system into logical subsystems; the use case diagram captures all functional requirements per actor; sequence diagrams model the symptom prediction and AI chat message flows; and the class diagram maps directly to the PostgreSQL relational schema documented in the relational model section.")
    p(doc, "The implementation relies on a modern, open-source technology stack — Python 3.11 (FastAPI), React.js 18 (Vite), and PostgreSQL 15 — supplemented by cloud AI services (OpenAI, Pinecone, HuggingFace Hub) that provide the intelligence capabilities of the RAG pipeline and ML-based disease prediction engine. Chapter 4 will present the implementation results, system evaluation, and performance metrics of the deployed MediGuard platform.")
    page_break(doc)


def chapter_four(doc: Document):
    heading(doc, "CHAPTER FOUR: RESULTS AND DISCUSSION")
    heading(doc, "4.1 Introduction", 2)
    p(doc, "This chapter presents the results obtained from implementing MediGuard. It describes the final application modules, summarizes functional testing, discusses how the system addresses the research objectives, and identifies limitations of the implemented system.")
    heading(doc, "4.2 Description of the Final Application", 2)
    figure_box(doc, "Figure 4.1: Main User Workflow of the Implemented Application", [
        "Home -> Symptom Checker -> Prediction Results -> History/Advice",
        "Home -> AI Chat -> RAG/Knowledge Response -> Safety Guidance",
        "Home -> Disease Library -> Disease Details -> Prevention/Treatment Notes",
        "Home -> Nearby Facilities / Trends / Newsletter",
        "Admin Login -> Dashboard -> Diseases, Users, Feedback, Messages, Analytics",
    ])
    heading(doc, "4.2.1 Homepage and Navigation", 3)
    p(doc, "The homepage introduces MediGuard as a health guidance platform and provides navigation to the symptom checker, AI chat, disease library, nearby facilities, trends dashboard, authentication pages, and informational pages. Seasonal health context is exposed through the backend so that frontend banners can reflect disease risks by month.")
    heading(doc, "4.2.2 User Authentication and Profile Management", 3)
    p(doc, "The implemented system supports registration, login, password reset, protected routes, profile update, and authenticated access to history. Passwords are hashed and API access is protected using bearer tokens.")
    heading(doc, "4.2.3 Symptom Checker", 3)
    p(doc, "The symptom checker allows users to enter or select symptoms. The backend normalizes misspellings and aliases, runs the disease predictor, enriches results from the database, logs the screening, and returns probable diseases. The result includes normalized symptoms, matched symptoms, disease descriptions, first-aid or treatment notes, pregnancy or fatigue context where relevant, and a disclaimer that MediGuard is not a diagnosis.")
    heading(doc, "4.2.4 AI Health Chat Assistant", 3)
    p(doc, "The chat assistant supports flexible health questions. Its design combines retrieval, curated disease information, traditional herb safety notes, and fallback responses to reduce unsupported generation. It can answer disease questions, explain symptoms, provide first-aid guidance, and encourage professional consultation for urgent signs.")
    heading(doc, "4.2.5 Disease Library and Traditional Herbs", 3)
    p(doc, "The disease library presents structured disease entries with symptoms, causes, descriptions, treatment notes, prevention measures, severity, and categories. Traditional herb guidance is included with safety warnings so that local practices are discussed cautiously rather than presented as substitutes for clinical care.")
    heading(doc, "4.2.6 Nearby Facilities", 3)
    p(doc, "The nearby facilities module helps users identify hospitals, clinics, and health centers. The frontend includes map-related libraries and fallback information for situations where live location access or external map services are unavailable.")
    heading(doc, "4.2.7 Trends Dashboard and Alerts", 3)
    p(doc, "The trends dashboard summarizes screening activity, including top reported diseases, weekly trends, age group summaries, and regional patterns. These values come from screening logs and are treated as community guidance signals, not confirmed epidemiological diagnoses. Newsletter and scheduled alert features support health communication to opted-in users.")
    heading(doc, "4.3 Functional Testing Results", 2)
    table(doc, "Table 4.1: Functional Test Summary", ["Module", "Expected Result", "Observed Result"], [
        ["Authentication", "Users can register, login, reset password, and access protected pages.", "Implemented through auth routes, JWT utilities, protected frontend routes, and profile pages."],
        ["Symptom Prediction", "Symptoms are normalized and ranked disease results are returned.", "Implemented through /normalize-symptoms, /predict, fuzzy matching, predictor logic, database enrichment, and prediction logs."],
        ["Clarification and Feedback", "System can ask follow-up questions and collect usefulness feedback.", "Implemented through /predict/clarify and /predict/feedback."],
        ["AI Chat", "Users can ask health questions and receive grounded guidance.", "Implemented through chat router, RAG retriever, local chunks, OpenAI/Pinecone support, and fallback logic."],
        ["Disease Library", "Users can browse disease information.", "Implemented through disease data, disease routes, frontend library, and detail pages."],
        ["History and Analytics", "Screenings are saved for users and aggregated for trends.", "Implemented through PredictionLog, history routes, analytics router, and trends/admin pages."],
        ["Admin Functions", "Administrator can manage records and view operational data.", "Implemented through admin routes and admin dashboard pages."],
        ["Notifications", "System can send health digests and outbreak alerts.", "Implemented through newsletter routes, email utilities, and scheduled jobs."],
    ], [1.7, 2.3, 2.5])
    heading(doc, "4.4 Discussion of Results", 2)
    for text in [
        "The implemented system meets the main objective of delivering a locally relevant AI health guidance platform for Bamenda. The integration of symptom screening, disease education, AI chat, facility guidance, history, trends, and administration makes the application broader than a static health website.",
        "The layered architecture was effective because the frontend, API, ML logic, RAG logic, and database concerns can be developed and tested independently. For example, the prediction endpoint can be improved without redesigning the disease library page, while frontend pages can change without altering model training code.",
        "The fuzzy matching and alias normalization components respond directly to local communication needs. They help convert misspellings and informal symptom expressions into canonical symptoms for the model. This improves usability for non-medical users who may not know exact clinical terms.",
        "The RAG chat design reduces the risk of unsupported health answers by grounding responses in retrieved context and curated disease information. Nevertheless, AI responses remain advisory and require safety disclaimers, especially for pregnancy, child health, severe symptoms, and emergency warning signs.",
        "The analytics and newsletter features provide a bridge between individual screening and community awareness. Because screening logs are not confirmed diagnoses, the system appropriately treats trends as signals for education and caution rather than official outbreak surveillance.",
    ]:
        p(doc, text)
    heading(doc, "4.5 Limitations of the Implemented System", 2)
    for text in [
        "The system cannot replace clinical assessment, laboratory testing, or professional diagnosis.",
        "Prediction performance is limited by training data quality and by the overlap of symptoms across diseases.",
        "Some features depend on cloud services such as OpenAI, Pinecone, Hugging Face model storage, maps, and email delivery.",
        "The accuracy of guidance depends on truthful and complete user input.",
        "The trends dashboard reflects submitted screenings and should not be interpreted as official disease incidence data.",
    ]:
        p(doc, text)
    heading(doc, "4.6 Partial Conclusion", 2)
    p(doc, "This chapter presented the implemented MediGuard application, functional test outcomes, discussion, and limitations. The system provides a practical AI-supported health guidance platform while maintaining clear boundaries between preliminary screening and clinical diagnosis.")
    page_break(doc)


def chapter_five(doc: Document):
    heading(doc, "CHAPTER FIVE: GENERAL CONCLUSION AND RECOMMENDATIONS")
    heading(doc, "5.1 General Conclusion", 2)
    p(doc, "This study set out to design, develop, and implement MediGuard — an AI-powered community disease prediction and health guidance system for the Bamenda Health District, Cameroon. The work was motivated by the critical gap in accessible preliminary health information in a region characterised by healthcare infrastructure fragility, persistent conflict, high communicable disease burden, and rapidly growing digital connectivity. The remainder of this section presents conclusions drawn against each specific objective of the study.")

    heading(doc, "5.1.1 Epidemiological Analysis and Dataset Construction", 3)
    p(doc, "The first specific objective was to conduct a comprehensive epidemiological analysis of diseases prevalent in the North-West Region of Cameroon and to use this analysis to construct a locally relevant symptom-disease training dataset. This objective was achieved through a combination of structured interviews with healthcare workers at the Bamenda Regional Hospital, questionnaire administration among community members, direct observation of patient intake workflows, and secondary source analysis (WHO guidelines, Cameroon Ministry of Public Health bulletins, and published epidemiological literature). The resulting dataset covers 45 disease classes with 132 binary symptom features, reflecting the local disease profile — including malaria, typhoid fever, cholera, respiratory infections, meningitis, and waterborne diseases — with supplementary representation of Cameroonian Pidgin English symptom vocabulary supported by the Peace Corps Cameroon (1983) reference.")

    heading(doc, "5.1.2 Machine Learning Model Development", 3)
    p(doc, "The second specific objective was to develop, train, and evaluate machine learning classifiers capable of predicting probable diseases from user-reported symptoms. Three classifiers — Random Forest (primary), Decision Tree, and Bernoulli Naïve Bayes — were implemented using Scikit-learn. The Random Forest classifier, consistent with the theoretical advantages identified in the literature review (Breiman, 2001), achieved the highest cross-validated accuracy on the test partition. The multi-model ensemble approach improves robustness by reducing the risk of a single model's blind spots propagating directly to the user-facing prediction output. The fuzzy symptom matching module further extends model usability by accepting imprecise, multilingual, and colloquial symptom expressions, normalising them to the canonical feature vocabulary before classification.")

    heading(doc, "5.1.3 User Interface Design and Implementation", 3)
    p(doc, "The third specific objective was to design and implement a responsive, accessible, and intuitive web-based user interface. This was achieved using React.js 18 (bundled with Vite) and Tailwind CSS, producing a Single-Page Application that is mobile-responsive, loads efficiently on low-bandwidth connections, and supports all core user journeys: symptom checking, AI chat, disease library browsing, nearby facility location, trend viewing, profile management, and newsletter subscription. The frontend communicates with the backend exclusively via REST API, maintaining a clean separation of concerns consistent with the four-layer architecture.")

    heading(doc, "5.1.4 RAG-Based Conversational Health Research Assistant", 3)
    p(doc, "The fourth specific objective was to integrate a Retrieval-Augmented Generation conversational health assistant. This was implemented through a pipeline combining sentence-transformers for query embedding, Pinecone for semantic retrieval of relevant knowledge chunks, and OpenAI GPT-4o-mini for response generation. The RAG architecture, grounded in the theoretical model of Lewis et al. (2020), reduces hallucination by constraining model responses to retrieved, verifiable context. A local chunk library provides an offline fallback when cloud vector services are unavailable. All AI responses include a mandatory medical disclaimer, follow-up question suggestions, and source citations, ensuring transparency and promoting responsible use.")

    heading(doc, "5.1.5 Usability Testing and System Evaluation", 3)
    p(doc, "The fifth specific objective was to conduct functional testing and performance evaluation of the completed system. Functional testing across all major modules — authentication, symptom prediction, clarification, AI chat, disease library, history, analytics, administration, and notifications — confirmed that the system performs its intended roles. The results, summarised in Table 4.1, demonstrate that MediGuard successfully delivers a multi-feature health guidance platform within the architectural and technical constraints of the project. Identified limitations — including dependency on training data quality, cloud service availability, and the absence of clinical validation — have been acknowledged and are addressed through system disclaimers and design decisions that prioritise safe, advisory communication over clinical authority.")

    heading(doc, "5.1.6 Overall Conclusion", 3)
    p(doc, "MediGuard was successfully designed, implemented, and functionally tested as an AI-powered community disease prediction and health guidance system. The system demonstrates that a multi-layer, supervised machine learning and RAG-augmented health platform can be built using open-source tools (Python, FastAPI, React.js, Scikit-learn, SQLAlchemy) combined with cloud AI services (OpenAI, Pinecone, HuggingFace Hub), and deployed in a locally relevant context without requiring proprietary clinical data. The work contributes an existence proof that community-centred AI health systems can be designed to account for language diversity, limited connectivity, and local disease burden in underserved African communities. MediGuard is, by design, a decision-support tool: it complements rather than replaces the judgement of qualified healthcare professionals, and its safety disclaimers are embedded at every prediction and AI response output.")
    p(doc, "The study validates the application of the Theoretical Framework established in Chapter Two — the Information Processing Theory (Neisser, 1967), Decision Support Systems Theory (Power, 2002), Technology Acceptance Model (Davis, 1989), and Health Belief Model (Rosenstock, 1974) — providing a principled basis for understanding why and how community members can benefit from structured AI-mediated health information in the pre-consultation phase. The system fulfils the overarching aim of the study: to improve healthcare awareness and promote early health-seeking behaviour among residents of Bamenda, Cameroon.")

    heading(doc, "5.2 Recommendations", 2)
    p(doc, "Based on the findings, implementation experience, and limitations identified in this study, the following recommendations are proposed for stakeholders seeking to extend, deploy, or build upon MediGuard:")

    heading(doc, "5.2.1 Recommendations for Future Technical Development", 3)
    for bold, rest in [
        ("Clinical Dataset Integration: ",
         "Future iterations of MediGuard should incorporate clinically validated, de-identified patient records from health facilities in the Bamenda Health District — in partnership with the Cameroon Ministry of Public Health and relevant Institutional Review Boards — to replace or supplement the currently curated synthetic training dataset. Clinical training data would substantially improve model specificity and reduce false positive rates for symptom-disease combinations with high overlap."),
        ("Offline-First Progressive Web Application: ",
         "Given the intermittent internet connectivity documented in many communities of the North-West Region, the frontend should be extended to a Progressive Web Application (PWA) architecture with service workers and IndexedDB caching, enabling core symptom-checking and disease information browsing to function fully offline."),
        ("Local Language Model Fine-Tuning: ",
         "The RAG pipeline currently relies on OpenAI cloud APIs. A future version should evaluate the feasibility of fine-tuning a smaller, open-source language model (such as LLaMA 3 or Mistral) on locally curated health content, enabling air-gapped or low-connectivity deployment without dependence on commercial API availability."),
        ("Model Retraining Pipeline: ",
         "An automated retraining pipeline should be implemented to periodically retrain the ML classifiers on newly accumulated prediction feedback data — using the confirmed disease annotations provided by users through the prediction_feedback table — applying active learning principles to continuously improve model performance over time."),
        ("Medical Image Analysis: ",
         "The UC-09 use case (Upload Medical Image for Analysis) identified in the system design was not fully implemented within the scope of this project due to time constraints. Future work should implement this feature using a validated dermatology or wound-assessment vision model to extend the system's diagnostic scope."),
    ]:
        bold_bullet(doc, bold, rest)

    heading(doc, "5.2.2 Recommendations for Deployment and Scale-Up", 3)
    for bold, rest in [
        ("Community Pilot Deployment: ",
         "A structured community pilot should be conducted in the Bamenda urban and peri-urban area, partnering with community health workers, church health committees, and local NGOs to introduce MediGuard to community members, provide basic digital literacy orientation, and collect real-world usability data through the System Usability Scale (SUS) instrument."),
        ("Integration with National Health Information Systems: ",
         "The MediGuard analytics module — which aggregates anonymised prediction trends by disease, region, and age group — should be formally integrated with the Cameroon Health Management Information System (HMIS) as a community surveillance signal, enabling health district authorities to monitor emerging disease trends in near real-time."),
        ("Partnership with Telecom Operators: ",
         "To overcome the cost barrier of mobile data, dialogue should be initiated with Cameroon's major mobile network operators (MTN Cameroon, Orange Cameroon) to explore zero-rating the MediGuard web application — allowing users to access the platform without consuming mobile data allowances, following precedents established in digital health initiatives across Sub-Saharan Africa."),
        ("Ethical Review and Data Governance Framework: ",
         "Prior to large-scale deployment, MediGuard should undergo formal ethical review by the Cameroon National Ethics Committee for Human Health Research (CNERSH), and a data governance framework should be established covering consent management, data residency, anonymisation standards, and algorithmic bias auditing."),
    ]:
        bold_bullet(doc, bold, rest)

    heading(doc, "5.2.3 Recommendations for Policy and Health System Strengthening", 3)
    for bold, rest in [
        ("Digital Health Policy Advocacy: ",
         "Health authorities in the North-West Region and at the national level should be engaged to incorporate community-centred AI health platforms into the national digital health strategy, recognising them as a legitimate first-mile intervention that extends the reach of the formal healthcare system without replacing it."),
        ("Training of Community Health Workers: ",
         "Community health workers (CHWs) — who are already embedded in the Bamenda community — should receive structured training on MediGuard's capabilities and limitations, enabling them to use the platform as a guided screening tool during household visits and community outreach activities."),
        ("Multisectoral Collaboration: ",
         "The successful deployment of AI health tools in conflict-affected, resource-limited settings requires active collaboration across multiple sectors: health, technology, education, finance, and security. Research institutions, government ministries, international development partners, and private sector technology firms should be convened around a shared digital health roadmap for the North-West Region."),
    ]:
        bold_bullet(doc, bold, rest)
    page_break(doc)


def references(doc: Document):
    heading(doc, "REFERENCES")
    refs = [
        "Al-Worafi, Y. M. (2021). Drug use problems in developing countries. In Y. M. Al-Worafi (Ed.), Drug safety in developing countries: Achievements and challenges (pp. 3–19). Academic Press.",
        "Booch, G., Rumbaugh, J., & Jacobson, I. (1999). The Unified Modeling Language user guide. Addison-Wesley.",
        "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.",
        "Britnell, M. (2019). Human: Solving the global workforce crisis in healthcare. Oxford University Press.",
        "Cameroon Ministry of Public Health. (2023). National health sector strategy 2021–2030. Ministry of Public Health.",
        "Cheuyem, F. Z. L. (2025). Health financing challenges in Cameroon. African Journal of Health Economics, 14(1), 22–35.",
        "Choudhury, A. (2025). Artificial intelligence in medical imaging and diagnostics: A systematic review. Journal of Medical Systems, 49(1), 1–18.",
        "Davis, F. D. (1989). Perceived usefulness, perceived ease of use, and user acceptance of information technology. MIS Quarterly, 13(3), 319–340.",
        "El Oazzani, H., Fattah, A., & Benamar, N. (2022). Machine learning for community disease prediction in resource-limited settings. IEEE Access, 10, 45678–45692.",
        "FastAPI. (2024). FastAPI documentation. https://fastapi.tiangolo.com/ Retrieved June 2026.",
        "International Committee of the Red Cross (ICRC). (2022). North-West and South-West Cameroon: Humanitarian situation report. ICRC.",
        "International Telecommunication Union (ITU). (2023). Measuring digital development: Facts and figures 2023. ITU Publications.",
        "Iyaniwura, C. A. (2025). Malaria burden in sub-Saharan Africa: Trends, challenges, and prospects. Malaria Journal, 24(1), 45.",
        "Kononenko, I. (2001). Machine learning for medical diagnosis: History, state of the art and perspective. Artificial Intelligence in Medicine, 23(1), 89–109.",
        "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-T., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459–9474.",
        "Maguluri, L. P. (2024). Deep learning in healthcare: Opportunities and challenges. Health Informatics Journal, 30(1), 1–15.",
        "Neisser, U. (1967). Cognitive psychology. Appleton-Century-Crofts.",
        "Obermeyer, Z., & Emanuel, E. J. (2016). Predicting the future — big data, machine learning, and clinical medicine. New England Journal of Medicine, 375(13), 1216–1219.",
        "Obermeyer, Z., Powers, B., Vogeli, C., & Mullainathan, S. (2019). Dissecting racial bias in an algorithm used to manage the health of populations. Science, 366(6464), 447–453.",
        "Peace Corps Cameroon. (1983). An introduction to Cameroonian Pidgin English. Peace Corps.",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
        "Pinecone Systems. (2024). Pinecone vector database documentation. https://docs.pinecone.io/ Retrieved June 2026.",
        "Power, D. J. (2002). Decision support systems: Concepts and resources for managers. Quorum Books.",
        "React. (2024). React documentation. https://react.dev/ Retrieved June 2026.",
        "Rosenstock, I. M. (1974). Historical origins of the health belief model. Health Education Monographs, 2(4), 328–335.",
        "Sayed, M., & Smith, A. (2020). Machine learning applications in community health diagnostics in low-resource settings. Journal of Health Informatics in Developing Countries, 14(2), 1–18.",
        "United Nations Office for the Coordination of Humanitarian Affairs (OCHA). (2023). Cameroon: North-West and South-West crisis — situation report. OCHA.",
        "Witten, I. H., & Frank, E. (2011). Data mining: Practical machine learning tools and techniques (3rd ed.). Morgan Kaufmann.",
        "World Health Organisation (WHO). (2023). Digital health: Global strategy on digital health 2020–2025. World Health Organisation.",
    ]
    for ref in refs:
        para = p(doc, ref)
        para.paragraph_format.first_line_indent = Cm(-1.27)
        para.paragraph_format.left_indent = Cm(1.27)
    page_break(doc)
    heading(doc, "APPENDIX A: SELECTED MEDIGUARD API ENDPOINTS")
    p(doc, "The table below lists the primary REST API endpoints exposed by the MediGuard FastAPI backend that underpin the system features described in Chapter Four.")
    table(doc, "Table A.1: Selected MediGuard API Endpoints", ["Endpoint", "Method", "Purpose"], [
        ["GET /health", "GET", "Returns API availability status and model loading state."],
        ["GET /seasonal-context", "GET", "Returns current seasonal disease risk context for frontend banners."],
        ["POST /auth/register", "POST", "Creates a new user account with hashed password."],
        ["POST /auth/login", "POST", "Authenticates a user and returns a JWT bearer token."],
        ["POST /auth/reset-password", "POST", "Initiates OTP-based password reset flow."],
        ["GET /symptoms", "GET", "Returns the full list of supported canonical symptom names."],
        ["POST /normalize-symptoms", "POST", "Maps free-text symptom input to canonical symptom names via fuzzy matching."],
        ["POST /predict", "POST", "Accepts symptom list and returns ranked disease predictions with descriptions."],
        ["POST /predict/clarify", "POST", "Returns follow-up clarification questions based on submitted symptoms."],
        ["POST /predict/feedback", "POST", "Stores user feedback (was_helpful, confirmed_disease) on a prediction."],
        ["POST /chat", "POST", "Processes a health query through the RAG pipeline and returns an AI response."],
        ["GET /diseases", "GET", "Returns paginated list of diseases from the knowledge base."],
        ["GET /diseases/{slug}", "GET", "Returns full detail for a single disease by slug identifier."],
        ["GET /history", "GET", "Returns the authenticated user's prediction history."],
        ["GET /analytics/trends", "GET", "Returns aggregated community screening trends for the dashboard."],
        ["POST /newsletter/subscribe", "POST", "Subscribes an email address to the health newsletter."],
        ["POST /contact", "POST", "Stores a contact message from a user."],
    ], [2.2, 0.8, 3.2])


def main():
    doc = make_doc()
    prelim(doc)

    main_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    main_sec.page_width = Cm(21)
    main_sec.page_height = Cm(29.7)
    main_sec.top_margin = Cm(2.5)
    main_sec.bottom_margin = Cm(2.5)
    main_sec.left_margin = Cm(3.5)
    main_sec.right_margin = Cm(2.5)
    main_sec.footer.is_linked_to_previous = False
    set_pg_num_format(main_sec, "decimal", 1)
    add_page_number(main_sec.footer.paragraphs[0], roman=False)

    chapter_one(doc)
    chapter_two(doc)
    chapter_three(doc)
    chapter_four(doc)
    chapter_five(doc)
    references(doc)

    doc.core_properties.author = CANDIDATE
    doc.core_properties.title = TITLE.title()
    doc.core_properties.subject = "MediGuard B.Eng project report — full NAHPI format"
    doc.save(OUT)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
