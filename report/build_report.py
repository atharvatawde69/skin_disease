"""Build the DL lab mini-project report from the college template.

Usage:  python report/build_report.py
Reads   DL Lab Mini project report template.docx (project root), report/figures/*.png,
        report/page_numbers.json (optional, written by report/find_pages.py)
Writes  report/Skin_Disease_Detection_Mini_Project_Report.docx
Yellow-highlighted text marks placeholders to fill in by hand (student names, IDs, SDG).
"""
import ast
import copy
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, Twips

import docx_helpers as H  # noqa: E402  (run from the report/ folder or with it on sys.path)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
FIG = REPORT / "figures"
TEMPLATE = ROOT / "DL Lab Mini project report template.docx"
OUT = REPORT / "Skin_Disease_Detection_Mini_Project_Report.docx"
PAGES_JSON = REPORT / "page_numbers.json"
PAGES = json.loads(PAGES_JSON.read_text(encoding="utf-8")) if PAGES_JSON.exists() else {}

TITLE = "Skin Disease Detection using Deep Learning: Lesion Classification with ResNet Transfer Learning and Grad-CAM"
J = WD_ALIGN_PARAGRAPH.JUSTIFY
C = WD_ALIGN_PARAGRAPH.CENTER

doc = Document(str(TEMPLATE))
BULLET = H.add_bullet_numbering(doc)

# ------------------------------------------------------------------ registries (auto numbering)
refs_order = []
REFS = {
    "esteva": 'A. Esteva, B. Kuprel, R. A. Novoa, J. Ko, S. M. Swetter, H. M. Blau and S. Thrun, "Dermatologist-level '
              'classification of skin cancer with deep neural networks," Nature, vol. 542, no. 7639, pp. 115-118, 2017.',
    "tschandl": 'P. Tschandl, C. Rosendahl and H. Kittler, "The HAM10000 dataset, a large collection of multi-source '
                'dermatoscopic images of common pigmented skin lesions," Scientific Data, vol. 5, Art. no. 180161, 2018.',
    "kaggle": 'K. S. Mader, "Skin Cancer MNIST: HAM10000," Kaggle dataset. [Online]. Available: '
              'https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000 (accessed Oct. 5, 2026).',
    "codella": 'N. Codella et al., "Skin lesion analysis toward melanoma detection 2018: A challenge hosted by the '
               'International Skin Imaging Collaboration (ISIC)," arXiv:1902.03368, 2019.',
    "he": 'K. He, X. Zhang, S. Ren and J. Sun, "Deep residual learning for image recognition," in Proc. IEEE Conf. '
          'Computer Vision and Pattern Recognition (CVPR), 2016, pp. 770-778.',
    "deng": 'J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li and L. Fei-Fei, "ImageNet: A large-scale hierarchical image '
            'database," in Proc. IEEE CVPR, 2009, pp. 248-255.',
    "selvaraju": 'R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh and D. Batra, "Grad-CAM: Visual '
                 'explanations from deep networks via gradient-based localization," in Proc. IEEE Int. Conf. Computer '
                 'Vision (ICCV), 2017, pp. 618-626.',
    "ioffe": 'S. Ioffe and C. Szegedy, "Batch normalization: Accelerating deep network training by reducing internal '
             'covariate shift," in Proc. Int. Conf. Machine Learning (ICML), 2015, pp. 448-456.',
    "srivastava": 'N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov, "Dropout: A simple way to '
                  'prevent neural networks from overfitting," J. Mach. Learn. Res., vol. 15, no. 56, pp. 1929-1958, 2014.',
    "kingma": 'D. P. Kingma and J. Ba, "Adam: A method for stochastic optimization," in Proc. Int. Conf. Learning '
              'Representations (ICLR), 2015 (arXiv:1412.6980).',
    "tieleman": 'T. Tieleman and G. Hinton, "Lecture 6.5 - RMSProp: Divide the gradient by a running average of its '
                'recent magnitude," COURSERA: Neural Networks for Machine Learning, 2012.',
    "loshchilov": 'I. Loshchilov and F. Hutter, "SGDR: Stochastic gradient descent with warm restarts," in Proc. ICLR, '
                  '2017 (arXiv:1608.03983).',
    "micikevicius": 'P. Micikevicius et al., "Mixed precision training," in Proc. ICLR, 2018 (arXiv:1710.03740).',
    "paszke": 'A. Paszke et al., "PyTorch: An imperative style, high-performance deep learning library," in Advances in '
              'Neural Information Processing Systems 32 (NeurIPS), 2019.',
    "pedregosa": 'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Mach. Learn. Res., vol. 12, '
                 'pp. 2825-2830, 2011.',
    "goodfellow": 'I. Goodfellow, Y. Bengio and A. Courville, Deep Learning. Cambridge, MA, USA: MIT Press, 2016.',
}


def cite(*keys):
    nums = []
    for k in keys:
        if k not in refs_order:
            refs_order.append(k)
        nums.append(str(refs_order.index(k) + 1))
    return "[" + ", ".join(nums) + "]"


fig_counts, tab_counts = {}, {}
figures, tables = [], []  # (label, caption) in order of appearance


def next_label(kind, chapter):
    counts = fig_counts if kind == "Fig" else tab_counts
    counts[chapter] = counts.get(chapter, 0) + 1
    return f"{kind} {chapter}.{counts[chapter]}"


# ------------------------------------------------------------------ body builders
def find_par(text, startswith=True):
    for p in doc.paragraphs:
        t = p.text.strip()
        if (t.startswith(text) if startswith else t == text):
            return p
    raise KeyError(text)


def body(text, after=6, align=J, line=1.5, keep_next=False, first=None, keep_together=False):
    p = doc.add_paragraph()
    H.add_rich(p, text)
    return H.fmt(p, align=align, after=after, line=line, keep_next=keep_next, first=first,
                 keep_together=keep_together)


def chapter(title):
    p = doc.add_paragraph(style="Heading 1")
    p.add_run(title)
    return H.fmt(p, align=C, before=0, after=14, page_break_before=True, keep_next=True)


def h2(text):
    p = doc.add_paragraph(style="Heading 2")
    p.paragraph_format.first_line_indent = Inches(0)
    p.paragraph_format.left_indent = Inches(0)
    r = p.add_run(text)
    H.set_run_font(r, 13, True)
    return H.fmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=12, after=6, keep_next=True, left=0, first=0)


def h3(text):
    p = doc.add_paragraph()
    H.add_rich(p, text, bold=True, italic=False)
    return H.fmt(p, before=8, after=4, keep_next=True)


def bullets(items, after=2):
    for i, text in enumerate(items):
        p = doc.add_paragraph()
        H.add_rich(p, text)
        H.set_numbering(p, BULLET)
        H.fmt(p, align=J, after=after if i < len(items) - 1 else 8, line=1.3)


def equation(text, label):
    p = doc.add_paragraph()
    r = p.add_run(text)
    H.set_run_font(r, 12, italic=True, name="Cambria Math")
    r2 = p.add_run(f"        ({label})")
    H.set_run_font(r2, 12)
    return H.fmt(p, align=C, before=2, after=8, line=1.2, keep_together=True)


