#!/usr/bin/env python3
"""Convert SRS.md and FINAL_REPORT.md to Word (.docx) with pandoc, then style tables.
Usage: python3 docs/build_docx.py   (after build_docs.py)"""
import os, re, subprocess, tempfile
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
WIDTH = {"02_components": "3.9in", "09_seq_background": "6.4in", "10_seq_ctrlc": "6.2in", "11_seq_error": "6.4in", "12_trust_boundaries": "6.4in", "05_use_case": "5.8in", "04_execution_flow": "4.6in", "08_error_flow": "5.2in", "03_lifecycle_flow": "5.0in",
         "01_architecture": "5.8in", "06_sequence": "6.4in", "05_use_case": "6.4in"}

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    tcPr.append(shd)

def build(md, out, toc=True):
    text = open(os.path.join(HERE, md)).read()
    def add_w(m):
        name = os.path.splitext(os.path.basename(m.group(2)))[0]
        return f"![{m.group(1)}]({m.group(2)}){{width={WIDTH.get(name,'6.2in')}}}"
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", add_w, text)
    tmp = os.path.join(HERE, "_tmp_" + md)
    open(tmp, "w").write(text)
    cmd = ["pandoc", tmp, "-f", "markdown+pipe_tables+yaml_metadata_block", "-o", os.path.join(HERE, out),
           "--resource-path", HERE]
    if toc: cmd += ["--toc", "--toc-depth=2"]
    subprocess.check_call(cmd); os.remove(tmp)
    doc = Document(os.path.join(HERE, out))
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(0.8); s.top_margin = s.bottom_margin = Inches(0.8)
    for t in doc.tables:
        t.style = "Table Grid" if "Table Grid" in [s.name for s in doc.styles] else t.style
        ncol = len(t.columns)
        size = 7.5 if ncol >= 7 else (8.5 if ncol >= 5 else 9.5)
        for ri, row in enumerate(t.rows):
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
                    for r in p.runs:
                        r.font.size = Pt(size)
                        if ri == 0: r.font.bold = True
                if ri == 0: shade(c, "D9E2F3")
        # borders (pandoc tables have none by default)
        tblPr = t._tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for b in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{b}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "808080"); borders.append(e)
        tblPr.append(borders)
    doc.save(os.path.join(HERE, out))
    print("wrote", out)

build("SRS.md", "SRS.docx")
build("FINAL_REPORT.md", "FINAL_REPORT.docx")
build("STP.md", "STP.docx")
build("SAD.md", "SAD.docx")
