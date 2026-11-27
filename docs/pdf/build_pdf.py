#!/usr/bin/env python3
"""Build docs/JMeter_Performance_Testing_Guide.pdf from the Markdown tutorials.

Needs: pip install markdown playwright pymupdf  &&  python -m playwright install chromium
Run:   python docs/pdf/build_pdf.py

How it works: Markdown -> one branded HTML file -> PDF with headless Chromium. It renders twice:
the first pass finds the page each chapter starts on, the second fills in the table of contents.
"""
import datetime
import html
import os
import re
import sys

import markdown
import pymupdf
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
ROOT = os.path.dirname(DOCS)
TUT = os.path.join(DOCS, "tutorials")
OUT_PDF = os.path.join(DOCS, "JMeter_Performance_Testing_Guide.pdf")
OUT_HTML = os.path.join(HERE, "guide.html")

NAVY, BLUE, LIGHT = "#1F2749", "#008ADD", "#7CC8F5"

PARTS = [
    ("Part 1", "Performance-testing fundamentals", "Why it matters, test types, metrics, SLOs and workload models.", ["00"]),
    ("Part 2", "JMeter basics", "Install, test plan anatomy, recording, CSV data, correlation and assertions.", ["01", "02", "03", "04", "05", "06"]),
    ("Part 3", "Advanced JMeter", "Timers, logic controllers, Groovy, non-GUI runs, distributed tests, CI and live dashboards.",
     ["07", "08", "09", "10", "11", "12", "13"]),
    ("Part 4", "Results and bottlenecks", "Reading the dashboard and percentiles, and a worked example with real data.", ["14"]),
    ("Part 5", "Cheat sheet and interview Q&A", "Commands, elements and functions on a page, and 35 interview questions.", ["15"]),
]


def tutorial_files():
    files = {}
    for f in sorted(os.listdir(TUT)):
        m = re.match(r"(\d\d)-.*\.md$", f)
        if m:
            files[m.group(1)] = os.path.join(TUT, f)
    return files


def md_to_html(text, num):
    # Drop navigation lines; they make no sense on paper.
    text = re.sub(r"^\*\*(Next|Previous):\*\*.*$", "", text, flags=re.M)
    # <details> answer blocks -> styled boxes rendered as Markdown.
    text = text.replace("<details><summary>Answers</summary>", '<div class="answers" markdown="1">\n\n**Answers**\n')
    text = text.replace("</details>", "</div>")
    # Links to other tutorials or repo files become plain text with the path in code style.
    text = re.sub(r"(?<!!)\[([^\]]+)\]\((?!https?://)([^)]+)\)", lambda m: m.group(1), text)
    # Images in docs/images are referenced relative to the tutorials folder.
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "md_in_html", "sane_lists"])
    body = body.replace('src="../images/', 'src="../images/')
    # First H1 becomes the chapter title block.
    body = re.sub(r"<h1>(.*?)</h1>", lambda m: '<h1 class="chapter-title" id="ch-%s">%s</h1>' % (num, m.group(1)), body, count=1)
    # Blockquote right after the title = chapter goal box.
    body = body.replace("<blockquote>", '<div class="goal">', 1).replace("</blockquote>", "</div>", 1)
    return body


def chapter_title(path):
    with open(path, encoding="utf-8") as f:
        first = f.readline()
    return first.lstrip("# ").strip()