def figure(chapter_no, filename, caption, width_in=6.2):
    label = next_label("Fig", chapter_no)
    figures.append((label, caption))
    p = doc.add_paragraph()
    p.add_run().add_picture(str(FIG / filename), width=Inches(width_in))
    H.fmt(p, align=C, before=6, after=3, keep_next=True, line=1.0)
    cap = doc.add_paragraph()
    H.add_rich(cap, f"**{label}:** {caption}", size=11)
    H.fmt(cap, align=C, after=12, line=1.0)
    return label


def figure_pair(chapter_no, items, widths_in):
    """Two figures side by side: items = [(filename, caption), ...]; each keeps its own label and caption."""
    labels = []
    for _, cap in items:
        label = next_label("Fig", chapter_no)
        labels.append(label)
        figures.append((label, cap))
    t = doc.add_table(rows=2, cols=len(items))
    t.alignment = H.WD_TABLE_ALIGNMENT.CENTER
    col_w = [w + 0.35 for w in widths_in]
    for j, ((fn, cap), label) in enumerate(zip(items, labels)):
        pic_par = t.rows[0].cells[j].paragraphs[0]
        pic_par.add_run().add_picture(str(FIG / fn), width=Inches(widths_in[j]))
        H.fmt(pic_par, align=C, before=4, after=3, keep_next=True, line=1.0)
        cap_par = t.rows[1].cells[j].paragraphs[0]
        H.add_rich(cap_par, f"**{label}:** {cap}", size=11)
        H.fmt(cap_par, align=C, after=8, line=1.0)
    H.fix_table_layout(t, col_w)
    H.reorder_tblpr(t)
    spacer = doc.add_paragraph()
    H.fmt(spacer, after=6, line=1.0)


def table(chapter_no, caption, headers, rows, widths, font_pt=10, align_cols=None, shade_rows=None, bold_rows=None):
    label = next_label("Table", chapter_no)
    tables.append((label, caption))
    cap = doc.add_paragraph()
    H.add_rich(cap, f"**{label}:** {caption}", size=11)
    H.fmt(cap, align=C, before=6, after=4, keep_next=True, line=1.0)
    t = H.make_table(doc, headers, rows, widths, font_pt, align_cols, shade_rows, bold_rows)
    spacer = doc.add_paragraph()
    H.fmt(spacer, after=8, line=1.0)
    return label


def source_of(path, name):
    """Source text of a top-level function or class from a project file (so the report shows real code)."""
    src = (ROOT / path).read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(src, node)
    raise KeyError(name)


def code(text, size=8):
    lines = text.rstrip("\n").split("\n")
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        r = p.add_run(line if line else " ")
        H.set_run_font(r, size, name="Consolas")
        H.shade_paragraph(p)
        H.fmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, after=0, line=1.0, keep_next=i < len(lines) - 1, left=0.05,
              keep_together=True)
    spacer = doc.add_paragraph()
    H.fmt(spacer, after=6, line=1.0)


# ================================================================== FRONT MATTER
def set_runs(par, text, size=None, bold=None, highlight=False):
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    run = par.add_run(text)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if highlight:
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return run


# cover page
title_par = find_par("Title of your")
set_runs(title_par, TITLE, size=15, bold=True)
title_par.paragraph_format.left_indent = Inches(0.9)
title_par.paragraph_format.right_indent = Inches(0.7)
for p in doc.paragraphs:
    if p.text.strip().startswith("Name of the Student"):
        for r in p.runs:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW

# certificate
cert = find_par("This is to certify")
for r in list(cert.runs):
    r._r.getparent().remove(r._r)
for text, bold in (("This is to certify that the requirements for the Mini project report entitled “", False),
                   (TITLE, True), ("” have been successfully completed by the following students:", False)):
    run = cert.add_run(text)
    run.font.size = Pt(12)
    run.font.bold = bold

hdr = next(p for p in doc.paragraphs if p.text.strip().startswith("Name") and "Roll" in p.text)
idx = list(doc.element.body).index(hdr._p)
placeholders = ["1. Name of the Student1 (Student ID)", "2. Name of the Student2 (Student ID)",
                "3. Name of the Student3 (Student ID)", "4. Name of the Student4 (Student ID)"]
blank_after = []
for el in list(doc.element.body)[idx + 1: idx + 12]:
    if el.tag == qn("w:p"):
        blank_after.append(el)
from docx.text.paragraph import Paragraph  # noqa: E402

for el, text in zip(blank_after[1:5], placeholders):
    p = Paragraph(el, hdr._parent)
    p.paragraph_format.tab_stops.add_tab_stop(Twips(5879))
    r1 = p.add_run(f" {text}")
    r1.font.size = Pt(12)
    r1.font.highlight_color = WD_COLOR_INDEX.YELLOW
    p.add_run().add_tab()
    p.add_run().add_tab()
    r2 = p.add_run("Roll No.")
    r2.font.size = Pt(12)
    r2.font.highlight_color = WD_COLOR_INDEX.YELLOW

# abstract: replace the sample text between the "Abstract" heading and "List of Figures"
abstract_head = find_par("Abstract", startswith=False)
lof_head = find_par("List of Figures", startswith=False)
cur = abstract_head._p.getnext()
while cur is not None and cur is not lof_head._p:
    nxt = cur.getnext()
    cur.getparent().remove(cur)
    cur = nxt

ABSTRACT = [
    "Skin cancer is among the most common cancers worldwide, and the chance of a good outcome is much higher when it is "
    "found early. Examination by a dermatologist is, however, not available to everyone. This project builds a "
    "deep-learning system that classifies dermoscopy images of pigmented skin lesions into the seven diagnostic "
    "categories of the HAM10000 dataset (10,015 images). The data are split by lesion rather than by image, so that no "
    "lesion appears in more than one of the training, validation and test sets, and a class-weighted cross-entropy "
    "loss is used to counter the heavy class imbalance.",
    "A small convolutional network trained from scratch is compared with ResNet-18 trained from scratch and "
    "fine-tuned from ImageNet weights. The effect of four optimizers (SGD, SGD with momentum, Adam and RMSProp), of "
    "regularization (data augmentation, dropout, weight decay and early stopping) and of the loss function is studied "
    "in eleven controlled experiments. Transfer learning raised the test macro-F1 from 0.40 to 0.67. The model selected "
    "on validation macro-F1, ResNet-18 trained with RMSProp, reached 79.2% test accuracy, 69% balanced accuracy and a "
    "macro-F1 of 0.68, yet it found only 59% of the melanomas, which shows why accuracy alone is misleading on "
    "imbalanced medical data. Grad-CAM heatmaps show that the network attends to the lesion itself.",
    "The final model is deployed in a Flask web application that returns class probabilities, a melanoma-probability "
    "meter, a heatmap and plain-language guidance, and that warns the user when the result is uncertain. The system "
    "is an educational tool and not a medical device.",
]
anchor = abstract_head._p
for text in reversed(ABSTRACT):
    p = doc.add_paragraph()
    H.add_rich(p, text)
    H.fmt(p, align=J, after=6, line=1.3)
    anchor.addnext(p._p)
sdg = doc.add_paragraph()
H.add_rich(sdg, "**Sustainable Development Goal mapped:** [[SDG number and name, as in the project PPT]]")
H.fmt(sdg, align=J, before=4, after=6, line=1.3)
abstract_head._p.getnext()  # keep linter quiet
# put the SDG line after the three abstract paragraphs
last_abs = abstract_head._p
for _ in ABSTRACT:
    last_abs = last_abs.getnext()
