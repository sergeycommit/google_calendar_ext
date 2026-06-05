#!/usr/bin/env python3
"""
Assembler: reads content/*.json → writes blog/*.html + blog/medium/*.md + blog/devto/*.md
Run: python3 build_site.py
"""
import json, re
from datetime import date, timedelta
from pathlib import Path

SITE_URL  = "https://calendar-extension.site"
STORE_URL = ("https://chromewebstore.google.com/detail/"
             "google-calendar-extension/dfbpjijneaihingmldgpgcodglkoamoe")
BLOG_DIR   = Path(__file__).parent / "blog"
MEDIUM_DIR = BLOG_DIR / "medium"
DEVTO_DIR  = BLOG_DIR / "devto"
START_DATE = date(2026, 4, 1)
DAYS_GAP   = 3

CONTENT_DIR = Path(__file__).parent / "content"

# Article plan (slug → cluster + meta, same as generate_articles.py)
from generate_articles import ARTICLES, LINK_MAP, ID_TO_ARTICLE

def pub_date(article_id: int) -> date:
    return START_DATE + timedelta(days=(article_id - 1) * DAYS_GAP)

# ── HTML assembler ────────────────────────────────────────────────────────────

def sections_to_html(sections):
    parts = []
    for s in sections:
        t = s.get("type", "h2")
        heading = s.get("heading") or s.get("h")
        content = s.get("content") or s.get("p") or ""
        bullets = s.get("bullets") or s.get("items") or []
        subheadings = s.get("subheadings") or s.get("subs") or []

        if t == "note":
            inner = content.replace("\n\n", "</p>\n<p>")
            parts.append(f'<div class="article-note">\n<p>{inner}</p>\n</div>')
        elif t == "cta":
            inner = content.replace("\n\n", "</p>\n<p>")
            parts.append(f'<div class="article-cta">\n<p>{inner}</p>\n</div>')
        elif t in ("ul", "ol"):
            tag = t
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            items = "".join(f"<li>{b}</li>\n" for b in bullets)
            parts.append(f"<{tag}>\n{items}</{tag}>")
        elif t == "h2_h3":
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            paras = content.split("\n\n") if content else []
            per = max(1, len(paras) // max(len(subheadings), 1))
            for i, sub in enumerate(subheadings):
                parts.append(f"<h3>{sub}</h3>")
                chunk = paras[i*per:(i+1)*per]
                for p in chunk:
                    if p.strip():
                        parts.append(f"<p>{p.strip()}</p>")
        else:  # h2 default
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            for para in content.split("\n\n"):
                if para.strip():
                    parts.append(f"<p>{para.strip()}</p>")
            if bullets:
                items = "".join(f"<li>{b}</li>\n" for b in bullets)
                parts.append(f"<ul>\n{items}</ul>")
    return "\n\n".join(parts)


def faq_to_html(faq):
    items = []
    for i, item in enumerate(faq, 1):
        q = item.get("question") or item.get("q", "")
        a = item.get("answer")   or item.get("a", "")
        items.append(
            f'<div class="faq-item">\n'
            f'  <button class="faq-question" role="button" id="faq-question-{i}" '
            f'aria-controls="faq-answer-{i}" aria-expanded="false">\n'
            f'    <h3>{q}</h3>\n'
            f'    <span class="faq-toggle" aria-hidden="true">+</span>\n'
            f'  </button>\n'
            f'  <div class="faq-answer" id="faq-answer-{i}" role="region" '
            f'aria-labelledby="faq-question-{i}">\n'
            f'    <p>{a}</p>\n'
            f'  </div>\n'
            f'</div>'
        )
    return '<div class="faq-list">\n' + "\n".join(items) + "\n</div>"


def faq_schema(faq):
    entries = []
    for item in faq:
        q = (item.get("question") or item.get("q","")).replace('"','\\"')
        a = (item.get("answer")   or item.get("a","")).replace('"','\\"')
        entries.append(
            f'{{"@type":"Question","name":"{q}",'
            f'"acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}'
        )
    return ",\n        ".join(entries)


def render_html(article, data, related, pub):
    pub_str   = pub.isoformat()
    pub_human = pub.strftime("%B %-d, %Y")
    slug      = article["slug"]
    title     = article["title"]
    seo_title = article["seo_title"]
    category  = article["category"]

    meta_desc   = data.get("meta_description") or data.get("meta","")
    intro       = data.get("intro","")
    read_time   = data.get("read_time", 6)
    sections    = data.get("body_sections") or data.get("sections", [])
    takeaways   = data.get("sidebar_takeaways") or data.get("takeaways", [])
    cta_text    = data.get("sidebar_cta_text") or data.get("cta_text","")
    rel_title   = data.get("related_title","Keep exploring this topic.")
    faq         = data.get("faq", [])

    body_html = sections_to_html(sections)
    faq_html_str = faq_to_html(faq)
    faq_sch   = faq_schema(faq)
    takeaways_li = "\n".join(f"<li>{t}</li>" for t in takeaways)

    related_cards = "\n".join(
        f'<article class="related-card">\n'
        f'  <h3>{r["title"]}</h3>\n'
        f'  <p>From the {r["cluster_name"]} series.</p>\n'
        f'  <a href="./{r["slug"]}.html" class="read-more">Read article →</a>\n'
        f'</article>'
        for r in related
    )
    footer_links_html = '<li><a href="./">Blog home</a></li>\n' + "\n".join(
        f'<li><a href="./{r["slug"]}.html">{r["title"]}</a></li>' for r in related
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{seo_title} | Schedule Calendar</title>
    <link rel="canonical" href="{SITE_URL}/blog/{slug}.html">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="{SITE_URL}/images/screenshot1.png">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{pub_str}">
    <meta property="article:author" content="Schedule Calendar Team">
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../css/site-refresh.css?v=20260326">
    <link rel="icon" type="image/png" href="../images/logo.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script type="application/ld+json">
    {{"@context":"https://schema.org","@type":"Article","headline":"{title}","description":"{meta_desc}","author":{{"@type":"Organization","name":"Schedule Calendar Team"}},"publisher":{{"@type":"Organization","name":"Schedule Calendar","logo":{{"@type":"ImageObject","url":"{SITE_URL}/images/logo.png"}}}},"datePublished":"{pub_str}","dateModified":"{pub_str}","mainEntityOfPage":"{SITE_URL}/blog/{slug}.html","image":"{SITE_URL}/images/screenshot1.png"}}
    </script>
    <script type="application/ld+json">
    {{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_sch}]}}
    </script>
