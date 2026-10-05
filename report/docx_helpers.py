"""Small helpers on top of python-docx for building the report body in the style of the college template."""
import copy
import re

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt

BODY_PT = 12
TEXT_WIDTH_IN = 7.0  # A4 body section: 11920 - 1000 - 840 twips


def set_run_font(run, size=BODY_PT, bold=None, italic=None, name=None, highlight=False, color=None):
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if name:
        run.font.name = name
        rpr = run._r.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.insert(0, fonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(attr), name)
    if highlight:
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if color:
        from docx.shared import RGBColor
        run.font.color.rgb = RGBColor.from_string(color)


_TOKEN = re.compile(r"(\*\*.+?\*\*|__.+?__|\[\[.+?\]\])")


def add_rich(par, text, size=BODY_PT, bold=False, italic=False, name=None):
    """**bold**, __italic__ and [[highlighted placeholder]] inline markup."""
    for part in _TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            run = par.add_run(part[2:-2])
            set_run_font(run, size, True, italic, name)
        elif part.startswith("__"):
            run = par.add_run(part[2:-2])
            set_run_font(run, size, bold, True, name)
        elif part.startswith("[["):
            run = par.add_run(part[2:-2])
            set_run_font(run, size, bold, italic, name, highlight=True)
        else:
            run = par.add_run(part)
            set_run_font(run, size, bold, italic, name)


def fmt(par, align=None, before=0, after=6, line=None, keep_next=False, keep_together=False,
        left=None, right=None, first=None, page_break_before=False):
    pf = par.paragraph_format
    if align is not None:
        par.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if line:
        pf.line_spacing = line
    pf.keep_with_next = keep_next
    pf.keep_together = keep_together
    pf.widow_control = True  # the template turns widow/orphan control off
    pf.page_break_before = page_break_before
    if left is not None:
        pf.left_indent = Inches(left)
    if right is not None:
        pf.right_indent = Inches(right)
    if first is not None:
        pf.first_line_indent = Inches(first)
    return par


def set_cell_shading(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    for old in tcpr.findall(qn("w:shd")):
        tcpr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def set_table_borders(table, color="808080", size=4):
    tblpr = table._tbl.tblPr
    for old in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(old)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        + "".join(f'<w:{edge} w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>'
                  for edge in ("top", "left", "bottom", "right", "insideH", "insideV"))
        + "</w:tblBorders>")
    tblpr.append(borders)


def set_cell_margins(table, top=40, bottom=40, left=80, right=80):
    tblpr = table._tbl.tblPr
    for old in tblpr.findall(qn("w:tblCellMar")):
        tblpr.remove(old)
    tblpr.append(parse_xml(
        f'<w:tblCellMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tblCellMar>'))


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def fix_table_layout(table, widths_in):
    table.autofit = False
    tblpr = table._tbl.tblPr
    for old in tblpr.findall(qn("w:tblLayout")):
        tblpr.remove(old)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    total = sum(widths_in)
    for old in tblpr.findall(qn("w:tblW")):
        tblpr.remove(old)
    tblw = OxmlElement("w:tblW")
    tblw.set(qn("w:w"), str(int(total * 1440)))
    tblw.set(qn("w:type"), "dxa")
    tblpr.append(tblw)
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_in):
        gc.set(qn("w:w"), str(int(w * 1440)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_in):
            cell.width = Inches(w)


def make_table(doc, headers, rows, widths_in, font_pt=10, align_cols=None, shade_rows=None, bold_rows=None):
    """Borderless-by-default python-docx table with grey header row, fixed layout, repeating header."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    set_cell_margins(table)
    align_cols = align_cols or ["l"] * len(headers)
    amap = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}
    shade_rows = shade_rows or set()
    bold_rows = bold_rows or set()

    def fill(cell, text, bold, a):
        par = cell.paragraphs[0]
        par.alignment = amap[a]
        fmt(par, before=0, after=0, line=1.0)
        add_rich(par, str(text), size=font_pt, bold=bold)

    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        fill(cell, h, True, "c" if align_cols[j] != "l" else "l")
        set_cell_shading(cell, "DCE6E3")
    repeat_header(table.rows[0])
    for i, row in enumerate(rows, start=1):
        no_split(table.rows[i])
        for j, val in enumerate(row):
            cell = table.rows[i].cells[j]
            fill(cell, val, (i - 1) in bold_rows, align_cols[j])
            if (i - 1) in shade_rows:
                set_cell_shading(cell, "EEF4F2")
    fix_table_layout(table, widths_in)
    reorder_tblpr(table)
    # keep the whole table on one page: every row except the last stays with the next one
    for row in table.rows[:-1]:
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.keep_with_next = True
    return table


_TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
                "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook"]


def reorder_tblpr(table):
    """Put the children of w:tblPr into the order the schema requires."""
    tblpr = table._tbl.tblPr
    children = list(tblpr)
    key = lambda el: _TBLPR_ORDER.index(el.tag.split("}")[1]) if el.tag.split("}")[1] in _TBLPR_ORDER else 99
    for el in children:
        tblpr.remove(el)
    for el in sorted(children, key=key):
        tblpr.append(el)


def add_bullet_numbering(doc):
    """Create a bullet list definition in numbering.xml and return its numId."""
    numbering = doc.part.numbering_part.element
    abstract_id, num_id = 90, 90
    abstract = parse_xml(
        f'<w:abstractNum {nsdecls("w")} w:abstractNumId="{abstract_id}">'
        '<w:multiLevelType w:val="hybridMultilevel"/>'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/>'
        '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/></w:rPr></w:lvl>'
        '</w:abstractNum>')
    first_num = numbering.find(qn("w:num"))
    if first_num is not None:
        first_num.addprevious(abstract)
    else:
        numbering.append(abstract)
    numbering.append(parse_xml(
        f'<w:num {nsdecls("w")} w:numId="{num_id}"><w:abstractNumId w:val="{abstract_id}"/></w:num>'))
    return num_id


def set_numbering(par, num_id):
    ppr = par._p.get_or_add_pPr()
    numpr = parse_xml(f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr>')
    ppr.append(numpr)


def shade_paragraph(par, fill="F1F3F1"):
    ppr = par._p.get_or_add_pPr()
    ppr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill}"/>'))


def clone_row_with_text(table, template_row_idx, texts, size_half_points=24):
    """Append a copy of a template row and put the given texts into its cells."""
    new_tr = copy.deepcopy(table.rows[template_row_idx]._tr)
    table._tbl.append(new_tr)
    row = table.rows[-1]
    for cell, text in zip(row.cells, texts):
        par = cell.paragraphs[0]
        for r in list(par.runs):
            r._r.getparent().remove(r._r)
        run = par.add_run(text)
        run.font.size = Pt(size_half_points / 2)
    return row