last_abs.addnext(sdg._p)

# roman numbering of the front matter should start at i on the abstract page (as in the contents table)
for pg in doc.element.body.iter(qn("w:pgNumType")):
    if pg.get(qn("w:start")) == "2":
        pg.set(qn("w:start"), "1")
lof_head.paragraph_format.page_break_before = True

# make the body section start page numbering at 1
sect = doc.sections[-1]._sectPr
if sect.find(qn("w:pgNumType")) is None:
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:start"), "1")
    cols = sect.find(qn("w:cols"))
    cols.addprevious(pg)

# ================================================================== CHAPTER 1
# (the template already contains the heading "Chapter 1 Introduction")
ch1 = find_par("Chapter 1")
ch1.paragraph_format.left_indent = Inches(0)
ch1.paragraph_format.right_indent = Inches(0)
ch1.alignment = C
H.fmt(ch1, align=C, before=0, after=14, keep_next=True)
h2("1.1  Introduction")
body("Skin conditions are among the most common reasons for seeking medical care, and skin cancer is one of the "
     "most frequently diagnosed cancers worldwide. As with most cancers, outcomes are far better when a malignant "
     "lesion is found early " + cite("esteva") + ". Melanoma is the most dangerous form because it can spread to other "
     "organs, while the more common basal cell carcinoma grows slowly and is usually treated locally.")
body("Dermoscopy is a non-invasive technique in which a dermatologist examines a lesion through a magnifying lens "
     "under controlled lighting, which reveals colours and structures beneath the skin surface. Reading these patterns "
     "takes training and experience, and specialists are not equally available everywhere. A computer-aided system "
     "that offers a fast and consistent second opinion could help with triage, which makes the problem a natural "
     "application of deep learning.")
body("Convolutional neural networks (CNNs) learn visual features directly from labelled images, and a well-known study "
     "showed that a CNN could classify skin lesions at a level comparable to dermatologists " + cite("esteva") + ". "
     "This mini project applies the techniques of the Deep Learning course (see, for example, " + cite("goodfellow") + ") to the public HAM10000 dataset "
     + cite("tschandl") + ". It builds a baseline CNN, a ResNet with transfer learning, compares optimizers and "
     "regularization methods, evaluates the models with metrics suited to imbalanced data, explains the predictions "
     "with Grad-CAM, and deploys the best model in a web application.")
body("The report is organised as follows. Chapter 1 defines the problem and describes the dataset. Chapter 2 presents "
     "related work, the system architecture and the techniques used. Chapter 3 lists the tools and shows sample code "
     "and screenshots. Chapter 4 discusses the results and concludes with limitations and future scope.")

h2("1.2  Problem Definition")
body("Given a dermoscopy image **x** of a single pigmented skin lesion, predict its diagnostic category from seven "
     "classes: actinic keratoses and intraepithelial carcinoma (akiec), basal cell carcinoma (bcc), benign "
     "keratosis-like lesions (bkl), dermatofibroma (df), melanoma (mel), melanocytic nevi (nv) and vascular lesions "
     "(vasc). The task is not as simple as maximising accuracy, because of the following difficulties:", after=4)
bullets([
    "**Class imbalance.** Melanocytic nevi make up 67% of the images and dermatofibromas about 1%. A classifier that "
    "always answers “nevus” would be 67% accurate and clinically useless.",
    "**Several photographs per lesion.** HAM10000 contains 10,015 images of only 7,470 lesions. A random split by image "
    "would place near-identical photographs of one lesion in both the training and the test set and inflate the score.",
    "**Unequal cost of errors.** Missing a melanoma is far more serious than a false alarm, so the per-class recall "
    "of melanoma has to be reported separately.",
    "**Limited data.** Ten thousand images are few compared with the millions used to train general vision models.",
    "**Trust and use.** A black-box answer is hard to trust. The system should explain what it looked at, admit "
    "when it is unsure, and be usable by a person who knows nothing about neural networks.",
])
body("The problem addressed in this project is therefore to design, train and fairly evaluate deep-learning models "
     "for seven-class dermoscopy classification under these constraints, and to deploy the best model as an "
     "easy-to-use and honest web application.")

h2("1.3  Objectives")
bullets([
    "To build a leakage-free data pipeline for HAM10000 by splitting the data by lesion into training, validation "
    "and test sets.",
    "To implement a small CNN from scratch as a baseline (syllabus module 4.1).",
    "To apply transfer learning with ResNet-18 and compare it with the same network trained from scratch "
    "(module 4.2).",
    "To compare the SGD, SGD with momentum, Adam and RMSProp optimizers (module 2.2).",
    "To measure the effect of regularization: data augmentation, dropout, weight decay, batch normalization and "
    "early stopping (module 2.3).",
    "To handle class imbalance with a weighted cross-entropy loss and to evaluate with balanced accuracy, macro-F1 and "
    "per-class recall, in particular for melanoma (module 2.1).",
    "To explain individual predictions with Grad-CAM heatmaps.",
    "To deploy the best model in a Flask web application that shows probabilities, a heatmap, plain-language "
    "guidance and warnings about uncertainty.",
])

h2("1.4  Dataset")
body("The experiments use the HAM10000 (“Human Against Machine with 10000 training images”) dataset "
     + cite("tschandl") + ", obtained from its Kaggle mirror " + cite("kaggle") + ". It contains 10,015 dermoscopy "
     "images of pigmented lesions collected over about twenty years at the Medical University of Vienna (Austria) and "
     "in a skin cancer practice in Queensland (Australia). More than half of the diagnoses were confirmed by "
     "histopathology and the rest by follow-up examination, expert consensus or confocal microscopy. The images are "
     "600 × 450 pixel JPEG files, and a metadata table gives, for each image, the lesion identifier, image "
     "identifier, diagnosis, how the diagnosis was confirmed, age, sex and body location. The dataset is released under "
     "a CC BY-NC-SA 4.0 licence, which allows its use for this educational project.")
body("Table 1.1 lists the seven classes. Figure 1.1 shows how unbalanced they are: melanocytic nevi account for about "
     "two thirds of all images, while dermatofibromas and vascular lesions together make up less than 3%.", after=6, keep_next=True)
table(1, "The seven diagnostic classes of HAM10000",
      ["Code", "Diagnosis", "Nature", "Images", "Share (%)"],
      [["nv", "Melanocytic nevi (common moles)", "Benign", "6,705", "66.9"],
       ["mel", "Melanoma", "Malignant", "1,113", "11.1"],
       ["bkl", "Benign keratosis-like lesions", "Benign", "1,099", "11.0"],
       ["bcc", "Basal cell carcinoma", "Malignant", "514", "5.1"],
       ["akiec", "Actinic keratoses / intraepithelial carcinoma", "Pre-cancerous / in situ", "327", "3.3"],
       ["vasc", "Vascular lesions", "Benign", "142", "1.4"],
       ["df", "Dermatofibroma", "Benign", "115", "1.1"],
       ["", "**Total**", "", "**10,015**", "**100**"]],
      [0.7, 3.0, 1.6, 0.8, 0.8], align_cols=["l", "l", "l", "r", "r"])
