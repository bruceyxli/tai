import pathlib, re

files = [
    ('rag/test_output/smart_reading_diff_v6.md', 'OOP · CS61A (5 min)'),
    ('rag/test_output/smart_reading_diff_v6_l01.md', 'L01 Functional Programming · CS61A (51 min)'),
    ('rag/test_output/smart_reading_diff_jensen_huang.md', '黄仁勋深度访谈 · Bilibili (58 min)'),
]

def md_to_html(text):
    text = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^\-\-\-$', r'<hr>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text

sections_html = []
for path, label in files:
    content = pathlib.Path('d:/tai/tai/' + path).read_text(encoding='utf-8')
    html_body = md_to_html(content)
    sections_html.append(
        f'<div class="video-section"><h1 class="video-label">{label}</h1>{html_body}</div>'
    )

combined = '\n<div class="page-break"></div>\n'.join(sections_html)

css = """
body { font-family: -apple-system, Arial, sans-serif; font-size: 13px; max-width: 860px; margin: 0 auto; padding: 24px; color: #24292e; }
del { background: #ffd7d7; color: #8b0000; text-decoration: line-through; padding: 1px 2px; border-radius: 2px; }
ins { background: #d4edda; color: #155724; text-decoration: none; padding: 1px 2px; border-radius: 2px; }
.section { border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin-bottom: 24px; }
.timestamp { font-size: 12px; color: #888; font-family: monospace; margin-bottom: 4px; }
.title-row { font-size: 14px; margin-bottom: 10px; }
.label { font-size: 11px; font-weight: bold; color: #666; text-transform: uppercase; margin-top: 12px; margin-bottom: 4px; }
.stat { font-size: 12px; background: #f6f8fa; border-radius: 4px; padding: 6px 12px; margin-bottom: 8px; font-family: monospace; }
.wc { font-size: 11px; color: #555; font-family: monospace; background: #f6f8fa; padding: 2px 6px; border-radius: 3px; margin-left: 8px; }
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }
th { background: #f6f8fa; padding: 6px 12px; border: 1px solid #ddd; text-align: left; }
td { padding: 6px 12px; border: 1px solid #ddd; }
h1 { border-bottom: 2px solid #e1e4e8; padding-bottom: 8px; }
h2 { color: #0366d6; margin-top: 24px; }
.video-label { background: #0366d6; color: white; padding: 8px 16px; border-radius: 6px; font-size: 16px; border: none; }
.video-section { margin-bottom: 48px; }
.page-break { page-break-after: always; height: 1px; }
hr { border: none; border-top: 2px solid #e1e4e8; margin: 32px 0; }
p { line-height: 1.6; }
"""

full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Smart Reading v6 — Video Diff Report</title>
<style>{css}</style>
</head><body>
<h1 style="text-align:center; font-size:22px; border:none;">Smart Reading v6 — Video Diff Report</h1>
<p style="text-align:center; color:#666; margin-top:0;">RAG Pipeline · Oral Transcript → Formal Lecture Notes · April 2026</p>
<hr>
{combined}
</body></html>"""

out = pathlib.Path('d:/tai/tai/rag/test_output/smart_reading_report.html')
out.write_text(full_html, encoding='utf-8')
print(f'HTML written: {len(full_html)} chars')
