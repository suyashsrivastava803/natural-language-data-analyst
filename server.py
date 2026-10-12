"""Fieldnote's local API and static file server (Python standard library only)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
import sqlite3
import statistics
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MAX_BYTES = 25 * 1024 * 1024
MAX_ROWS = 250_000
MAX_COLUMNS = 200
DATASETS: dict[str, dict] = {}
ACCOUNT_DB = PROJECT_DIR / "fieldnote.sqlite3"
SESSION_SECONDS = 8 * 60 * 60


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def db_connect():
    connection = sqlite3.connect(ACCOUNT_DB, timeout=10, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize_database():
    with db_connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY COLLATE NOCASE, salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE, expires_at INTEGER NOT NULL)")
        db.execute("CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at)")


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 310_000).hex()


def clean_number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[$£€¥,%\s]", "", text)
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        number = float(text)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def normalize_hindi_question(question):
    terms = {
        "समय के साथ": "over time", "के अनुसार": "by", "सबसे ज्यादा": "highest", "सबसे अधिक": "highest",
        "सबसे कम": "lowest", "कितने": "how many", "कितनी": "how many", "कुल": "total",
        "योग": "total", "औसत": "average", "माध्यिका": "median", "राजस्व": "revenue",
        "बिक्री": "sales", "लागत": "cost", "खर्च": "cost", "लाभ": "profit",
        "क्षेत्र": "region", "उत्पाद": "product", "ग्राहक": "customer", "महीने": "month",
        "महीना": "month", "वर्ष": "year", "तारीख": "date", "संबंध": "relationship",
        "सहसंबंध": "correlation", "अलग": "distinct", "अद्वितीय": "unique", "पंक्तियां": "rows",
        "पंक्तियाँ": "rows", "दिखाएं": "show", "दिखाओ": "show", "बताएं": "show"
    }
    result = str(question)
    for hindi, english in sorted(terms.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(hindi, english)
    return result


def infer_types(headers, rows, overrides=None):
    result = {}
    for header in headers:
        values = [row.get(header, "") for row in rows if str(row.get(header, "")).strip()]
        nums = sum(clean_number(value) is not None for value in values)
        dates = sum(is_date(value) for value in values)
        result[header] = ("number" if values and nums / len(values) >= .78 else
                          "date" if values and dates / len(values) >= .78 else "category")
    for header, type_name in (overrides or {}).items():
        if header in result and type_name in ("number", "date", "category"):
            result[header] = type_name
    return result


def is_date(value):
    value = str(value).strip()
    return bool(re.match(r"^\d{4}[-/]\d{1,2}([-/]\d{1,2})?$", value) or
                re.match(r"^\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}$", value) or
                re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", value))


def read_csv_bytes(payload):
    text = payload.decode("utf-8-sig", errors="replace")
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text, newline=""), dialect=dialect)
    raw_headers = next(reader, [])
    headers = [str(h or "").strip() or f"Column {i + 1}" for i, h in enumerate(raw_headers)]
    if len(headers) < 2:
        raise ValueError("I need a header row with at least two columns. Check that this is a CSV export.")
    if len(headers) > MAX_COLUMNS:
        raise ValueError(f"This file has more than {MAX_COLUMNS} columns. Remove columns you don't need and try again.")
    if len(set(headers)) != len(headers):
        raise ValueError("Two columns have the same name. Rename duplicate headers and upload the file again.")
    rows = []
    for values in reader:
        if len(rows) >= MAX_ROWS:
            raise ValueError(f"This file exceeds the {MAX_ROWS:,} row limit. Filter or split it before uploading.")
        row = {h: str(values[index] if index < len(values) else "").strip() for index, h in enumerate(headers)}
        if any(v.strip() for v in row.values()):
            rows.append(row)
    if not rows:
        raise ValueError("I found the headers, but there are no data rows.")
    return headers, rows


def parse_xlsx(payload):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError("Excel support is optional. Install it with `py -m pip install -r requirements.txt`, then restart Fieldnote.") from exc
    try:
        book = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        sheet = book.active
        iterator = sheet.iter_rows(values_only=True)
        raw_headers = next(iterator, None)
        if not raw_headers:
            raise ValueError("The first worksheet is empty.")
        headers = [str(h).strip() if h is not None and str(h).strip() else f"Column {i + 1}" for i, h in enumerate(raw_headers)]
        while headers and headers[-1].startswith("Column ") and all(row is None for row in raw_headers[len(headers):]):
            break
        headers = headers[:MAX_COLUMNS]
        rows = []
        for values in iterator:
            if len(rows) >= MAX_ROWS:
                raise ValueError(f"This file exceeds the {MAX_ROWS:,} row limit.")
            row = {}
            for index, header in enumerate(headers):
                value = values[index] if index < len(values) else None
                row[header] = value.isoformat() if hasattr(value, "isoformat") else str(value or "").strip()
            if any(row.values()):
                rows.append(row)
        book.close()
        if len(headers) < 2 or not rows:
            raise ValueError("The first worksheet needs a header row and at least one data row.")
        if len(set(headers)) != len(headers):
            raise ValueError("Two columns have the same name. Rename duplicate headers and upload again.")
        return headers, rows
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("I couldn't read this Excel workbook. Try exporting the first sheet as CSV.") from exc


def summary(dataset):
    headers, rows = dataset["headers"], dataset["rows"]
    types = infer_types(headers, rows, dataset.get("typeOverrides"))
    missing = sum(not str(row.get(h, "")).strip() for row in rows for h in headers)
    duplicates = len(rows) - len({tuple(row.get(h, "") for h in headers) for row in rows})
    issues = []
    if missing:
        issues.append({"kind": "missing", "count": missing, "label": "empty cells"})
    if duplicates:
        issues.append({"kind": "duplicates", "count": duplicates, "label": "duplicate rows"})
    filter_options = {}
    for header in headers:
        values = list(dict.fromkeys(row.get(header, "") or "(blank)" for row in rows))
        filter_options[header] = values[:100]
    return {"id": dataset["id"], "fileName": dataset["fileName"], "headers": headers,
            "types": types, "totalRows": len(rows), "totalColumns": len(headers),
            "numericColumns": [h for h in headers if types[h] == "number"],
            "missingCells": missing, "duplicateRows": duplicates, "issues": issues,
            "preview": rows[:40], "filterOptions": filter_options, "aiAvailable": bool(os.environ.get("OPENAI_API_KEY")),
            "aiModel": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")}


ALIASES = {"revenue": ["sales", "income", "turnover", "amount"], "sales": ["revenue", "income", "turnover", "amount"],
           "profit": ["margin", "earnings", "net income"], "cost": ["expense", "spend", "spending"],
           "units": ["quantity", "volume", "items"], "date": ["time", "month", "year", "day"],
           "region": ["area", "territory", "location"], "customer": ["client", "buyer"], "rating": ["score", "satisfaction"]}


def mention_column(question, headers, types, allowed=None):
    q = normalized(question)
    raw_question = str(question).casefold()
    options = []
    for header in headers:
        if allowed and header not in allowed:
            continue
        words = normalized(header).split()
        score = 10 + len(header) if normalized(header) and normalized(header) in q else 0
        if str(header).strip() and str(header).casefold() in raw_question:
            score += 14 + len(str(header))
        score += sum(4 for word in words if len(word) > 2 and re.search(rf"\b{re.escape(word)}\b", q))
        for word in words:
            score += sum(3 for alias in ALIASES.get(word, []) if re.search(rf"\b{re.escape(alias)}\b", q))
        if score:
            options.append((score, header))
    return max(options, default=(0, None))[1]


def fallback_plan(question, dataset):
    headers, rows = dataset["headers"], dataset["rows"]
    types = infer_types(headers, rows, dataset.get("typeOverrides"))
    nums = [h for h in headers if types[h] == "number"]
    q = normalized(question)
    if re.search(r"\b(correlat|relationship|related|connection|associate)\b", q):
        mentioned = [h for h in nums if normalized(h) in q]
        if len(mentioned) >= 2:
            return {"operation": "correlation", "metric": mentioned[0], "second": mentioned[1], "group_by": None, "sort": "desc"}
        return None
    op = "average" if re.search(r"\b(average|avg|mean)\b", q) else "median" if "median" in q else "count" if re.search(r"\b(count|how many|number of|frequency)\b", q) and not re.search(r"\b(total|sum|revenue|sales|average|avg)\b", q) else "min" if re.search(r"\b(lowest|least|smallest|minimum|min)\b", q) else "max" if re.search(r"\b(highest|most|largest|maximum|max)\b", q) else "count" if re.search(r"\b(count|how many|number of|frequency)\b", q) else "sum"
    metric = mention_column(question, headers, types, nums)
    named_category = mention_column(question, headers, types, [h for h in headers if types[h] == "category"])
    if re.search(r"\b(unique|distinct)\b", q) or (named_category and re.search(r"\b(how many|number of|count)\b", q) and not re.search(r"\b(by|per|across)\b", q)):
        op = "distinct"
        metric = named_category or mention_column(question, headers, types)
    if not metric:
        metric = next((h for h in nums if re.search(r"revenue|sales|amount|total|value|profit|cost|price|units|quantity", h, re.I)), nums[0] if nums else None)
    if op not in ("count", "distinct") and not metric:
        return None
    if op == "distinct" and not metric:
        return None
    dim_headers = [h for h in headers if h != metric and types[h] != "number"]
    group = mention_column(question, headers, types, dim_headers)
    is_trend = bool(re.search(r"\b(over time|trend|by month|by year|monthly|daily|weekly|throughout|each month|each year)\b", q))
    if is_trend and not group:
        group = next((h for h in headers if types[h] == "date"), None)
    if not group and re.search(r"\b(by|per|across|between|compare|comparison|breakdown)\b", q):
        group = next((h for h in dim_headers if types[h] == "category"), None)
    sort_order = "asc" if op == "min" else "desc"
    if group and op in ("min", "max"):
        op = "sum"
    return {"operation": op, "metric": metric, "second": None, "group_by": group, "sort": sort_order, "time_grain": "year" if "year" in q else "month"}


def ai_plan(question, dataset):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    headers, rows = dataset["headers"], dataset["rows"]
    types = infer_types(headers, rows, dataset.get("typeOverrides"))
    schema = [{"name": h, "type": types[h]} for h in headers]
    allowed = {"operation": ["sum", "average", "median", "count", "distinct", "min", "max", "correlation"], "metric": "column name or null", "second": "column name or null", "group_by": "column name or null", "sort": ["asc", "desc"], "time_grain": ["month", "year", None]}
    request_body = {"model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"}, "temperature": 0,
        "messages": [{"role": "system", "content": "Convert a user's data question into a safe analysis plan. Return only a JSON object with keys operation, metric, second, group_by, sort, time_grain. Use only exact column names from the schema. Never write code or SQL. If unclear, return {\"operation\":\"clarify\",\"reason\":\"short question\"}. Supported operations: sum, average, median, count, min, max, correlation."},
                      {"role": "user", "content": json.dumps({"question": question, "schema": schema, "allowed_plan_values": allowed}, ensure_ascii=False)}]}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(request_body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode())
        plan = json.loads(result["choices"][0]["message"]["content"])
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, IndexError) as exc:
        raise RuntimeError("AI interpretation did not respond. Try again or turn off AI interpretation to use Fieldnote's built-in question matching.") from exc
    ops = allowed["operation"]
    if plan.get("operation") == "clarify":
        return {"clarify": str(plan.get("reason", "Could you name a column and the result you want?"))[:240]}
    if plan.get("operation") not in ops:
        return None
    for key_name in ("metric", "second", "group_by"):
        if plan.get(key_name) is not None and plan[key_name] not in headers:
            return None
    if plan.get("operation") not in ("count", "distinct") and plan.get("metric") not in [h for h in headers if types[h] == "number"]:
        return None
    if plan.get("operation") == "correlation" and plan.get("second") not in [h for h in headers if types[h] == "number"]:
        return None
    return plan


def apply_filters(rows, filters, headers):
    if not isinstance(filters, list):
        return rows
    valid = [item for item in filters if isinstance(item, dict) and item.get("column") in headers]
    result = rows
    for rule in valid:
        column, value = rule["column"], str(rule.get("value", ""))
        if value == "(blank)":
            result = [row for row in result if not row.get(column, "").strip()]
        else:
            result = [row for row in result if row.get(column, "") == value]
    return result


def row_count_value(rows):
    return len(rows)


def aggregate(rows, metric, operation):
    if operation == "count":
        return len(rows)
    if operation == "distinct":
        return len({str(row.get(metric, "")).strip() for row in rows if str(row.get(metric, "")).strip()})
    values = [clean_number(row.get(metric)) for row in rows]
    values = [value for value in values if value is not None]
    if not values:
        return None
    if operation == "average":
        return statistics.fmean(values)
    if operation == "median":
        return statistics.median(values)
    if operation == "min":
        return min(values)
    if operation == "max":
        return max(values)
    return sum(values)


def fmt(value):
    if value is None:
        return "—"
    return f"{value:,.2f}".rstrip("0").rstrip(".") if isinstance(value, float) and not value.is_integer() else f"{value:,.0f}"


def analyze(question, dataset, filters, use_ai=False):
    rows = apply_filters(dataset["rows"], filters, dataset["headers"])
    if not rows:
        raise ValueError("No rows match those filters. Remove a filter or choose another value.")
    plan = ai_plan(question, dataset) if use_ai else None
    if plan is None:
        plan = fallback_plan(question, dataset)
    if not plan:
        raise ValueError("I couldn't confidently map that question to these columns. Try naming a field, like “average Revenue by Region,” or turn on AI interpretation for more flexible phrasing.")
    if plan.get("clarify"):
        raise ValueError("I need a little more detail: " + plan["clarify"])
    op, metric, group = plan["operation"], plan.get("metric"), plan.get("group_by")
    if op == "correlation":
        second = plan.get("second")
        pairs = [(clean_number(row.get(metric)), clean_number(row.get(second))) for row in rows]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        if len(pairs) < 3:
            raise ValueError("A relationship needs at least three rows with both values present.")
        mx = statistics.fmean(x for x, _ in pairs); my = statistics.fmean(y for _, y in pairs)
        numerator = sum((x-mx)*(y-my) for x, y in pairs)
        denominator = math.sqrt(sum((x-mx)**2 for x, _ in pairs) * sum((y-my)**2 for _, y in pairs))
        corr = numerator / denominator if denominator else 0
        strength = "strong" if abs(corr) >= .7 else "moderate" if abs(corr) >= .4 else "weak"
        direction = "positive" if corr >= 0 else "negative"
        return {"title": f"{metric} and {second}", "type": "RELATIONSHIP", "metric": metric, "second": second, "correlation": corr,
                "points": [{"x": x, "y": y} for x, y in pairs[:500]], "explanation": f"{metric} and {second} show a {strength} {direction} relationship in these {len(pairs):,} rows (correlation {corr:.2f}). This describes a pattern, not a cause.",
                "note": f"Pearson correlation on {len(pairs):,} rows with both values present.", "footnote": f"Each dot is one row · {len(pairs):,} complete pairs", "usedRows": len(pairs), "filters": filters}
    if not group:
        value = aggregate(rows, metric, op)
        if value is None:
            raise ValueError(f"There are no usable numeric values in {metric} after applying the filters.")
        label = "Row count" if op == "count" else f"Distinct {metric} count" if op == "distinct" else f"{op.title()} {metric}"
        return {"title": label, "type": "SUMMARY", "metric": metric, "group": None, "operation": op,
                "points": [{"label": label, "value": value, "rows": len(rows)}],
                "explanation": f"There are {fmt(value)} rows in this selection." if op == "count" else f"There are {fmt(value)} distinct {metric} values in this selection." if op == "distinct" else f"The {op} {metric} across {len(rows):,} filtered rows is {fmt(value)}.",
                "note": f"Calculated from {len(rows):,} rows. Empty or non-numeric {metric} values are skipped.", "footnote": f"Based on {len(rows):,} filtered rows", "usedRows": len(rows), "filters": filters}
    types = infer_types(dataset["headers"], dataset["rows"], dataset.get("typeOverrides"))
    groups = {}
    for row in rows:
        label = row.get(group, "") or "(blank)"
        if types[group] == "date":
            try:
                d = datetime.fromisoformat(label.replace("Z", "+00:00"))
                label = str(d.year) if plan.get("time_grain") == "year" else d.strftime("%b %y")
            except ValueError:
                pass
        groups.setdefault(label, []).append(row)
    points = [{"label": key, "value": aggregate(items, metric, op), "rows": len(items)} for key, items in groups.items()]
    points = [point for point in points if point["value"] is not None]
    if not points:
        raise ValueError("Those columns don't contain enough usable values to make a chart.")
    if types[group] == "date":
        points.sort(key=lambda point: datetime.strptime(point["label"], "%b %y") if re.match(r"^[A-Z][a-z]{2} \d{2}$", point["label"]) else point["label"])
        kind = "TREND"
    else:
        points.sort(key=lambda point: point["value"], reverse=plan.get("sort", "desc") != "asc")
        kind = "COUNTS" if op == "count" else "COMPARISON"
    points = points[:250]
    sort = plan.get("sort", "desc")
    extreme = points[0] if (types[group] == "date" or sort != "asc") else points[0]
    lowest = min(points, key=lambda point: point["value"])
    highest = max(points, key=lambda point: point["value"])
    chosen = lowest if op == "min" else highest
    op_label = "total" if op == "sum" else op
    title = f"{op_label.title()} {metric or 'rows'} by {group}"
    if op == "count":
        explanation = f"{extreme['label']} appears most often, with {fmt(extreme['value'])} rows. The chart counts records in each group."
    else:
        explanation = f"{chosen['label']} has the {'lowest' if op == 'min' else 'highest'} {op_label} {metric} at {fmt(chosen['value'])}."
        other = highest if op == "min" else lowest
        if other["label"] != chosen["label"]:
            explanation += f" {other['label']} is {'highest' if op == 'min' else 'lowest'} at {fmt(other['value'])}."
    return {"title": title, "type": kind, "metric": metric, "group": group, "operation": op, "points": points,
            "explanation": explanation, "note": f"{op.title()} calculated within each {group} group{'' if op == 'count' else f', using {metric}'}. Empty numeric values are skipped.",
            "footnote": f"Grouped by {group} · {len(rows):,} filtered source rows", "usedRows": len(rows), "filters": filters}


def localize_result(result, language):
    if language != "hi":
        return result
    result = dict(result)
    metric, group, op = result.get("metric"), result.get("group"), result.get("operation")
    if result.get("type") == "RELATIONSHIP":
        strength = "मजबूत" if abs(result.get("correlation", 0)) >= .7 else "मध्यम" if abs(result.get("correlation", 0)) >= .4 else "कमज़ोर"
        direction = "सकारात्मक" if result.get("correlation", 0) >= 0 else "नकारात्मक"
        result["explanation"] = f"{metric} और {result.get('second')} के बीच {strength} {direction} संबंध दिखता है। सहसंबंध {result.get('correlation', 0):.2f} है। यह केवल एक पैटर्न है, कारण का प्रमाण नहीं।"
        result["note"] = f"दोनों मान मौजूद होने वाली {result.get('usedRows', 0):,} पंक्तियों पर Pearson सहसंबंध।"
        result["footnote"] = f"हर बिंदु एक पंक्ति है · {result.get('usedRows', 0):,} पूरी जोड़ियाँ"
        return result
    if group:
        points = result.get("points", [])
        if points:
            highest = max(points, key=lambda point: point["value"])
            lowest = min(points, key=lambda point: point["value"])
            if op == "count":
                result["explanation"] = f"{highest['label']} में सबसे अधिक रिकॉर्ड हैं: {fmt(highest['value'])}। चार्ट हर समूह की पंक्तियाँ गिनता है।"
            elif op == "distinct":
                result["explanation"] = f"{highest['label']} में {metric} के {fmt(highest['value'])} अलग मान हैं।"
            else:
                focus = lowest if op == "min" else highest
                adjective = "सबसे कम" if op == "min" else "सबसे अधिक"
                measure = "औसत" if op == "average" else "माध्यिका" if op == "median" else "कुल"
                result["explanation"] = f"{focus['label']} में {metric} का {adjective} {measure} {fmt(focus['value'])} है।"
                other = highest if op == "min" else lowest
                if other["label"] != focus["label"]:
                    result["explanation"] += f" {other['label']} में यह {fmt(other['value'])} है।"
        action = {"sum": "कुल", "average": "औसत", "median": "माध्यिका", "count": "गिनती", "distinct": "अलग मानों की गिनती", "min": "न्यूनतम", "max": "अधिकतम"}.get(op, "कुल")
        result["title"] = f"{group} के अनुसार {metric} के अलग मान" if op == "distinct" else f"{group} के अनुसार {metric or 'पंक्तियों'} की {action}"
        result["note"] = f"हर {group} समूह में गणना की गई। खाली संख्यात्मक मान छोड़ दिए गए।"
        result["footnote"] = f"समूह: {group} · {result.get('usedRows', 0):,} फ़िल्टर की गई पंक्तियाँ"
    else:
        value = result.get("points", [{}])[0].get("value", 0)
        if op == "count":
            result["title"] = "पंक्तियों की संख्या"
            result["explanation"] = f"इस चयन में {fmt(value)} पंक्तियाँ हैं।"
        elif op == "distinct":
            result["title"] = f"{metric} के अलग मान"
            result["explanation"] = f"इस चयन में {metric} के {fmt(value)} अलग मान हैं।"
        else:
            action = {"sum": "कुल", "average": "औसत", "median": "माध्यिका", "min": "न्यूनतम", "max": "अधिकतम"}.get(op, "कुल")
            result["title"] = f"{metric} का {action}"
            result["explanation"] = f"{result.get('usedRows', 0):,} फ़िल्टर की गई पंक्तियों में {metric} का {action} {fmt(value)} है।"
        result["note"] = f"{result.get('usedRows', 0):,} पंक्तियों से गणना की गई। खाली या गैर-संख्यात्मक मान छोड़ दिए गए।"
        result["footnote"] = f"{result.get('usedRows', 0):,} फ़िल्टर की गई पंक्तियों पर आधारित"
    return result


class FieldnoteHandler(SimpleHTTPRequestHandler):
    server_version = "Fieldnote/2.0"

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, status, payload, extra_headers=()):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BYTES + 1_000_000:
            raise ValueError("Request is too large.")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _same_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        from urllib.parse import urlparse
        return urlparse(origin).netloc == self.headers.get("Host", "")

    def _current_user(self):
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie.get("fieldnote_session").value if cookie.get("fieldnote_session") else ""
        except Exception:
            return None
        if not token:
            return None
        with db_connect() as db:
            row = db.execute("SELECT username FROM sessions WHERE token_hash=? AND expires_at>?", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        return row["username"] if row else None

    def _owned_dataset(self, dataset_id, username):
        dataset = DATASETS.get(dataset_id)
        return dataset if dataset and dataset.get("owner") == username else None

    def do_GET(self):
        if self.path == "/api/status":
            return self._json(200, {"version": "2.1", "requiresAuth": True, "aiAvailable": bool(os.environ.get("OPENAI_API_KEY")), "aiModel": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), "xlsxAvailable": importlib_available("openpyxl"), "maxUploadBytes": MAX_BYTES, "maxRows": MAX_ROWS})
        if self.path == "/api/auth/me":
            username = self._current_user()
            return self._json(200 if username else 401, {"username": username} if username else {"error": "Sign in to continue."})
        if self.path.startswith("/api/dataset"):
            username = self._current_user()
            if not username:
                return self._json(401, {"error": "Sign in to continue."})
            from urllib.parse import parse_qs, urlparse
            dataset_id = parse_qs(urlparse(self.path).query).get("id", [""])[0]
            dataset = self._owned_dataset(dataset_id, username)
            if not dataset:
                return self._json(404, {"error": "Dataset not found. Upload it again to continue."})
            return self._json(200, summary(dataset))
        return super().do_GET()

    def do_POST(self):
        if not self._same_origin():
            return self._json(403, {"error": "Cross-origin requests are not accepted."})
        try:
            if self.path in ("/api/auth/register", "/api/auth/login"):
                payload = self._body_json()
                username = str(payload.get("username", "")).strip()
                password = str(payload.get("password", ""))
                if self.path.endswith("register"):
                    username_ok = re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", username)
                    email_ok = len(username) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", username)
                    if not (username_ok or email_ok):
                        return self._json(400, {"error": "Use a 3–64 character username or a valid email address."})
                    if len(password) < 8 or len(password) > 128:
                        return self._json(400, {"error": "Choose a password between 8 and 128 characters."})
                    salt = secrets.token_hex(16)
                    try:
                        with db_connect() as db:
                            db.execute("INSERT INTO users(username,salt,password_hash,created_at) VALUES(?,?,?,?)", (username, salt, password_hash(password, salt), int(time.time())))
                    except sqlite3.IntegrityError:
                        return self._json(409, {"error": "That username is already in use on this machine."})
                else:
                    with db_connect() as db:
                        user = db.execute("SELECT username,salt,password_hash FROM users WHERE username=? COLLATE NOCASE", (username,)).fetchone()
                    if not user or not hmac.compare_digest(user["password_hash"], password_hash(password, user["salt"])):
                        return self._json(401, {"error": "Username or password is incorrect."})
                    username = user["username"]
                token = secrets.token_urlsafe(32)
                expiry = int(time.time()) + SESSION_SECONDS
                with db_connect() as db:
                    db.execute("DELETE FROM sessions WHERE expires_at<=?", (int(time.time()),))
                    db.execute("INSERT INTO sessions(token_hash,username,expires_at) VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), username, expiry))
                cookie = f"fieldnote_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_SECONDS}"
                return self._json(200, {"username": username}, (("Set-Cookie", cookie),))
            if self.path == "/api/auth/logout":
                from http.cookies import SimpleCookie
                cookie = SimpleCookie(); cookie.load(self.headers.get("Cookie", ""))
                if cookie.get("fieldnote_session"):
                    token = cookie["fieldnote_session"].value
                    with db_connect() as db:
                        db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
                return self._json(200, {"ok": True}, (("Set-Cookie", "fieldnote_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"),))
            username = self._current_user()
            if not username:
                return self._json(401, {"error": "Sign in to continue."})
            if self.path == "/api/upload":
                return self._upload(username)
            if self.path == "/api/analyze":
                payload = self._body_json()
                dataset = self._owned_dataset(payload.get("datasetId"), username)
                if not dataset:
                    return self._json(404, {"error": "This dataset is no longer in the server session. Please upload it again."})
                language = "hi" if payload.get("language") == "hi" else "en"
                question = str(payload.get("question", ""))[:500]
                if language == "hi":
                    question = normalize_hindi_question(question)
                result = analyze(question, dataset, payload.get("filters", []), bool(payload.get("useAI")))
                result = localize_result(result, language)
                return self._json(200, result)
            if self.path == "/api/clean":
                payload = self._body_json()
                dataset = self._owned_dataset(payload.get("datasetId"), username)
                if not dataset:
                    return self._json(404, {"error": "Upload the dataset again first."})
                action = payload.get("action")
                if action == "duplicates":
                    dataset.setdefault("undo", []).append([row.copy() for row in dataset["rows"]])
                    seen, unique = set(), []
                    for row in dataset["rows"]:
                        key = tuple(row.get(h, "") for h in dataset["headers"])
                        if key not in seen:
                            seen.add(key); unique.append(row)
                    removed = len(dataset["rows"]) - len(unique); dataset["rows"] = unique
                    message = f"Removed {removed:,} duplicate rows."
                elif action == "empty":
                    dataset.setdefault("undo", []).append([row.copy() for row in dataset["rows"]])
                    old = len(dataset["rows"]); dataset["rows"] = [row for row in dataset["rows"] if all(str(row.get(h, "")).strip() for h in dataset["headers"])]
                    removed = old - len(dataset["rows"]); message = f"Removed {removed:,} rows with one or more empty cells."
                elif action == "undo":
                    if not dataset.get("undo"):
                        return self._json(400, {"error": "There are no cleanup changes to undo."})
                    dataset["rows"] = dataset["undo"].pop(); message = "Last cleanup change undone."
                else:
                    dataset["undo"].pop()
                    return self._json(400, {"error": "Unknown cleanup action."})
                result = summary(dataset); result["message"] = message
                return self._json(200, result)
            if self.path == "/api/types":
                payload = self._body_json()
                dataset = self._owned_dataset(payload.get("datasetId"), username)
                column, type_name = payload.get("column"), payload.get("type")
                if not dataset or column not in dataset["headers"]:
                    return self._json(404, {"error": "That column isn't available in the current dataset."})
                if type_name not in ("number", "date", "category"):
                    return self._json(400, {"error": "Choose number, date, or category for a column type."})
                dataset.setdefault("typeOverrides", {})[column] = type_name
                result = summary(dataset); result["message"] = f"{column} is now treated as {type_name}."
                return self._json(200, result)
            return self._json(404, {"error": "API route not found."})
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        except RuntimeError as exc:
            return self._json(502, {"error": str(exc)})
        except Exception as exc:
            print(f"Request error: {exc}", file=sys.stderr)
            return self._json(500, {"error": "Something went wrong while handling that request. The file is still private to this local app; try again."})

    def _upload(self, username):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BYTES + 1_000_000:
            return self._json(413, {"error": "Choose a file under 25 MB."})
        raw = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        envelope = b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw
        message = BytesParser(policy=default).parsebytes(envelope)
        file_name, payload = None, None
        for part in message.iter_parts():
            if part.get_content_disposition() == "form-data" and part.get_param("name", header="content-disposition") == "file":
                file_name = Path(part.get_filename() or "dataset.csv").name
                payload = part.get_payload(decode=True)
                break
        if not payload:
            return self._json(400, {"error": "Choose a CSV or Excel file to upload."})
        if len(payload) > MAX_BYTES:
            return self._json(413, {"error": "This file is over 25 MB. Export fewer rows or columns and try again."})
        suffix = Path(file_name).suffix.lower()
        if suffix == ".csv":
            headers, rows = read_csv_bytes(payload)
        elif suffix in (".xlsx", ".xlsm"):
            headers, rows = parse_xlsx(payload)
        else:
            return self._json(415, {"error": "Choose a .csv or .xlsx file. Older .xls workbooks are not supported yet."})
        dataset_id = secrets.token_urlsafe(18)
        dataset = {"id": dataset_id, "fileName": file_name, "headers": headers, "rows": rows, "undo": [], "owner": username}
        while len(DATASETS) >= 3:
            DATASETS.pop(next(iter(DATASETS)))
        DATASETS[dataset_id] = dataset
        return self._json(201, summary(dataset))

    def do_DELETE(self):
        if not self._same_origin():
            return self._json(403, {"error": "Cross-origin requests are not accepted."})
        username = self._current_user()
        if not username:
            return self._json(401, {"error": "Sign in to continue."})
        if self.path.startswith("/api/dataset"):
            from urllib.parse import parse_qs, urlparse
            dataset_id = parse_qs(urlparse(self.path).query).get("id", [""])[0]
            dataset = self._owned_dataset(dataset_id, username)
            if dataset:
                DATASETS.pop(dataset_id, None)
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "API route not found."})

    def log_message(self, format_string, *args):
        if args and str(args[1]).startswith("/api"):
            super().log_message(format_string, *args)


def importlib_available(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def load_dotenv():
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def main():
    load_dotenv()
    initialize_database()
    parser = argparse.ArgumentParser(description="Run Fieldnote's local analysis app")
    parser.add_argument("--host", default="127.0.0.1", help="Network interface (default: localhost only)")
    parser.add_argument("--port", type=int, default=8001, help="Preferred port (default: 8001; nearby ports are tried automatically if needed)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the app automatically")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    handler = partial(FieldnoteHandler, directory=str(PROJECT_DIR))
    server = None
    last_error = None
    last_port = min(args.port + 30, 65535)
    ports_to_try = [0] if args.port == 0 else range(args.port, last_port + 1)
    for port in ports_to_try:
        try:
            server = ThreadingHTTPServer((args.host, port), handler)
            if port != args.port:
                print(f"Port {args.port} is unavailable; using port {port} instead.")
            break
        except OSError as exc:
            last_error = exc
    if server is None:
        raise SystemExit(f"Could not start Fieldnote on ports {args.port}–{last_port}: {last_error}")
    actual_port = server.server_address[1]
    url = f"http://{args.host}:{actual_port}"
    print("Fieldnote 2.1 is ready.")
    print(f"Open {url} in your browser. Press Ctrl+C to stop.")
    print("Datasets are held in memory for this run and cleared when the server stops.")
    print("AI question interpretation is enabled." if os.environ.get("OPENAI_API_KEY") else "AI is off. Built-in question matching is available.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFieldnote stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