body("The data were divided by lesion into a training set of 7,054 images (70.4%), a validation set of 1,464 images "
     "(14.6%) and a test set of 1,497 images (14.9%), keeping the class proportions similar in each part. Figure 1.2 "
     "shows the resulting counts per class. The rarest classes have only 22 test images each (dermatofibroma and "
     "vascular lesions), so their per-class scores are noisy: a single image changes the recall by about 4.5 "
     "percentage points.", keep_next=True)
figure_pair(1, [("fig1_1_class_distribution.png", "Images per class in HAM10000 (Kaggle notebook output)."),
                ("fig1_2_split_counts.png", "Images per split and class after the lesion-wise split.")],
            [3.3, 1.95])

# ================================================================== CHAPTER 2
chapter("Chapter 2 Methodology")
h2("2.1  Related Work")
body("Deep learning for skin lesion analysis has developed quickly. Esteva et al. " + cite("esteva") + " fine-tuned an "
     "ImageNet-pretrained Inception network on about 129,000 clinical images and reported dermatologist-level "
     "performance on two classification tasks, which made transfer learning the standard starting point for the "
     "field. The International Skin Imaging Collaboration (ISIC) organises public challenges on lesion "
     "segmentation, attribute detection and diagnosis; the 2018 edition used HAM10000 as the training data of its "
     "diagnosis task " + cite("codella") + ", and the dataset has been widely used since.")
body("Architecturally, the residual networks (ResNet) of He et al. " + cite("he") + " made very deep CNNs trainable by "
     "adding identity shortcut connections, and ResNets pretrained on ImageNet " + cite("deng") + " are a common "
     "backbone for medical images. Training is stabilised by batch normalization " + cite("ioffe") + " and "
     "regularized by dropout " + cite("srivastava") + ". Grad-CAM " + cite("selvaraju") + " produces visual explanations "
     "from any CNN without changing its architecture, which is important when a prediction concerns health. "
     "Table 2.1 summarises the works most relevant to this project.")
table(2, "Summary of related work",
      ["Work", "Contribution", "Use in this project"],
      [["Esteva et al., 2017 " + cite("esteva"), "CNN transfer learning reaches dermatologist-level skin lesion classification.",
        "Motivation for fine-tuning a pretrained network."],
       ["Tschandl et al., 2018 " + cite("tschandl"), "HAM10000: 10,015 dermoscopy images in 7 classes.", "The dataset used here."],
       ["Codella et al., 2019 " + cite("codella"), "ISIC 2018 challenge on lesion segmentation, attributes and diagnosis.",
        "Context and benchmark for the data."],
       ["He et al., 2016 " + cite("he"), "Residual learning with skip connections for very deep networks.", "ResNet-18 backbone."],
       ["Selvaraju et al., 2017 " + cite("selvaraju"), "Grad-CAM: gradient-based visual explanations.", "Heatmaps in the evaluation and in the web app."]],
      [1.9, 2.9, 2.1], font_pt=10)
body("Many published results report accuracy only, or split the data by image. This project differs in emphasis rather "
     "than in novelty: it splits by lesion, reports balanced metrics and melanoma recall, studies the optimizer and "
     "regularization choices in controlled experiments, and delivers the result as a usable and honest application.")

h2("2.2  System Architecture / Block Diagram")
body("Figure 2.1 shows the complete system. It has two pipelines connected by a trained checkpoint. The "
     "__training pipeline__ runs in a Kaggle notebook on a GPU and produces the best model. The __inference pipeline__ "
     "runs in the Flask web application on an ordinary computer and uses that model on images uploaded by the user.")
figure(2, "fig2_1_block_diagram.png", "Block diagram of the system: training pipeline, model selection and web inference.",
       width_in=6.3)
body("The main blocks are:", after=4)
bullets([
    "**Dataset and pre-processing.** Images and metadata are read, resized once to 224 × 224 pixels and normalised "
    "with the ImageNet mean and standard deviation, which the pretrained network expects.",
    "**Lesion-wise split.** All photographs of a lesion are assigned to the same set (70% / 15% / 15%), and the code "
    "asserts that no lesion occurs in two sets.",
    "**Augmentation.** Random flips, rotations, crops and colour changes are applied to training images only.",
    "**Model training.** A CNN or ResNet-18 is trained with a weighted cross-entropy loss, a chosen optimizer, "
    "weight decay, dropout, a cosine learning-rate schedule and early stopping on validation macro-F1.",
    "**Evaluation and selection.** Validation macro-F1 selects the epoch and the final model; the test set is used "
    "only for reporting. Metrics include accuracy, balanced accuracy, macro-F1, per-class recall and the confusion matrix.",
    "**Inference and explanation.** The web application resizes and normalises the uploaded image in memory, runs the "
    "network, computes a Grad-CAM heatmap, applies simple rules for uncertainty warnings and shows the guidance text "
    "for the predicted class.",
])

h2("2.3  Techniques / Algorithm")
h3("2.3.1  Pre-processing and data augmentation")
body("Every image is resized to 224 × 224 pixels (the original 600 × 450 aspect ratio is not preserved) and "
     "its channels are normalised with mean (0.485, 0.456, 0.406) and standard deviation (0.229, 0.224, 0.225). "
     "Resized images are kept in memory so that each epoch is fast. For training, the following random "
     "transformations are applied: resized crop (scale 0.75 to 1.0), horizontal and vertical flips, rotation by up "
     "to 30 degrees, and colour jitter (brightness, contrast and saturation 0.2, hue 0.02). These are valid for "
     "dermoscopy because a lesion has no preferred orientation. Validation and test images are not augmented.")

h3("2.3.2  Lesion-wise split")
body("The procedure is: (1) group the metadata by lesion_id and take the diagnosis of each lesion; (2) split the lesions "
     "(not the images) into train+validation and test sets, stratified by diagnosis; (3) split train+validation again "
     "into training and validation sets; (4) give every image the split of its lesion; (5) verify that the lesion "
     "sets of the three parts are disjoint. A fixed random seed (42) makes the split reproducible.")

h3("2.3.3  Baseline CNN (built from scratch)")
body("The baseline network (Figure 2.2) stacks four blocks, each consisting of a 3 × 3 convolution, batch "
     "normalization, a ReLU activation and 2 × 2 max pooling, with 32, 64, 128 and 256 filters. Global average "
     "pooling reduces the final 256 × 14 × 14 feature map to a 256-dimensional vector, which passes through "
     "dropout (0.5) and a linear layer with seven outputs. It has 390,695 parameters and is trained from random "
     "initialisation.")
figure(2, "fig2_2_cnn_architecture.png", "Architecture of the baseline CNN (BN = batch normalization).", width_in=6.3)

h3("2.3.4  ResNet-18 and transfer learning")
body("ResNet-18 " + cite("he") + " consists of an initial 7 × 7 convolution, max pooling, and four stages of two "
     "__basic residual blocks__ each, followed by global average pooling and a classifier (Figure 2.3). In a residual "
     "block the input is added to the output of two convolutions through a shortcut connection:", after=2)
equation("y = ReLU( F(x, {Wᵢ}) + x )", "2.1")
body("The shortcut lets gradients flow directly to earlier layers, which makes deeper networks easier to optimise. "
     "In transfer learning the network is initialised with weights learned on ImageNet " + cite("deng") + ", which "
     "already encode general edges, textures and shapes, and is then fine-tuned on the skin images. The original "
     "1000-class layer is replaced by dropout (0.3) and a new linear layer from 512 to 7 outputs. The resulting "
     "model has 11,180,103 parameters. For comparison, the same network is also trained from random initialisation.")
