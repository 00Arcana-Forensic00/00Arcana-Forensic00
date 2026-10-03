"""Renders the Arcalume legal and support pages into the website (site/arcalume/).

The Markdown files in android/store/ are the source; the HTML is generated so the pages Play
links to never drift from the reviewed text. Standard library only:

    python3 android/store/build_pages.py
"""
import html
import pathlib
import re

STORE = pathlib.Path(__file__).resolve().parent
SITE = STORE.parents[1] / "site" / "arcalume"

PAGES = {
    "privacy.html": STORE / "legal" / "PRIVACY_POLICY.md",
    "terms.html": STORE / "legal" / "TERMS_OF_USE.md",
    "refunds.html": STORE / "legal" / "REFUND_POLICY.md",
    "notices.html": STORE / "legal" / "THIRD_PARTY_NOTICES.md",
    "support.html": STORE / "SUPPORT_PAGE.md",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ --bg: #0b0f14; --panel: #121821; --border: #1f2a38; --text: #e6edf3; --muted: #93a4b8; --accent: #4fb0ff;
            --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
    @media (prefers-color-scheme: light) {{ :root {{ --bg: #ffffff; --panel: #f4f6f8; --border: #d6dde5; --text: #14202c; --muted: #4a5a6a; --accent: #0b62a8; }} }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: var(--sans); line-height: 1.6; }}
    main {{ max-width: 46rem; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    nav {{ font-size: 0.9rem; margin-bottom: 1.5rem; }}
    a {{ color: var(--accent); }}
    h1 {{ font-size: 1.7rem; line-height: 1.25; }}
    h2 {{ font-size: 1.15rem; margin-top: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; display: block; overflow-x: auto; font-size: 0.92rem; }}
    th, td {{ border: 1px solid var(--border); padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }}
    code {{ background: var(--panel); padding: 0 0.25rem; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
<nav><a href="support.html">Arcalume help</a> · <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms</a> · <a href="refunds.html">Refunds</a></nav>
{body}
</main>
</body>
</html>
"""


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"(?<![\"'>])(https://[^\s<)]+[^\s<).,])", r'<a href="\1">\1</a>', text)


def render(md: str) -> tuple[str, str]:
    out, title = [], "Arcalume"
    blocks = re.split(r"\n\s*\n", md.strip())
    for block in blocks:
        lines = block.splitlines()
        first = lines[0]
        if first.startswith("# "):
            title = first[2:].strip()
            out.append(f"<h1>{inline(title)}</h1>")
            rest = "\n".join(lines[1:]).strip()
            if rest:
                out.append(f"<p>{'<br>'.join(inline(l) for l in rest.splitlines())}</p>")
        elif first.startswith("## "):
            out.append(f"<h2>{inline(first[3:])}</h2>")
            if len(lines) > 1:
                out.append(f"<p>{inline(' '.join(lines[1:]))}</p>")
        elif first.startswith("- "):
            items, cur = [], None
            for l in lines:
                if l.startswith("- "):
                    cur = [l[2:].strip()]
                    items.append(cur)
                else:
                    cur.append(l.strip())
            out.append("<ul>" + "".join(f"<li>{inline(' '.join(i))}</li>" for i in items) + "</ul>")
        elif first.startswith("|"):
            rows = [r.strip().strip("|").split("|") for r in lines if not re.match(r"^\|[-| ]+\|$", r.strip())]
            head, body = rows[0], rows[1:]
            out.append(
                "<table><thead><tr>" + "".join(f"<th>{inline(c.strip())}</th>" for c in head) + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{inline(c.strip())}</td>" for c in r) + "</tr>" for r in body)
                + "</tbody></table>"
            )
        else:
            # Prose is joined; a line ending in a backslash (a CommonMark hard break) keeps its break.
            text = " ".join(l.strip() for l in lines)
            out.append(f"<p>{'<br>'.join(inline(part.strip()) for part in text.split(chr(92) + ' '))}</p>")
    return title, "\n".join(out)


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    for name, src in PAGES.items():
        title, body = render(src.read_text(encoding="utf-8"))
        (SITE / name).write_text(TEMPLATE.format(title=html.escape(title), body=body), encoding="utf-8")
        print(f"site/arcalume/{name} <- {src.relative_to(STORE.parents[1])}")


if __name__ == "__main__":
    main()
