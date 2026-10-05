"""Read the rendered report PDF and write report/page_numbers.json (page of every heading, figure and table).

Body pages are numbered from 1 at 'Chapter 1 Introduction'; the front matter uses the roman numeral printed in the footer.
Usage: python report/find_pages.py [pdf]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parent
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT / "Skin_Disease_Detection_Mini_Project_Report.pdf"
POPPLER = Path(r"C:\poppler\Library\bin")


def run(*args):
    return subprocess.run([str(POPPLER / args[0]), *args[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout


info = run("pdfinfo.exe", str(PDF))
n_pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
texts = [run("pdftotext.exe", "-f", str(i), "-l", str(i), "-layout", str(PDF), "-") for i in range(1, n_pages + 1)]
lines = [[ln.strip() for ln in t.splitlines() if ln.strip()] for t in texts]

body_start = next(i for i, ls in enumerate(lines) if "Chapter 1 Introduction" in ls)  # 0-based pdf page index
print("body starts on pdf page", body_start + 1)


def body_page(pattern, start=body_start, anywhere=False):
    rx = re.compile(pattern)
    for i in range(start, n_pages):
        if any((rx.search(ln) if anywhere else rx.match(ln)) for ln in lines[i]):
            return i - body_start + 1
    return None


def roman_of(i):
    for ln in reversed(lines[i]):
        if re.fullmatch(r"[ivxlc]+", ln):
            return ln
    return None


pages = {}
# front matter (search only between the contents table and the body)
for key in ("Abstract", "List of Figures", "List of Tables"):
    for i in range(3, body_start):
        if key in lines[i] and roman_of(i):
            pages[key] = roman_of(i)
            break

headings = {
    "1": r"Chapter 1 Introduction$", "1.1": r"1\.1\s+Introduction$", "1.2": r"1\.2\s+Problem Definition$",
    "1.3": r"1\.3\s+Objectives$", "1.4": r"1\.4\s+Dataset$",
    "2": r"Chapter 2 Methodology$", "2.1": r"2\.1\s+Related Work$", "2.2": r"2\.2\s+System Architecture",
    "2.3": r"2\.3\s+Techniques",
    "3": r"Chapter 3 Implementation Details$", "3.1": r"3\.1\s+Tools Used$", "3.2": r"3\.2\s+Sample Code",
    "4": r"Chapter 4 Conclusion$", "4.1": r"4\.1\s+Results and Discussion$", "4.2": r"4\.2\s+Conclusion",
    "References": r"References$", "Acknowledgement": r"Acknowledgement$",
}
for key, pattern in headings.items():
    pages[key] = body_page(pattern)

labels = json.loads((REPORT / "labels.json").read_text(encoding="utf-8"))
for label, _ in labels["figures"]:
    pages[label] = body_page(r"%s:" % re.escape(label), anywhere=True)
for label, _ in labels["tables"]:
    pages[label] = body_page(r"%s:" % re.escape(label), anywhere=True)

missing = [k for k, v in pages.items() if v is None]
(REPORT / "page_numbers.json").write_text(json.dumps(pages, indent=1), encoding="utf-8")
print(json.dumps(pages))
print("missing:", missing)