figure(2, "fig2_3_resnet18.png", "(a) ResNet-18 with the new classifier head; (b) the basic residual block.", width_in=6.2)

h3("2.3.5  Loss function and class weights")
body("The network outputs seven scores z. The softmax function turns them into probabilities and the cross-entropy "
     "loss penalises a low probability for the true class:", after=2)
equation("pᶜ = exp(zᶜ) / Σⱼ exp(zⱼ)", "2.2")
equation("L = −(1/N) Σᵢ w(yᵢ) · log p(i, yᵢ)", "2.3")
body("To counter the imbalance, each class c receives a weight inversely proportional to its frequency in the training "
     "set, where N is the number of training images, K = 7 the number of classes and nᶜ the images of class c:", after=2)
equation("wᶜ = N / (K · nᶜ)", "2.4")
body("With these weights a mistake on a dermatofibroma counts about 62 times as much as a mistake on a nevus (Table 2.2), "
     "so the model cannot reach a low loss by favouring the majority class. The weights are computed from the "
     "training set only. One ablation experiment uses the plain, unweighted loss.")
table(2, "Class weights computed from the training set (N = 7,054)",
      ["Class", "Training images", "Weight w"],
      [["akiec", "233", "4.33"], ["bcc", "365", "2.76"], ["bkl", "775", "1.30"], ["df", "76", "13.26"],
       ["mel", "777", "1.30"], ["nv", "4,730", "0.21"], ["vasc", "98", "10.28"]],
      [1.5, 1.8, 1.5], align_cols=["l", "r", "r"])

h3("2.3.6  Optimizers")
body("Four optimizers are compared (module 2.2). All minimise the loss by changing the weights θ against the "
     "gradient g of a mini-batch. __SGD__ updates θ ← θ − ηg. __SGD with momentum__ "
     "accumulates a velocity that smooths the direction and speeds up progress in consistent directions:", after=2)
equation("vₜ = μvₜ₋₁ + gₜ ,   θ ← θ − ηvₜ", "2.5")
body("__RMSProp__ " + cite("tieleman") + " divides the step by a running average of recent squared gradients, so that "
     "each weight gets its own effective learning rate:", after=2)
equation("sₜ = ρsₜ₋₁ + (1−ρ)gₜ² ,   θ ← θ − ηgₜ / (√sₜ + ε)", "2.6")
body("__Adam__ " + cite("kingma") + " combines both ideas, keeping running averages of the gradient (first moment m) "
     "and of its square (second moment v) with bias correction:", after=2)
equation("mₜ = β₁mₜ₋₁ + (1−β₁)gₜ ,   vₜ = β₂vₜ₋₁ + (1−β₂)gₜ² ,   "
         "θ ← θ − η m̂ₜ / (√v̂ₜ + ε)", "2.7")
body("The learning rate η depends strongly on the optimizer, so each one received its own value (Table 2.3).")

h3("2.3.7  Regularization")
body("Regularization (module 2.3) reduces overfitting, which is a particular risk with 7,000 training images. Five "
     "techniques are used. __Data augmentation__ shows the network a different version of each image every epoch. "
     "__Dropout__ " + cite("srivastava") + " randomly switches off neurons during training. __Weight decay__ adds an L2 "
     "penalty on the weights, L_total = L + (λ/2)‖θ‖², which keeps them small. __Batch "
     "normalization__ " + cite("ioffe") + " normalises activations inside the network and has a mild regularizing "
     "effect. __Early stopping__ ends training when the validation score has not improved for five epochs and "
     "restores the best epoch.")

h3("2.3.8  Training configuration")
body("All experiments share the settings in Table 2.3. The learning rate follows a cosine schedule " + cite("loshchilov")
     + " that decays smoothly to zero, and training on the GPU uses mixed precision " + cite("micikevicius")
     + " for speed. The random seed is fixed so that runs are repeatable.", after=6, keep_next=True)
table(2, "Training configuration",
      ["Setting", "Value"],
      [["Input", "224 × 224 RGB, ImageNet mean and standard deviation"],
       ["Batch size / epochs", "64 / at most 15"],
       ["Early stopping", "patience of 5 epochs on validation macro-F1; best epoch restored"],
       ["Learning-rate schedule", "cosine annealing to zero over 15 epochs"],
       ["Loss", "weighted cross-entropy (plain cross-entropy in one ablation)"],
       ["Learning rates", "Adam 3×10⁻⁴; RMSProp 1×10⁻⁴; SGD and SGD with momentum (0.9) 1×10⁻²; "
                          "models trained from scratch (Adam) 1×10⁻³"],
       ["Weight decay (L2)", "1×10⁻⁴ (0 in the ablations)"],
       ["Dropout", "0.3 before the ResNet classifier, 0.5 in the CNN (0 in the ablation)"],
       ["Augmentation", "resized crop, flips, rotation ±30°, colour jitter (off in the ablations)"],
       ["Precision", "mixed precision (FP16 autocast with gradient scaling) on the GPU"],
       ["Random seed", "42"],
       ["Hardware", "one NVIDIA Tesla T4 GPU on Kaggle, two data-loading workers"]],
      [1.9, 5.0], align_cols=["l", "l"])

h3("2.3.9  Evaluation metrics")
body("Because of the imbalance, accuracy alone is not used to judge the models. For each class c, precision is "
     "Pᶜ = TP/(TP+FP), recall is Rᶜ = TP/(TP+FN) and the F1-score is their harmonic mean:", after=2)
equation("F1ᶜ = 2PᶜRᶜ / (Pᶜ + Rᶜ)", "2.8")
equation("Macro-F1 = (1/K) Σᶜ F1ᶜ ,    Balanced accuracy = (1/K) Σᶜ Rᶜ", "2.9")
body("__Macro-F1__ and __balanced accuracy__ average over classes with equal weight, so rare classes count as much "
     "as the common nevus class. The __recall of melanoma__ (the share of real melanomas that are found) is reported "
     "separately because a missed melanoma is the costliest error. The __confusion matrix__ shows which classes are "
     "mistaken for which. Validation macro-F1 is used to choose epochs and models; the test set is used only to "
     "report the final numbers.")

h3("2.3.10  Grad-CAM")
body("Grad-CAM " + cite("selvaraju") + " shows which regions of an image most increased the score of a class. For the "
     "last convolutional layer with feature maps Aᵏ, the importance of each map is the average gradient of the "
     "class score yᶜ with respect to that map, and the heatmap is the positive part of the weighted sum of maps:",
     after=2)
equation("αᵏ = (1/Z) Σᵢ Σⱼ ∂yᶜ/∂Aᵏᵢⱼ ,    L = ReLU( Σᵏ αᵏ Aᵏ )", "2.10")
body("The result is resized to the image and shown as a colour overlay (red means a strong influence). In this project "
     "the last residual block of ResNet-18 is used.")

h3("2.3.11  Experimental design")
body("Table 2.4 lists the eleven runs. All ablations change one factor of the reference configuration "
     "(ResNet-18 pretrained, Adam, augmentation, dropout 0.3, weight decay 10⁻⁴, weighted loss), which is "
     "the run called resnet18_main.", after=6, keep_next=True, keep_together=True)
