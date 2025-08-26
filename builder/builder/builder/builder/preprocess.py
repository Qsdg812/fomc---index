import re
sent = (seg + punct).replace("§", ".").strip(' \t\n"\'')
sent = re.sub(r"^\s*[•\-\u2022]\s*", "", sent) # remove leading bullets
if sent:
sents.append(sent)
i += 2
if i < len(parts):
tail = parts[i].replace("§", ".").strip(' \t\n"\'')
if tail:
sents.append(tail)
return sents




def split_minutes_sections(full_text: str) -> Dict[str, list[str]]:
"""Heuristically split minutes into big sections, then sentences per section."""
pattern = "|".join([re.escape(t) for t in SECTION_TITLES])
marked = re.sub(f"({pattern})", r"\n@@SECTION@@ \1\n", full_text, flags=re.I)
chunks = [c.strip() for c in marked.split("@@SECTION@@") if c.strip()]
sections: Dict[str, list[str]] = {}
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




def preprocess_text_files(text_paths: List[str]) -> list[dict]:
"""
Return rows: [{date, doc_type, section, sentence}]
- If filename hints a minutes section file you prepared, keep its section = stem prefix.
- Otherwise, try heuristic section split for minutes PDFs; statements are single section "Statement".
"""
rows: list[dict] = []
for tp in text_paths:
p = Path(tp)
name = p.stem # e.g., 2024-01-31_abcd1234
date_part = name.split("_")[0]
text = p.read_text(encoding="utf-8", errors="ignore")
lower_name = p.name.lower()
if "minutes" in lower_name or "rmpstc" in lower_name or "seo" in lower_name:
# treat as minutes; try to infer section from filename like FOMC_SEO_YYYY...
if "fomc_" in lower_name and "_" in lower_name:
# section tag between first and second underscore
try:
sec_tag = lower_name.split("_")[1].upper()
except Exception:
sec_tag = "Minutes"
sentences = split_sentences(text)
for s in sentences:
rows.append({
"date": date_part, "doc_type": "minutes", "section": sec_tag, "sentence": s
})
else:
# one big minutes text → split by sections heuristically
for sec_title, sents in split_minutes_sections(text).items():
for s in sents:
rows.append({
"date": date_part, "doc_type": "minutes", "section": sec_title, "sentence": s
})
else:
# statement: one big block → sentences
for s in split_sentences(text):
rows.append({
"date": date_part, "doc_type": "statement", "section": "Statement", "sentence": s
})
return rows
