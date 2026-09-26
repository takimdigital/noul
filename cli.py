#!/usr/bin/env python3
"""noul CLI — the local abstention gate. stdlib-only."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul import decide, doctor, ENGINES, load_pack, list_packs, show_pack, run_control, batch_decide, ordinal_tier, __version__


def cmd_check(args):
    """Run a single check."""
    state = args.doc
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            state = f.read()
    pack = load_pack(args.pack)
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {args.ask}"
    resp = decide(state, {qname: {"type": "noul", "instructions": instructions}}, engine=args.engine)
    ans = resp["answers"][qname]
    noul = ans.get("noul", 0.0)
    label = q["label_true"] if noul >= 0.5 else q["label_false"]
    out = {
        "label": label,
        "noul": round(noul, 3),
        "engine": args.engine,
        "latency_ms": resp["_noul_latency_ms"],
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"  {label:<16} noul={noul:.3f}   {resp['_noul_latency_ms']:.1f} ms   engine={args.engine}")
    # log
    log_path = os.path.expanduser("~/.noul/log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"label": label, "noul": noul, "engine": args.engine, "latency_ms": resp["_noul_latency_ms"], "question": args.ask}) + "\n")
    return 0


def cmd_doctor(args):
    results = doctor()
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for name, info in results.items():
        if info.get("reachable"):
            print(f"  {name:<10} reachable  {info['latency_ms']:.1f} ms  model={info['model']}  enforce={info['enforce']}")
        else:
            print(f"  {name:<10} UNREACHABLE  {info.get('reason', '')}")


def cmd_pack(args):
    if args.pack_command == "show":
        print(show_pack(args.pack))
    elif args.pack_command == "list":
        packs = list_packs()
        print("  " + ", ".join(packs) if packs else "  (no packs)")
    elif args.pack_command == "control":
        result = run_control(args.pack, args.engine)
        if args.json:
            print(json.dumps(result, indent=2))
            return
        print(f"  controls run: {result['controls_run']}  all_pass: {result['all_pass']}")
        for r in result["results"]:
            status = "PASS" if r.get("PASS") else "FAIL"
            print(f"    [{status}] {r['control']}: vague={r.get('vague_noul')} contrast={r.get('contrast_noul')} gap={r.get('gap')}")


def cmd_eval(args):
    from noul.eval import eval_card
    card = eval_card()
    print(json.dumps(card, indent=2))


def cmd_label(args):
    from noul.eval import add_label
    correct = ' '.join(args.correct).upper()
    add_label(args.index, correct)
    print(f"  labeled check #{args.index} = {correct}")


def cmd_tally(args):
    from noul.eval import load_log, labels_count
    log = load_log()
    n = len(log)
    labels_n = labels_count()
    if not log:
        print("  no checks yet. run `noul check` first.")
        return
    ans_count = sum(1 for l in log if l["label"] == "ANSWERABLE")
    not_count = n - ans_count
    avg_ms = sum(l["latency_ms"] for l in log) / n
    print(f"  checks: {n}   ANSWERABLE: {ans_count}   NOT ANSWERABLE: {not_count}   avg: {avg_ms:.1f}ms")
    print(f"  labels: {labels_n}/100")
    if labels_n < 100:
        print(f"  {100 - labels_n} more labels until eval unlocks")


def cmd_mcp(args):
    from noul.mcp import print_config
    print(print_config(args.host))


def cmd_batch(args):
    from noul.batch import load_batch_input, save_batch_results
    items = load_batch_input(args.input)
    doc = ""
    if args.doc:
        doc = args.doc
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            doc = f.read()
    results = batch_decide(items, doc=doc, pack=args.pack, engine=args.engine, ordinal=args.ordinal)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"  ERROR: {r['error']}")
            else:
                tier = f" [{r['tier']}]" if args.ordinal else ""
                print(f"  {r['verdict']:<16} noul={r['noul']:.3f}{tier}  {r['latency_ms']:.1f}ms  {r['question'][:60]}")
    if args.output:
        save_batch_results(results, args.output)
        print(f"  → saved {len(results)} results to {args.output}")
    return 0


def main():
    p = argparse.ArgumentParser(prog="noul", description="noul — the local abstention gate")
    p.add_argument("--version", action="version", version=f"noul {__version__}")
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    c_check = sub.add_parser("check", help="Run a single answerability check")
    c_check.add_argument("--doc", default="", help="Context text (or use --file)")
    c_check.add_argument("--file", help="Read context from file")
    c_check.add_argument("--ask", required=True, help="The question")
    c_check.add_argument("--pack", default="answerability")
    c_check.add_argument("--engine", default="kev")
    c_check.set_defaults(func=cmd_check)

    c_doc = sub.add_parser("doctor", help="Check engine status")
    c_doc.set_defaults(func=cmd_doctor)

    c_pack = sub.add_parser("pack", help="Pack operations")
    c_pack.add_argument("pack_command", choices=["show", "list", "control"])
    c_pack.add_argument("--pack", default="answerability")
    c_pack.add_argument("--engine", default="kev")
    c_pack.set_defaults(func=cmd_pack)

    c_tally = sub.add_parser("tally", help="Show usage tally")
    c_tally.set_defaults(func=cmd_tally)

    c_eval = sub.add_parser("eval", help="Evaluate (refused until >=100 labels)")
    c_eval.add_argument("--pack", default="answerability")
    c_eval.set_defaults(func=cmd_eval)

    c_label = sub.add_parser("label", help="Label a check from the log")
    c_label.add_argument("--index", type=int, required=True)
    c_label.add_argument("--correct", required=True, nargs='+',
                         help="The correct label (ANSWERABLE or 'NOT ANSWERABLE')")
    c_label.set_defaults(func=cmd_label)

    c_mcp = sub.add_parser("mcp", help="Print MCP config block")
    c_mcp.add_argument("--host", default="lmstudio", choices=["lmstudio", "vscode", "claude", "openwebui"])
    c_mcp.set_defaults(func=cmd_mcp)

    c_batch = sub.add_parser("batch", help="Batch check multiple questions against a doc")
    c_batch.add_argument("--input", required=True, help="Input file: .csv, .tsv, or .jsonl with 'question' column(s)")
    c_batch.add_argument("--doc", default="", help="Shared context text (or use --file)")
    c_batch.add_argument("--file", help="Read shared context from file")
    c_batch.add_argument("--pack", default="answerability")
    c_batch.add_argument("--engine", default="kev")
    c_batch.add_argument("--ordinal", action="store_true", help="Add ordinal tier: definite_yes / maybe / definite_no")
    c_batch.add_argument("--output", help="Save results as JSONL")
    c_batch.add_argument("--json", action="store_true", help="Output as JSON array")
    c_batch.set_defaults(func=cmd_batch)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