table(2, "Experiments and the factor each one varies",
      ["No.", "Runs", "Factor studied", "Module"],
      [["E1", "cnn_scratch", "Baseline CNN trained from scratch", "4.1"],
       ["E2", "resnet18_scratch, resnet18_main", "Random versus ImageNet initialisation", "4.2"],
       ["E3", "resnet18_main (Adam), opt_sgd, opt_momentum, opt_rmsprop", "Optimizer", "2.2"],
       ["E4", "reg_no_augment, reg_no_dropout, reg_no_weight_decay, reg_none", "Regularization", "2.3"],
       ["E5", "loss_unweighted", "Weighted versus plain cross-entropy", "2.1"]],
      [0.5, 3.4, 2.4, 0.6], font_pt=10, align_cols=["l", "l", "l", "c"])

# ================================================================== CHAPTER 3
chapter("Chapter 3 Implementation Details")
h2("3.1  Tools Used")
body("The project was written in Python. Training was run in a Kaggle notebook on an NVIDIA Tesla T4 GPU; the "
     "complete set of eleven experiments took 4,279 seconds (about 71 minutes). The web application runs on an "
     "ordinary computer without a GPU. Table 3.1 lists the tools.", after=6, keep_next=True)
table(3, "Tools and libraries",
      ["Tool", "Details", "Purpose"],
      [["Python 3", "Kaggle notebook and local virtual environment", "Programming language"],
       ["PyTorch " + cite("paszke"), "2.11 (CUDA 12.8) on Kaggle; 2.14 (CPU) locally", "Models, training, Grad-CAM"],
       ["torchvision", "ImageNet-pretrained ResNet-18, image transforms", "Transfer learning, augmentation"],
       ["scikit-learn " + cite("pedregosa"), "Stratified split, metrics", "Evaluation"],
       ["pandas, NumPy", "Metadata and array handling", "Data pipeline"],
       ["Matplotlib, Pillow", "Plots, colour maps, image input/output", "Figures and heatmaps"],
       ["Flask", "3.1", "Web application"],
       ["Kaggle Notebooks", "NVIDIA Tesla T4 GPU, internet access for weights", "Training environment"],
       ["Git and GitHub", "Public repository", "Version control"]],
      [1.6, 3.3, 2.0], font_pt=10)
body("The source code is organised as a small package so that the notebook, the tests and the web application all "
     "use the same functions:", after=4, keep_next=True)
code("""skin_disease/
  src/
    labels.py      class codes, names, normalisation constants
    data.py        metadata loading, lesion-wise split, cached Dataset, augmentation
    models.py      SimpleCNN, ResNet builder, Grad-CAM target layer
    train.py       configuration, optimizers, training loop with early stopping
    evaluate.py    predictions, metrics, confusion-matrix and curve plots
    gradcam.py     Grad-CAM and heatmap rendering
    knowledge.py   plain-language guidance for each class
  notebooks/train.ipynb   all experiments, runs on Kaggle or Colab
  app.py, templates/, static/   Flask web application
  models/best.pt, model_card.json   trained model and its metrics
  tests/test_smoke.py     end-to-end test on small fake data""", size=8.5)

h2("3.2  Sample Code & Screenshots")
h3("3.2.1  Lesion-wise split")
body("The function below assigns every image the split of its lesion and asserts that no lesion appears in two sets.",
     after=4, keep_next=True)
code(source_of("src/data.py", "split_by_lesion"), size=7.5)
h3("3.2.2  Model definitions")
body("The baseline CNN and the function that adapts a ResNet to seven classes:", after=4, keep_next=True)
code(source_of("src/models.py", "SimpleCNN"), size=7.5)
code(source_of("src/models.py", "build_resnet"), size=7.5)
h3("3.2.3  Training loop (abridged)")
body("The core of the training function: a mixed-precision training step, validation macro-F1 after every epoch, "
     "checkpointing of the best epoch and early stopping.", after=4, keep_next=True)
code("""for epoch in range(1, cfg.epochs + 1):
    model.train()
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast(device_type=device.type, enabled=use_amp):
            out = model(x)
            loss = criterion(out, y)              # weighted cross-entropy
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    if scheduler:
        scheduler.step()                          # cosine learning-rate schedule

    val = predict(model, val_loader, device, criterion)
    val_f1 = f1_score(val["y_true"], val["y_pred"], average="macro")
    if val_f1 > best_f1:                          # keep the best epoch
        best_f1, best_epoch, wait = val_f1, epoch, 0
        torch.save({"model": model.state_dict(), "cfg": asdict(cfg), ...}, ckpt_path)
    else:
        wait += 1
    if wait >= cfg.patience:                      # early stopping
        break""", size=7.5)
h3("3.2.4  Grad-CAM")
body("Grad-CAM is implemented with a forward hook on the last residual block, which stores the feature maps and "
     "the gradients flowing back into them:", after=4, keep_next=True)
code(source_of("src/gradcam.py", "GradCAM"), size=7.5)

h3("3.2.5  Web application")
body("The Flask application loads the saved checkpoint once and serves a single page. Images are read from the upload, "
     "processed in memory and never written to disk; files larger than 10 MB or that are not images are rejected "
     "with a clear message. Figure 3.1 shows the upload screen and Figure 3.2 the result for a sample image. "
     "Besides the top three classes, the result page shows:", after=4)
bullets([
    "a separate **melanoma-probability meter**, always visible;",
    "a **Grad-CAM heatmap** with a slider to fade it over the original image;",
    "**warnings** when the confidence is below 50%, when the top two classes are within 15 percentage points, or "
    "when the melanoma probability is at least 15% although another class ranked first;",
    "a reminder that a result other than melanoma is **not a clearance**, quoting the melanoma recall measured on "
    "the test set;",
    "a **risk badge** that is never reassuring when the result is uncertain;",
    "a plain-language **guidance card** (what the lesion type is, what it often looks like, suggested next steps), "
    "the ABCDE rule for checking moles, a panel with the model's measured performance and limitations, and a "
    "print-friendly summary.",
])
figure(3, "fig3_2_app_upload.png", "Upload screen of the web application.", width_in=5.4)
figure(3, "fig3_3_app_result.png", "Result page for a sample melanoma image: prediction, confidence, melanoma meter, "
       "Grad-CAM heatmap and guidance.", width_in=6.2)

# ================================================================== CHAPTER 4
chapter("Chapter 4 Conclusion")
h2("4.1  Results and Discussion")
body("All eleven runs were evaluated on the same lesion-wise test set of 1,497 images. Table 4.1 gives the best "
     "epoch chosen by early stopping, the validation macro-F1 used for model selection, and the test metrics. The "
     "selected model is shaded.", after=6, keep_next=True)