def build_html(page_numbers=None):
    files = tutorial_files()
    logo = os.path.join(DOCS, "images", "k11_logo.png").replace("\\", "/")
    today = datetime.date.today().strftime("%B %Y")

    toc_rows = []
    for part, title, _, nums in PARTS:
        pn = (page_numbers or {}).get("part-" + part, "")
        toc_rows.append('<tr class="toc-part"><td><a href="#part-%s">%s · %s</a></td><td>%s</td></tr>'
                        % (part.replace(" ", ""), part, html.escape(title), pn))
        for n in nums:
            t = chapter_title(files[n])
            pn = (page_numbers or {}).get(n, "")
            toc_rows.append('<tr><td class="toc-ch"><a href="#ch-%s">%s</a></td><td>%s</td></tr>' % (n, html.escape(t), pn))

    chapters = []
    for part, title, blurb, nums in PARTS:
        chapters.append(
            '<section class="part-page" id="part-%s"><div class="part-label">%s</div><div class="part-title">%s</div>'
            '<div class="part-blurb">%s</div><div class="part-list">%s</div></section>'
            % (part.replace(" ", ""), part, html.escape(title), html.escape(blurb),
               "".join("<div>%s</div>" % html.escape(chapter_title(files[n])) for n in nums)))
        for n in nums:
            with open(files[n], encoding="utf-8") as f:
                chapters.append('<section class="chapter">%s</section>' % md_to_html(f.read(), n))

    with open(os.path.join(HERE, "guide.css"), encoding="utf-8") as f:
        css = f.read()

    return """<!doctype html><html><head><meta charset="utf-8"><title>JMeter Performance Testing Guide</title>
<style>{css}</style></head><body>
<section class="cover">
  <div class="cover-top"><img src="file:///{logo}" class="cover-logo"><div class="cover-brand">K11 TECH LAB</div></div>
  <div class="cover-main">
    <div class="cover-kicker">Beginner to advanced</div>
    <div class="cover-title">Performance Testing<br>with Apache JMeter</div>
    <div class="cover-sub">Fundamentals · JMeter basics · Advanced techniques · Results and bottlenecks · Cheat sheet and interview Q&amp;A</div>
    <div class="cover-bar"></div>
  </div>
  <div class="cover-bottom">
    <div>Hands-on companion to the GitHub repository<br><b>K11-Software-Solutions/jmeter-performance-and-load-testing</b></div>
    <div class="cover-meta">Kavita Jadhav · K11 Software Solutions · {today}<br>JMeter 5.6.3</div>
  </div>
</section>

<section class="front">
  <h1 class="front-title">How to use this guide</h1>
  <p>This guide takes you from your first performance test to analysing a bottleneck with real data. Every chapter has a matching, runnable JMeter script in the repository, and every script runs against a <b>local mock API</b> included in the repo, so you can practise safely without touching a real website.</p>
  <div class="callout"><b>The scenario used throughout.</b> A healthcare claims analytics application. Analysts log in, open a dashboard, run the <b>Claims Summary</b> report for a provider and date range, and export it. Target: <b>300 concurrent users at peak; Claims Summary p95 under 3 s; error rate under 1%</b>. Mix: dashboard 50%, Claims Summary 35%, export 15%; think time 3–8 s.</div>
  <h2>Set up once</h2>
<pre><code>git clone https://github.com/K11-Software-Solutions/jmeter-performance-and-load-testing
cd jmeter-performance-and-load-testing
node mock-server/server.js            # terminal 1: the target API
python scripts/run_tutorials.py       # terminal 2: runs every tutorial plan</code></pre>
  <h2>Suggested pace</h2>
  <table><tr><th>Week</th><th>Chapters</th><th>Outcome</th></tr>
  <tr><td>1</td><td>00–06</td><td>You can explain the metrics and build a correlated, parameterised, asserted script.</td></tr>
  <tr><td>2</td><td>07–10</td><td>You can model a realistic workload and run it from the command line with an HTML report.</td></tr>
  <tr><td>3</td><td>11–15</td><td>You can scale out, automate in CI, find a bottleneck and talk about it in an interview.</td></tr></table>
  <h2>A note on numbers</h2>
  <p>All results in this guide come from runs against the local mock on a laptop. They are real measurements of that mock, useful for learning to read results. They are <b>not</b> benchmarks of any real system. In an interview, only quote numbers from your own projects.</p>
  <p>The scripts were checked with Apache JMeter 5.6.3 in non-GUI mode. The optional InfluxDB and Grafana stack (chapter 13) was not run while the guide was written.</p>
</section>

<section class="toc"><h1 class="front-title">Contents</h1><table class="toc-table">{toc}</table></section>
{chapters}
<section class="back-cover"><img src="file:///{logo}" class="back-logo"><div class="back-text">K11 Software Solutions · K11 Tech Lab<br>github.com/K11-Software-Solutions</div></section>
</body></html>""".format(css=css, logo=logo, today=today, toc="\n".join(toc_rows), chapters="\n".join(chapters))


HEADER = '<div></div>'
FOOTER = ('<div style="width:100%;font-family:Segoe UI,Arial,sans-serif;font-size:8px;color:#6b7280;padding:0 18mm;'
          'display:flex;justify-content:space-between"><span>K11 Tech Lab · Performance Testing with Apache JMeter</span>'
          '<span><span class="pageNumber"></span></span></div>')


def render(page_numbers=None):
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html(page_numbers))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file:///" + OUT_HTML.replace("\\", "/"))
        pg.wait_for_load_state("networkidle")
        pg.pdf(path=OUT_PDF, format="A4", print_background=True, display_header_footer=True,
               header_template=HEADER, footer_template=FOOTER, prefer_css_page_size=True)
        b.close()


def find_pages():
    """Chromium stores each id= anchor as a named destination; map them to 1-based page numbers."""
    doc = pymupdf.open(OUT_PDF)
    found = {}
    for name, dest in doc.resolve_names().items():
        if name.startswith("ch-"):
            found[name[3:]] = dest["page"] + 1
        elif name.startswith("part-Part"):
            found["part-Part " + name[len("part-Part"):]] = dest["page"] + 1
    doc.close()
    return found


def _part_of(n):
    for part, _, _, nums in PARTS:
        if n in nums:
            return part
    return ""


def mask_footer_on_full_bleed_pages(pages):
    """Chromium prints the footer on every page; hide it on the navy cover, part and back pages."""
    doc = pymupdf.open(OUT_PDF)
    navy = tuple(int(NAVY[i:i + 2], 16) / 255 for i in (1, 3, 5))
    full_bleed = {1, len(doc)} | {v for k, v in pages.items() if k.startswith("part-")}
    for n in full_bleed:
        page = doc[n - 1]
        r = page.rect
        page.add_redact_annot(pymupdf.Rect(0, r.height - 50, r.width, r.height), fill=navy)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    doc.save(OUT_PDF + ".tmp", garbage=3, deflate=True)
    doc.close()
    os.replace(OUT_PDF + ".tmp", OUT_PDF)


if __name__ == "__main__":
    render()
    pages = find_pages()
    render(pages)
    mask_footer_on_full_bleed_pages(pages)
    doc = pymupdf.open(OUT_PDF)
    print("Wrote %s (%d pages). TOC entries found: %d" % (OUT_PDF, len(doc), len(pages)))
    missing = [n for n in tutorial_files() if n not in pages]
    if missing:
        print("WARNING: no page found for chapters", missing, file=sys.stderr)
