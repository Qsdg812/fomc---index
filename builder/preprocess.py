import re
from pathlib import Path
from typing import List, Dict

ABBREVIATIONS = [
    "U.S.", "Mr.", "Mrs.", "Ms.", "Dr.", "St.", "No.", "Inc.", "Ltd.", "Jr.", "Sr.", "Co.", "vs.",
    "Prof.", "Fig.", "Eq.", "cf.", "e.g.", "i.e.", "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.",
    "Aug.", "Sep.", "Sept.", "Oct.", "Nov.", "Dec."
]

SECTION_TITLES = [
    "Staff Economic Outlook",
    "Staff Review of the Economic Situation",
    "Staff Review of the Financial Situation",
    "Participants' Views on Current Conditions and the Economic Outlook",
    "Participants' Assessments of the Outlook",
    "Committee Policy Action",
    "Implementation Note",
    "Votes for this action",
    "Summary of Economic Projections",
]

def _normalize_and_protect(text: str) -> str:
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=\d)\.(?=\d)", "§", text)           # 1.5 → 1§5
    for abbr in ABBREVIATIONS:
        text = text.replace(abbr, abbr.replace(".", "§"))  # U.S. → U§S§
    text = re.sub(r"\b([A-Z])\.(?=\s+[A-Z])", r"\1§", text) # J. Powell → J§ Powell
    return text

def split_sentences(text: str) -> List[str]:
    p = _normalize_and_protect(text)
    parts = re.split(r"(?<!§)([.!?])\s+", p)
    sents: List[str] = []
    i = 0
    while i < len(parts) - 1:
        seg, punct = parts[i], parts[i+1]
        sent = (seg + punct).replace("§", ".").strip(' \t\n"\'')
        sent = re.sub(r"^\s*[•\-\u2022]\s*", "", sent)
        if sent:
            sents.append(sent)
        i += 2
    if i < len(parts):
        tail = parts[i].replace("§", ".").strip(' \t\n"\'')
        if tail:
            sents.append(tail)
    return sents

def split_minutes_sections(full_text: str) -> Dict[str, List[str]]:
    pattern = "|".join([re.escape(t) for t in SECTION_TITLES])
    marked = re.sub(f"({pattern})", r"\n@@SECTION@@ \1\n", full_text, flags=re.I)
    chunks = [c.strip() for c in marked.split("@@SECTION@@") if c.strip()]
    sections: Dict[str, List[str]] = {}
    current_title = "Preamble"
    for ch in chunks:
        m = re.match(r"([^\n]+)\n(.*)", ch, flags=re.S)
        if m:
            title, body = m.group(1).strip(), m.group(2).strip()
        else:
            title, body = current_title, ch
        sections[title] = split_sentences(body)
        current_title = title
    return sections

def preprocess_text_files(text_paths: List[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for tp in text_paths:
        p = Path(tp)
        name = p.stem
        text = p.read_text(encoding="utf-8", errors="ignore")
        lower_name = p.name.lower()

        # 날짜 추출(파일명 어디에 있어도 YYYY-MM-DD만 찾으면 OK)
        m = re.search(r"\d{4}-\d{2}-\d{2}", name)
        date_part = m.group(0) if m else name.split("_")[0]

        # Minutes 류
        if ("minutes" in lower_name) or ("rmpstc" in lower_name) or ("seo" in lower_name):
            # 파일명에 섹션 힌트가 들어온 특수 케이스 (예: FOMC_SEO_2023-10-31)
            if "fomc_" in lower_name and "_" in lower_name:
                try:
                    sec_tag = lower_name.split("_")[1].upper()
                except Exception:
                    sec_tag = "MINUTES"
                for s in split_sentences(text):
                    rows.append({"date": date_part, "doc_type": "minutes",
                                 "section": sec_tag, "sentence": s})
            else:
                for sec_title, sents in split_minutes_sections(text).items():
                    for s in sents:
                        rows.append({"date": date_part, "doc_type": "minutes",
                                     "section": sec_title, "sentence": s})
        else:  # Statements
            for s in split_sentences(text):
                rows.append({"date": date_part, "doc_type": "statement",
                             "section": "Statement", "sentence": s})
    return rows