</head>
<body class="schedule-article">
    <div class="scroll-progress"></div>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand">
                    <img src="../images/logo.png" alt="Schedule Calendar logo" class="logo" width="42" height="42">
                    <span class="brand-name">Schedule Calendar</span>
                </div>
                <ul class="nav-menu">
                    <li><a href="../index.html">Home</a></li>
                    <li><a href="../index.html#features">Features</a></li>
                    <li><a href="./">Blog</a></li>
                    <li><a href="../support.html">Support</a></li>
                    <li><a href="{STORE_URL}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">Add to Chrome</a></li>
                </ul>
                <button class="hamburger" aria-label="Toggle navigation menu" aria-expanded="false" tabindex="0">
                    <span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>
                </button>
            </div>
        </nav>
    </header>
    <div class="nav-overlay"></div>
    <main class="blog-main">
        <div class="container">
            <section class="article-hero">
                <div class="article-breadcrumbs">
                    <a href="./" class="text-link">Blog</a><span>/</span><span>{category}</span>
                </div>
                <div class="eyebrow">Published {pub_human}</div>
                <h1 class="article-title">{title}</h1>
                <p class="article-intro">{intro}</p>
                <p class="article-meta">{read_time} min read · Written by the Schedule Calendar Team</p>
            </section>
            <section class="article-layout">
                <article class="article-body-card">
                    <img src="../images/screenshot1.png" alt="Schedule Calendar Chrome extension showing upcoming events" class="article-cover" width="1365" height="768">
                    {body_html}
                    <section class="article-faq" aria-label="Frequently asked questions">
                        <h2>Frequently asked questions</h2>
                        {faq_html_str}
                    </section>
                </article>
                <aside class="article-sidebar">
                    <h3>Key takeaways</h3>
                    <ul>{takeaways_li}</ul>
                    <h3>Try next</h3>
                    <p>{cta_text}</p>
                    <a href="{STORE_URL}" class="btn btn-primary" target="_blank" rel="noopener">Add to Chrome</a>
                </aside>
            </section>
            <section class="section">
                <div class="section-header">
                    <span class="section-kicker">Related reading</span>
                    <h2 class="section-title">{rel_title}</h2>
                </div>
                <div class="related-grid">{related_cards}</div>
            </section>
        </div>
    </main>
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-card">
                    <div class="nav-brand">
                        <img src="../images/logo.png" alt="Schedule Calendar logo" class="footer-logo" width="42" height="42">
                        <span class="footer-brand-name">Schedule Calendar</span>
                    </div>
                    <p class="footer-description">Workflow notes for people who want their calendar to support the day, not dominate it.</p>
                </div>
                <div class="footer-card">
                    <h4>Read next</h4>
                    <ul class="footer-links">{footer_links_html}</ul>
                </div>
                <div class="footer-card">
                    <h4>Explore</h4>
                    <ul class="footer-links">
                        <li><a href="../index.html">Home</a></li>
                        <li><a href="../support.html">Support</a></li>
                        <li><a href="../privacy-policy.html">Privacy Policy</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom"><p>&copy; 2026 Schedule Calendar. All rights reserved.</p></div>
        </div>
    </footer>
    <button class="back-to-top" aria-label="Back to top">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z"/></svg>
    </button>
    <script src="../js/script.js?v=20260326"></script>
