"""Minimal standalone HTML renderer for the operator console demo."""

from __future__ import annotations

from html import escape


def render_operator_case_html(view_model) -> str:
    section_html = "\n".join(
        f"""
        <section class="panel">
          <h2>{escape(section.title)}</h2>
          <p>{escape(section.body)}</p>
        </section>
        """
        for section in view_model.sections
    )
    evidence_items = "".join(
        f"<li>{escape(evidence_id)}</li>" for evidence_id in view_model.evidence_ids
    ) or "<li>None</li>"
    checklist_items = "".join(
        f"<li>{escape(item)}</li>" for item in view_model.checklist
    ) or "<li>Review pending</li>"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StoreOps Triage Agent</title>
  <style>
    :root {{
      --bg: #f4efe4;
      --paper: #fffaf0;
      --ink: #172121;
      --muted: #5d5d57;
      --accent: #b6462d;
      --accent-soft: #f2d4bf;
      --border: #d8c9ae;
      --ok: #2b6e49;
      --warn: #8b5e00;
      --danger: #9a2c2c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Noto Serif KR", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff6dc 0, transparent 30rem),
        linear-gradient(135deg, #f3ebda 0%, var(--bg) 48%, #ece5d7 100%);
    }}
    .shell {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero {{
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 16px 48px rgba(23, 33, 33, 0.08);
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      color: var(--muted);
    }}
    h1 {{
      margin: 8px 0 12px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      line-height: 1.05;
    }}
    .lede {{
      max-width: 58rem;
      color: var(--muted);
      font-size: 1.05rem;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 20px;
    }}
    .meta-card, .panel, .aside-card {{
      background: rgba(255, 250, 240, 0.92);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.95fr);
      gap: 18px;
      margin-top: 18px;
    }}
    .stack {{
      display: grid;
      gap: 14px;
    }}
    h2, h3 {{
      margin: 0 0 10px;
      font-size: 1.05rem;
    }}
    p {{
      margin: 0;
      line-height: 1.55;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    .pill {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.92rem;
      margin-right: 8px;
    }}
    .approval {{
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }}
    .approval label {{
      display: flex;
      gap: 10px;
      align-items: center;
    }}
    .mono {{
      font-family: "Cascadia Code", Consolas, monospace;
      font-size: 0.92rem;
      color: var(--muted);
    }}
    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header class="hero">
      <div class="eyebrow">StoreOps Triage Agent</div>
      <h1>{escape(view_model.headline)}</h1>
      <p class="lede">{escape(view_model.current_status)}. {escape(view_model.cause_or_abstention)}</p>
      <div class="meta">
        <div class="meta-card"><div class="eyebrow">Case</div><strong>{escape(view_model.case_id)}</strong></div>
        <div class="meta-card"><div class="eyebrow">State</div><strong>{escape(view_model.state)}</strong></div>
        <div class="meta-card"><div class="eyebrow">Assessment</div><strong>{escape(view_model.assessment)}</strong></div>
        <div class="meta-card"><div class="eyebrow">Evidence</div><strong>{view_model.evidence_count}</strong></div>
      </div>
    </header>
    <div class="layout">
      <main class="stack">
        {section_html}
      </main>
      <aside class="stack">
        <section class="aside-card">
          <h3>Approvals</h3>
          <div class="approval">
            <label><input type="checkbox" disabled> 원인 판단 승인</label>
            <label><input type="checkbox" disabled> 담당자/라우팅 승인</label>
            <label><input type="checkbox" disabled> 사장님 답변 승인</label>
          </div>
        </section>
        <section class="aside-card">
          <h3>Checklist</h3>
          <ul>{checklist_items}</ul>
        </section>
        <section class="aside-card">
          <h3>Evidence IDs</h3>
          <ul>{evidence_items}</ul>
        </section>
        <section class="aside-card">
          <h3>Technical Snapshot</h3>
          <div class="mono">retrieved policies: {escape(', '.join(view_model.technical_details['retrieved_policy_ids']))}</div>
        </section>
      </aside>
    </div>
  </div>
</body>
</html>
"""


__all__ = ["render_operator_case_html"]