RES = [
    ["cnn_scratch", "CNN from scratch, Adam 10⁻³, dropout 0.5", 11, 0.3733, 0.5438, 0.4747, 0.3774, 0.6071],
    ["resnet18_scratch", "ResNet-18, random initialisation, Adam 10⁻³", 13, 0.4236, 0.5865, 0.5050, 0.4021, 0.5893],
    ["resnet18_main", "Reference: ResNet-18 pretrained, Adam 3×10⁻⁴", 13, 0.6748, 0.7455, 0.7216, 0.6723, 0.7143],
    ["opt_sgd", "Reference with SGD, 10⁻²", 15, 0.6130, 0.7308, 0.6998, 0.6388, 0.7381],
    ["opt_momentum", "Reference with SGD + momentum 0.9, 10⁻²", 2, 0.3806, 0.6092, 0.4744, 0.3479, 0.5179],
    ["opt_rmsprop", "Reference with RMSProp, 10⁻⁴", 9, 0.6909, 0.7916, 0.6925, 0.6815, 0.5893],
    ["reg_no_augment", "Reference without augmentation", 9, 0.6892, 0.8103, 0.6500, 0.6665, 0.6488],
    ["reg_no_dropout", "Reference without dropout", 12, 0.6592, 0.7629, 0.7344, 0.6808, 0.6964],
    ["reg_no_weight_decay", "Reference without weight decay", 12, 0.6841, 0.7495, 0.7096, 0.6670, 0.7262],
    ["reg_none", "No augmentation, dropout or weight decay", 9, 0.6843, 0.8203, 0.6475, 0.6740, 0.5238],
    ["loss_unweighted", "Reference with plain cross-entropy", 15, 0.6887, 0.8257, 0.6225, 0.6692, 0.6071],
]
rows = [[r[0], r[1], str(r[2])] + [f"{v:.4f}" for v in r[3:]] for r in RES]
table(4, "Results of all experiments (test metrics at the epoch with the best validation macro-F1)",
      ["Run", "Setup", "Best epoch", "Val macro-F1", "Test accuracy", "Balanced accuracy", "Test macro-F1", "Melanoma recall"],
      rows, [1.25, 1.85, 0.5, 0.65, 0.65, 0.7, 0.65, 0.7], font_pt=8, align_cols=["l", "l", "c", "c", "c", "c", "c", "c"],
      shade_rows={5})

h3("4.1.1  Effect of architecture and pretraining")
body("The small CNN reached a test macro-F1 of 0.377 and a balanced accuracy of 0.475. ResNet-18 trained from the same "
     "random start improved on this only slightly (0.402 and 0.505), which shows that a deeper network alone does not "
     "help when only about 7,000 training images are available. Starting from ImageNet weights changed the picture: "
     "macro-F1 rose to 0.672 and balanced accuracy to 0.722, a gain of about 27 and 22 percentage points over the "
     "from-scratch ResNet. Pretrained filters for edges, textures and colours transfer well to dermoscopy, so transfer "
     "learning is the most influential single decision in this study (Figure 4.1).")
figure(4, "fig4_1_models_comparison.png", "Training loss, validation loss and validation macro-F1 of the CNN, the "
       "ResNet-18 trained from scratch and the pretrained ResNet-18.", width_in=6.6)

h3("4.1.2  Effect of the optimizer")
body("Adam (macro-F1 0.672), RMSProp (0.682) and plain SGD (0.639) all produced usable models with the pretrained "
     "network, and RMSProp obtained the best validation score. SGD improved until the last epoch (best epoch 15), so "
     "it had not converged within the 15-epoch budget and would probably have gained from more epochs or a higher "
     "learning rate. SGD with momentum failed in this experiment: its best validation F1 of 0.381 occurred in the "
     "second epoch and training was stopped early. A learning rate of 0.01 combined with a momentum of 0.9 is "
     "effectively about ten times larger than plain SGD at the same rate, which was evidently too aggressive for "
     "fine-tuning. This result reflects an untuned learning rate and is not a verdict against momentum; each optimizer "
     "received only one learning rate (Figure 4.2).")
figure(4, "fig4_2_optimizers.png", "Training curves for different optimizers (resnet18_main uses Adam).", width_in=6.6)

h3("4.1.3  Effect of regularization")
body("Removing data augmentation raised the test accuracy from 74.6% to 81.0%, but lowered balanced accuracy from "
     "0.722 to 0.650 and melanoma recall from 0.714 to 0.649. Without augmentation the network fits the training "
     "images more closely and leans towards the dominant nevus class, which gains accuracy and loses the rare classes. "
     "Removing all three regularizers gave a melanoma recall of only 0.524, lower than every other pretrained run "
     "except the failed momentum run. Dropout and "
     "weight decay, on the other hand, had no clear effect: the runs without them differ from the reference by about one "
     "percentage point in macro-F1, which is within the run-to-run noise. A plausible explanation is that fine-tuning "
     "a pretrained network for few epochs with early stopping and a decaying learning rate is already strongly "
     "regularized. Augmentation was therefore the most useful regularizer here (Figure 4.3). It also dominated the "
     "training time: runs with augmentation took about 7 minutes and those without about 3 minutes, because the "
     "image transformations ran on only two CPU workers.")
figure(4, "fig4_3_regularization.png", "Training curves of the regularization ablation.", width_in=6.6)

h3("4.1.4  Effect of the loss function")
body("The run with the plain cross-entropy loss had the highest accuracy of all (82.6%) but a balanced accuracy of "
     "only 0.623, compared with 0.722 for the weighted loss, and a melanoma recall of 0.607 compared with 0.714. Its "
     "macro-F1 was almost unchanged (0.669 against 0.672), because higher precision offset lower recall. The class "
     "weights therefore shift the model towards recall on the rare classes, which is the desired behaviour for "
     "screening, at a cost in accuracy (Figure 4.4). This is the clearest demonstration in the study that accuracy "
     "alone is a misleading measure on this dataset.")
figure(4, "fig4_4_loss.png", "Training curves for weighted versus plain cross-entropy.", width_in=6.6)

h3("4.1.5  The selected model")
body("The final model was chosen by a rule fixed in advance: the ResNet run with the highest validation macro-F1. This "
     "was opt_rmsprop (validation macro-F1 0.691). On the test set it reached an accuracy of 79.2%, a balanced accuracy "
     "of 0.69, a macro-F1 of 0.682 and a melanoma recall of 0.589, i.e. 99 of the 168 melanomas in the test set were "
     "found and 69 were missed. Figure 4.5 shows the confusion matrix and Table 4.2 the recall per class.")
table(4, "Per-class recall of the selected model on the test set (confusions read from the normalised matrix, ±0.01)",
      ["Class", "Test images", "Recall", "Most frequent confusion"],
      [["akiec", "51", "0.63", "bkl (18%)"], ["bcc", "77", "0.61", "nv (13%)"], ["bkl", "157", "0.70", "nv (13%)"],
       ["df", "22", "0.59", "mel and nv (14% each)"], ["mel", "168", "0.59", "nv (21%), bkl (15%)"],
       ["nv", "1000", "0.86", "mel (7%)"], ["vasc", "22", "0.86", "nv (9%)"]],
      [1.2, 1.4, 1.2, 3.1], align_cols=["l", "r", "r", "l"])
figure(4, "fig4_5_confusion_matrix.png", "Normalised confusion matrix of the selected model on the test set "
       "(rows: true class, columns: predicted class).", width_in=4.6)
body("Nevi and vascular lesions are recognised best (recall 0.86), while melanoma is confused with nevi in 21% of "
     "cases and with benign keratosis in 15%. Clinically this is the worrying direction, because a melanoma that is "
     "called a mole may not be followed up. It is the reason why the web application never treats a non-melanoma result "
     "as a clearance and shows the melanoma probability separately. Two further points should be stated openly. "
     "First, the best six ResNet configurations lie within 1.6 percentage points of validation macro-F1, and every "
     "run used a single seed, so the choice of RMSProp over the others is not statistically meaningful. Second, the "
     "reference run with Adam had a higher melanoma recall (0.714) and balanced accuracy (0.722) than the selected "
     "model. Choosing it afterwards because of its test numbers would, however, bias the reported test results, so the "
     "pre-defined rule was kept.")

