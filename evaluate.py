"""Exercise supplied cases offline, or collect raw Gemini model results."""
import argparse
import json
from pathlib import Path

from study_pack import ENGINE_NAME, generate, gemini, preview

ROOT = Path(__file__).resolve().parent

def run(mode, versions):
    cases = json.loads((ROOT / "evaluation/cases.json").read_text(encoding="utf-8"))
    records = []
    for case in cases:
        for version in (["offline"] if mode == "offline" else versions):
            record = {"test": case["id"], "version": version, "expectation": case["expectation"], "calls": []}
            def logged_model(stage, payload, schema=None):
                call = {"stage": stage, "input": payload, "schema": schema}
                record["calls"].append(call)
                call["output"] = gemini(stage, payload, schema)
                return call["output"]

            try:
                record["output"] = (preview(case["notes"]) if mode == "offline"
                                    else generate(case["notes"], version, logged_model))
                record["status"] = "produced"
            except (ValueError, OSError, KeyError, TypeError) as error:
                record["status"] = "rejected or failed"
                record["message"] = str(error)
            records.append(record)
    return {"model": ENGINE_NAME if mode == "ai" else None, "mode": mode, "records": records}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "ai"), default="offline")
    parser.add_argument("--versions", nargs="+", choices=("v1", "v2", "v3"), default=["v1", "v2", "v3"])
    parser.add_argument("--output", type=Path, default=Path("results.json"))
    args = parser.parse_args()
    result = run(args.mode, args.versions)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(result['records'])} records to {args.output}")
