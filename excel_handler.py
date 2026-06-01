import json
import re
from io import BytesIO

from anthropic import Anthropic
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

_client: Anthropic | None = None
EXCEL_MODEL = "claude-sonnet-4-6"

# Xovia blue header + alternating row colours
_HEADER_HEX  = "185FA5"
_GREY_HEX    = "F5F5F5"
_WHITE_HEX   = "FFFFFF"

# Column names that get currency formatting
_CURRENCY_HEADERS = frozenset({
    "amount", "total", "cost", "price", "budget", "revenue",
    "salary", "income", "expense", "expenses", "profit", "loss",
    "subtotal", "tax",
})

_STRUCTURE_SYSTEM = """\
You are an Excel file architect for Xovia AI. Never mention Claude, Anthropic, or any AI provider.

When asked to create a spreadsheet, respond ONLY with a valid JSON object describing the workbook.
No markdown, no explanation, no preamble — raw JSON only.

Required format:
{
  "filename": "budget_tracker.xlsx",
  "sheets": [
    {
      "name": "Dashboard",
      "headers": ["Category", "Amount", "Percentage"],
      "rows": [["Income", 5000, "100%"], ["Expenses", 3200, "64%"]],
      "col_widths": [20, 15, 15]
    }
  ],
  "summary": "One sentence describing what was built.",
  "vba_code": "(optional) Include only if VBA automation would genuinely improve this spreadsheet. Omit the key entirely if not needed."
}

Rules:
- Create all logical sheets for the request (e.g. Dashboard, Details, Settings)
- Include realistic sample data in every sheet
- col_widths values are in Excel character units (typical: 15-25)
- Use numeric values (not strings) for any monetary or numeric fields so Excel can compute on them
- vba_code should be complete, working VBA — omit if not needed\
"""


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def _get_structure(prompt: str) -> dict:
    """Ask Claude to describe the workbook as JSON and return the parsed dict."""
    response = _get_client().messages.create(
        model=EXCEL_MODEL,
        max_tokens=4096,
        system=_STRUCTURE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences and retry
    clean = re.sub(r"^```[a-z]*\n?", "", text, flags=re.MULTILINE)
    clean = re.sub(r"```$", "", clean, flags=re.MULTILINE).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Extract the first {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group())

    raise ValueError(f"Could not parse JSON from model response: {text[:300]}")


def _build_xlsx(structure: dict) -> bytes:
    """Build an .xlsx file from a structure dict and return raw bytes."""
    wb = Workbook()
    wb.remove(wb.active)  # remove default blank sheet

    hdr_fill   = PatternFill(start_color=_HEADER_HEX, end_color=_HEADER_HEX, fill_type="solid")
    grey_fill  = PatternFill(start_color=_GREY_HEX,   end_color=_GREY_HEX,   fill_type="solid")
    white_fill = PatternFill(start_color=_WHITE_HEX,  end_color=_WHITE_HEX,  fill_type="solid")
    hdr_font   = Font(bold=True, color=_WHITE_HEX, size=11)
    centre     = Alignment(horizontal="center", vertical="center")

    for sheet_def in structure.get("sheets", []):
        name    = str(sheet_def.get("name", "Sheet"))[:31]  # Excel max 31 chars
        headers = sheet_def.get("headers", [])
        rows    = sheet_def.get("rows", [])
        widths  = sheet_def.get("col_widths", [])

        ws = wb.create_sheet(title=name)
        ws.row_dimensions[1].height = 22

        # ── Header row ──────────────────────────────────────────────────────
        for ci, hdr in enumerate(headers, 1):
            cell = ws.cell(row=1, column=ci, value=hdr)
            cell.fill   = hdr_fill
            cell.font   = hdr_font
            cell.alignment = centre

        # ── Data rows ───────────────────────────────────────────────────────
        for ri, row_data in enumerate(rows, 2):
            fill = white_fill if ri % 2 == 0 else grey_fill
            for ci, val in enumerate(row_data, 1):
                cell = ws.cell(row=ri, column=ci, value=val)
                cell.fill = fill
                # Currency format for numeric amount-like columns
                if ci <= len(headers):
                    if (
                        any(kw in headers[ci - 1].lower() for kw in _CURRENCY_HEADERS)
                        and isinstance(val, (int, float))
                    ):
                        cell.number_format = '$#,##0.00'

        # ── Column widths ───────────────────────────────────────────────────
        for ci, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(ci)].width = w
        # Auto-width for any columns beyond the specified list
        for ci in range(len(widths) + 1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(ci)].width = 18

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generate_excel(prompt: str) -> tuple[bytes | None, str, str, str | None]:
    """
    Generate an Excel workbook from a user prompt.
    Returns (excel_bytes, filename, chat_response, error_key).
    error_key is None on success.
    """
    try:
        structure = _get_structure(prompt)
    except Exception as e:
        return None, "", f"I couldn't generate the Excel structure. ({e})", "parse_error"

    try:
        excel_bytes = _build_xlsx(structure)
    except Exception as e:
        return None, "", f"I couldn't build the Excel file. ({e})", "build_error"

    filename = str(structure.get("filename", "spreadsheet.xlsx"))
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    summary  = structure.get("summary", "Your spreadsheet is ready.")
    vba_code = structure.get("vba_code", "").strip()

    lines = [f"✅ {summary}", "", "Your file is ready — click **Download as .xlsx** below."]

    if vba_code:
        lines += [
            "",
            "---",
            "### VBA Automation Code",
            "Paste this into the Visual Basic Editor (**Alt+F11** in Excel) to add automation:",
            f"```vba\n{vba_code}\n```",
            "",
            "> **Note:** VBA runs inside Excel after you paste it — it is not embedded in the "
            "downloaded .xlsx file.",
        ]

    return excel_bytes, filename, "\n".join(lines), None


# ---------------------------------------------------------------------------
# Standalone test — run with: python excel_handler.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import tomllib

    with open(".streamlit/secrets.toml", "rb") as f:
        _s = tomllib.load(f)
    os.environ["ANTHROPIC_API_KEY"] = _s["anthropic"]["api_key"]

    prompts = [
        "Can you build me a budget tracker Excel file?",
        "Create a simple sales tracker spreadsheet with columns for date, product, quantity, and revenue",
    ]
    for i, p in enumerate(prompts, 1):
        print(f"\n[{i}] {p}")
        xb, fn, resp, err = generate_excel(p)
        if err:
            print(f"    ERROR: {err}")
        else:
            with open(f"test_excel_{i}.xlsx", "wb") as fh:
                fh.write(xb)
            print(f"    Saved: test_excel_{i}.xlsx  ({len(xb):,} bytes)")
            print(f"    Response:\n{resp[:200]}...")