h3("4.1.6  What the model looks at")
body("Figure 4.6 shows Grad-CAM heatmaps for eight randomly chosen test images, all of which the model classified "
     "correctly. In these examples the strongest activation lies on the lesion itself and not on hair, ruler marks or "
     "the surrounding skin, which is the behaviour a clinician would expect. Grad-CAM shows where the network looked "
     "and not why it reached its decision, and the eight images are a small and favourable sample, so the heatmaps "
     "increase trust but do not prove that the model is correct.")
figure(4, "fig4_6_gradcam.png", "Grad-CAM heatmaps of the selected model for eight random test images (top: image "
       "with true label; bottom: heatmap with predicted label and probability).", width_in=6.9)

h3("4.1.7  Limitations")
bullets([
    "Each configuration was trained once with one random seed, so differences of one or two percentage points between "
    "runs cannot be treated as significant. Repeated runs or cross-validation would be needed.",
    "Each optimizer received a single learning rate without tuning, which is why SGD with momentum failed and SGD was "
    "still improving at the last epoch. The 15-epoch limit also ended two runs before they had converged.",
    "The model was trained on dermoscopy images only. Photographs taken with a phone are a different kind of image, "
    "and the results should not be expected to transfer.",
    "The test images come from the same clinics as the training images and have mostly been selected for clinical "
    "reasons, so performance on new patients and new devices is likely to be lower.",
    "The two rarest classes have only 22 test images each, so their per-class scores are uncertain.",
    "Melanoma recall of 0.59 is far too low for any clinical use. The system is an educational project and not a "
    "medical device.",
])

h2("4.2  Conclusion & Future Scope")
body("This project built and evaluated a deep-learning system for classifying dermoscopy images into the seven "
     "HAM10000 categories. A lesion-wise split removed a source of leakage that would have inflated the scores, and a "
     "weighted loss together with balanced metrics exposed the real behaviour of the models on the rare classes. The "
     "experiments showed that transfer learning was by far the most important factor (macro-F1 0.40 to 0.67), that "
     "data augmentation was the most useful regularizer, that class weights trade a little accuracy for recall on "
     "rare classes, and that all optimizers except an untuned SGD with momentum gave similar results. The selected "
     "ResNet-18 reached 79.2% accuracy, 0.69 balanced accuracy and 0.682 macro-F1 on the test set, but found only 59% "
     "of the melanomas. Grad-CAM showed that the model attends to the lesions, and the web application presents the "
     "result together with its uncertainty and simple guidance. The work met the objectives set in Chapter 1, and "
     "its most important lesson is that on imbalanced medical data accuracy alone is a poor measure of quality.")
body("Future work could improve the system in several directions:", after=4, keep_next=True)
bullets([
    "run several random seeds or cross-validation and tune the learning rate of each optimizer, to obtain results "
    "with confidence intervals;",
    "improve melanoma recall by cost-sensitive training, threshold tuning on the validation set, or a dedicated "
    "melanoma-versus-rest stage;",
    "try deeper or more modern backbones, test-time augmentation and ensembles of models;",
    "calibrate the predicted probabilities (for example with temperature scaling) so that a confidence of 60% really "
    "means 60%;",
    "add the patient metadata of the dataset (age, sex, body location) as extra inputs;",
    "validate on external datasets such as later ISIC collections, and train on phone photographs if the tool is to "
    "be used outside dermoscopy;",
    "package the model for mobile devices, and assess it in a clinical study before any real-world use.",
])

# ================================================================== REFERENCES + ACKNOWLEDGEMENT
# (references are listed in the order of first citation; keys never cited are appended)
ref_head = chapter("References")
for i, key in enumerate(refs_order, start=1):
    p = doc.add_paragraph()
    H.add_rich(p, f"[{i}]  {REFS[key]}", size=11)
    H.fmt(p, align=WD_ALIGN_PARAGRAPH.LEFT, after=6, line=1.15, left=0.4, first=-0.4)

chapter("Acknowledgement")
body("We would like to express our sincere gratitude to our guide and subject in-charge, Prof. Vijaya Bharathi J, for her "
     "guidance, encouragement and valuable suggestions throughout this mini project.")
body("We are thankful to the Head of the Department of Computer Science & Engineering (Artificial Intelligence & "
     "Machine Learning), the Principal, and all the teaching and non-teaching staff of A.P. Shah Institute of "
     "Technology for providing the facilities and a supportive environment for our work.")
body("We also thank the creators of the HAM10000 dataset for making it publicly available, the open-source "
     "communities behind PyTorch, scikit-learn and Flask, and our friends and family for their constant support and "
     "motivation.")

# ================================================================== LISTS AND CONTENTS (front matter tables)
tabs = doc.tables
toc, lof, lot = tabs[0], tabs[1], tabs[2]


def set_tc_text(tc, text):
    paragraphs = tc.findall(qn("w:p"))
    p = paragraphs[0]
    runs = p.findall(qn("w:r"))
    if runs:
        first = runs[0]
        for r in runs[1:]:
            p.remove(r)
        for t in first.findall(qn("w:t")):
            first.remove(t)
        t = OxmlElement("w:t")
        t.text = text
        first.append(t)
    else:
        from docx.text.paragraph import Paragraph as P
        run = P(p, None).add_run(text)
        run.font.size = Pt(12)


for row in toc.rows:
    tcs = row._tr.findall(qn("w:tc"))
    texts = ["".join(t.text or "" for t in tc.iter(qn("w:t"))).strip() for tc in tcs]
    label = next((t for t in texts if t), "").rstrip(".")
    if label in PAGES:
        set_tc_text(tcs[-1], str(PAGES[label]))

# list of figures: header + one row per figure, reusing the formatting of the template's first data row
proto = copy.deepcopy(lof.rows[1]._tr)
for row in list(lof.rows)[1:]:
    lof._tbl.remove(row._tr)
for label, caption in figures:
    tr = copy.deepcopy(proto)
    lof._tbl.append(tr)
    tcs = tr.findall(qn("w:tc"))
    set_tc_text(tcs[0], label)
    set_tc_text(tcs[1], caption)
    set_tc_text(tcs[2], str(PAGES.get(label, "")))

proto = copy.deepcopy(lot.rows[1]._tr)
for row in list(lot.rows)[1:]:
    lot._tbl.remove(row._tr)
for label, caption in tables:
    tr = copy.deepcopy(proto)
    lot._tbl.append(tr)
    tcs = tr.findall(qn("w:tc"))
    set_tc_text(tcs[0], label)
    set_tc_text(tcs[1], caption)
    set_tc_text(tcs[2], str(PAGES.get(label, "")))

doc.core_properties.title = TITLE
doc.core_properties.subject = "Deep Learning Lab (CSL701) mini project report"
doc.save(str(OUT))
print("saved", OUT)
print("figures:", len(figures), "tables:", len(tables), "references:", len(refs_order))
json.dump({"figures": figures, "tables": tables}, open(REPORT / "labels.json", "w", encoding="utf-8"), indent=1)