</body>
</html>"""


def render_medium(article, data):
    medium_body = data.get("medium_body") or data.get("medium","")
    return f"""# {article['title']}

*Originally published on [Schedule Calendar Blog]({SITE_URL}/blog/{article['slug']}.html)*

---

{medium_body}

---

**Want the full guide?** Read the complete article on the [Schedule Calendar blog]({SITE_URL}/blog/{article['slug']}.html) — including step-by-step tips, a FAQ section, and how a lightweight Chrome extension helps you put these habits into practice without adding friction to your day.

[Add Schedule Calendar to Chrome]({STORE_URL}) — free, no account required.
"""


def render_devto(article, data):
    tags = data.get("devto_tags", "productivity,googlecalendar,chrome,timemanagement")
    devto_body = data.get("devto_body", data.get("medium_body", ""))
    meta_desc = data.get("meta_description", "")
    slug = article["slug"]
    return f"""---
title: "{article['title']}"
published: false
description: "{meta_desc}"
tags: {tags}
canonical_url: {SITE_URL}/blog/{slug}.html
---

{devto_body}

---

*[Schedule Calendar]({STORE_URL}) — free Chrome extension. Your Google Calendar in one click from the toolbar.*
"""


def main():
    BLOG_DIR.mkdir(exist_ok=True)
    MEDIUM_DIR.mkdir(exist_ok=True)
    DEVTO_DIR.mkdir(exist_ok=True)

    # Load all content files
    all_content: dict[str, dict] = {}
    for f in sorted(CONTENT_DIR.glob("cluster_*.json")):
        data = json.loads(f.read_text())
        for item in data:
            all_content[item["slug"]] = item

    ok = 0
    skip = 0
    missing = []

    for article in ARTICLES:
        slug = article["slug"]
        html_path  = BLOG_DIR / f"{slug}.html"
        md_path    = MEDIUM_DIR / f"{slug}.md"
        devto_path = DEVTO_DIR / f"{slug}.md"

        if slug not in all_content:
            missing.append(slug)
            continue

        data    = all_content[slug]
        rel_ids = LINK_MAP.get(article["id"], [])
        related = [ID_TO_ARTICLE[i] for i in rel_ids if i in ID_TO_ARTICLE]
        pub     = pub_date(article["id"])

        html_path.write_text(render_html(article, data, related, pub), encoding="utf-8")
        md_path.write_text(render_medium(article, data), encoding="utf-8")
        devto_path.write_text(render_devto(article, data), encoding="utf-8")
        print(f"  ✓ {slug}")
        ok += 1

    print(f"\nDone — {ok} articles written, {len(missing)} missing content.")
    if missing:
        print("Missing:", missing[:10])


if __name__ == "__main__":
    main()
