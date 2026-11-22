"""NeuralNotes prompt pipeline using Google Gemini."""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
ENGINE_NAME = f"Google Gemini · {MODEL}"
MAX_CHARS = 12000

def array(items, limit):
    return {"type": "array", "items": items, "maxItems": limit}

def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields),
            "additionalProperties": False}

STRING = {"type": "string", "minLength": 1}
REFS = {**array(STRING, 6), "minItems": 1}
EXTRACT = obj(title=STRING, claims=array(obj(quote=STRING, ref=STRING), 12))
PACK = obj(title=STRING, summary=array(obj(text=STRING, refs=REFS), 5),
           terms=array(obj(term=STRING, definition=STRING, refs=REFS), 8),
           questions=array(obj(question=STRING, answer=STRING, refs=REFS), 6),
           warnings=array(STRING, 6))

def source_lines(notes):
    notes = notes.strip()
    if len(notes) > MAX_CHARS:
        raise ValueError(f"Limit notes to {MAX_CHARS:,} characters.")
    if len(re.findall(r"[^\W\d_]+", notes)) < 4:
        raise ValueError("Enter at least four words of lecture notes.")
    lines = []
    for paragraph in notes.splitlines():
        lines.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", paragraph) if part.strip())
    return {f"L{i}": line for i, line in enumerate(lines, 1)}

def validate(value, schema):
    kind = schema["type"]
    if kind == "string":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("The model returned a missing or invalid text field.")
    elif kind == "array":
        if not isinstance(value, list) or not schema.get("minItems", 0) <= len(value) <= schema["maxItems"]:
            raise ValueError("The model returned an invalid list length.")
        for item in value:
            validate(item, schema["items"])
    elif kind == "object":
        fields = schema["properties"]
        if not isinstance(value, dict) or value.keys() != fields.keys():
            raise ValueError("The model returned unexpected or missing fields.")
        for key, field in fields.items():
            validate(value[key], field)
    return value

def check_pack(pack, lines):
    validate(pack, PACK)
    for field in ("summary", "terms", "questions"):
        if any(ref not in lines for item in pack[field] for ref in item["refs"]):
            raise ValueError("The model returned a source ID outside the allowed evidence.")
    return pack

def gemini_schema(schema):
    """Keep the request schema to the JSON Schema subset used by Gemini."""
    kind = schema["type"]
    result = {"type": kind}
    if kind == "object":
        result["properties"] = {
            name: gemini_schema(field)
            for name, field in schema["properties"].items()
        }
        result["required"] = schema["required"]
    elif kind == "array":
        result["items"] = gemini_schema(schema["items"])
    return result

def gemini(stage, payload, schema=None):
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "Google Gemini API key is missing. Add GOOGLE_API_KEY to the project .env file."
        )

    prompt_path = ROOT / "prompts" / f"{stage}.txt"
    try:
        system_prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ValueError(f"Could not read Gemini prompt {prompt_path.name}: {error}") from error

    request = {
        "model": MODEL,
        "input": system_prompt + "\n\nUser JSON:\n" + json.dumps(payload, ensure_ascii=False),
    }
    if schema:
        request["response_format"] = {
            "type": "text",
            "mime_type": "application/json",
            "schema": gemini_schema(schema),
        }

    client = genai.Client(api_key=api_key)
    try:
        response = client.interactions.create(**request)
    except genai_errors.APIError as error:
        raise ValueError(f"Gemini API request failed: {error}") from error
    finally:
        client.close()

    content = response.output_text
    if not content or not content.strip():
        raise ValueError("Gemini returned an empty response.")
    if not schema:
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid JSON for a structured response.") from error

def generate(notes, version="v3", model=None):
    lines = source_lines(notes)
    if model is None:
        model = gemini
    if version == "v1":
        return model("v1", {"lines": lines})
    if version == "v2":
        return check_pack(model("v2", {"lines": lines}, PACK), lines)
    if version != "v3":
        raise ValueError("Unknown prompt version.")
    extraction = validate(model("p1", {"lines": lines}, EXTRACT), EXTRACT)
    claims = [claim for claim in extraction["claims"]
              if claim["quote"] in lines.get(claim["ref"], "")]
    if not claims:
        return empty_pack("No verifiable study material found.")
    allowed = {claim["ref"]: lines[claim["ref"]] for claim in claims}
    draft = validate(model("p2", {"lines": allowed, "claims": claims}, PACK), PACK)
    return check_pack(model("p3", {"lines": allowed, "draft": draft}, PACK), allowed)

def empty_pack(message):
    return {"title": "Study pack", "summary": [], "terms": [], "questions": [], "warnings": [message]}

def preview(notes):
    """Extractive offline preview. It intentionally makes zero model calls."""
    lines = source_lines(notes)
    pack = empty_pack("Offline preview uses simple text patterns. AI mode handles synthesis and review.")
    pack["title"] = "Offline study pack"
    for ref, line in list(lines.items())[:5]:
        pack["summary"].append({"text": line, "refs": [ref]})
        match = re.fullmatch(r"(.{2,55}?)\s+(?:is|are|means|refers to)\s+(.+)", line)
        if match:
            term, definition = match.groups()
            pack["terms"].append({"term": term, "definition": definition, "refs": [ref]})
            pack["questions"].append({"question": f"How do the notes define {term}?",
                                      "answer": definition, "refs": [ref]})
    return pack

def markdown(pack, show_answers=True):
    sections = [f"# {pack['title']}"]
    for label, rows, fields in (
        ("Summary", pack["summary"], ("text",)),
        ("Key terms", pack["terms"], ("term", "definition")),
        ("Practice questions", pack["questions"], ("question", "answer") if show_answers else ("question",)),
    ):
        sections.append("## " + label)
        sections.extend("- " + " — ".join(row[field] for field in fields)
                        + " [" + ", ".join(row["refs"]) + "]" for row in rows)
        if not rows:
            sections.append("No supported items.")
    if pack["warnings"]:
        sections.append("## Notes")
        sections.extend("- " + warning for warning in pack["warnings"])
    return "\n\n".join(sections) + "\n"
