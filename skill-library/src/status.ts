// `status`: a read-only, structured project progress snapshot (port of sdlc/status.py).

import { DELIVERY_STATUSES, DOC_CATEGORIES, DOC_STATUSES, type Diagnostic, Outcome, cmpId, idSortKey } from "./model.js";
import { type Doc, type Project, scanDocuments } from "./project.js";
import { cmpTuple, sortedStrings, strip } from "./pyfmt.js";
import * as technical from "./technical.js";
import { validate } from "./validate.js";

const REFERENCE_CODES = ["broken-link", "unknown-requirement", "covers-unknown", "retired-reference", "covers-source-not-linked", "retired-id-in-use"];

const brief = (d: Diagnostic) => ({ code: d.code, message: d.message, path: d.path, id: d.id, line: d.line });

/** Current (non-superseded) verification runs per Story ID. */
function currentRuns(docs: Doc[]): Map<string, technical.Rec[]> {
  const out = new Map<string, technical.Rec[]>();
  const ac = new Map<string, number | null>();
  for (const d of docs) if (d.isStory) ac.set(d.id, technical.acceptanceCriteriaCount(technical.sections(d.text)));
  for (const doc of docs) {
    if (doc.category !== "TEST" || !doc.valid) continue;
    const [recs] = technical.checkVerificationRuns(doc.rel, doc.id, technical.sections(doc.text), ac);
    for (const r of recs) {
      if (technical.isSuperseded(r)) continue;
      const key = strip(r.fields["story"] ?? "");
      const list = out.get(key);
      if (list) list.push(r); else out.set(key, [r]);
    }
  }
  return out;
}

export function buildStatus(project: Project): Outcome {
  const [docs] = scanDocuments(project);
  const check = validate(project);
  const diags = check.diagnostics;
  const valid = docs.filter((d) => d.valid);
  const bySev = (s: string) => diags.filter((d) => d.severity === s);

  const summary = (check.result as { summary: unknown; documents: number });
  const health = {
    ok: bySev("error").length === 0,
    summary: summary.summary,
    documents: summary.documents,
    errors: bySev("error").map(brief),
    warnings: bySev("warning").map(brief),
    stale_maps: sortedStrings(new Set(diags.filter((d) => ["stale-map", "map-markers", "missing-map"].includes(d.code)).map((d) => d.path as string))),
    broken_references: bySev("error").filter((d) => REFERENCE_CODES.includes(d.code)).map(brief),
  };

  const inventory: Record<string, unknown> = {};
  for (const cat of DOC_CATEGORIES) {
    const mine = valid.filter((d) => d.category === cat);
    const invalid = docs.filter((d) => !d.valid && d.category === cat).length;
    const byStatus: Record<string, number> = {};
    for (const s of DOC_STATUSES) byStatus[s] = mine.filter((d) => d.meta["status"] === s).length;
    inventory[cat] = { total: mine.length + invalid, by_status: byStatus, invalid };
  }

  const stories = valid.filter((d) => d.isStory).sort((a, b) => cmpId(a.id, b.id));
  const delivery: Record<string, unknown[]> = {};
  for (const s of DELIVERY_STATUSES) delivery[s] = [];
  for (const st of stories) delivery[st.meta["delivery_status"] as string]!.push({ id: st.id, title: st.title, status: st.meta["status"] ?? null, path: st.rel });

  const unresolvedTbd = stories.filter((st) => technical.unresolvedTbdBullets(technical.sections(st.text)) > 0).map((st) => st.id);
  const traceability = {
    uncovered_requirements: bySev("notice").filter((d) => d.code === "requirement-uncovered").map((d) => d.id),
    standalone_stories: bySev("notice").filter((d) => d.code === "story-no-coverage").map((d) => d.id),
    invalid_references: bySev("error").filter((d) => REFERENCE_CODES.includes(d.code)).map(brief),
    unresolved_tbd: unresolvedTbd,
  };

  const runs = currentRuns(docs);
  const attention: { kind: string; id: string | null; message: string; path: string | null }[] = [];
  const add = (kind: string, id: string | null, message: string, path: string | null = null) => attention.push({ kind, id, message, path });

  for (const d of bySev("error")) add("validation-error", d.id, `${d.message} (${d.code})`, d.path);
  for (const sid of unresolvedTbd) add("unresolved-acceptance", sid, "has unresolved acceptance behavior (TBD) — decide it or accept the residual explicitly", stories.find((s) => s.id === sid)!.rel);
  for (const st of stories) {
    const ds = st.meta["delivery_status"];
    if (ds === "Ready") add("ready-to-implement", st.id, "Ready — can be implemented (implement-story)", st.rel);
    else if (ds === "In Progress") add("in-progress", st.id, "In Progress — implementation underway", st.rel);
    else if (ds === "Implemented") {
      const mine = runs.get(st.id) ?? [];
      const seen = new Map<string, [string, string]>();
      for (const r of mine) {
        const result = strip(r.fields["result"] ?? "?");
        if (["failed", "blocked", "not-run"].includes(result)) seen.set(`${r.id}\u0000${result}`, [r.id, result]);
      }
      const bad = [...seen.values()].sort((a, b) => cmpTuple(a, b));
      if (bad.length) {
        add("verification-problem", st.id, "current verification run(s) not passed: " + bad.map(([i, res]) => `${i} ${res}`).join(", ") + " — rework (implement-story) or resolve, then re-verify", st.rel);
      }
      add("awaiting-verification", st.id, "Implemented — awaiting verification (verify-story)", st.rel);
    }
  }
  for (const d of valid.filter((x) => x.meta["status"] === "In Review").sort((a, b) => cmpId(a.id, b.id))) {
    add("in-review", d.id, `${d.category} document is In Review — awaiting a human decision`, d.rel);
  }
  const rank: Record<string, number> = { "validation-error": 0, "verification-problem": 1, "unresolved-acceptance": 2, "awaiting-verification": 3, "in-progress": 4, "ready-to-implement": 5, "in-review": 6 };
  attention.sort((a, b) => cmpTuple([rank[a.kind]!, ...(a.id ? idSortKey(a.id) : [99, 0, 0])], [rank[b.kind]!, ...(b.id ? idSortKey(b.id) : [99, 0, 0])]));

  return new Outcome(0, { health, inventory, delivery, traceability, attention, empty: docs.length === 0 }, []);
}
