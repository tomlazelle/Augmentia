// `publish-preview` / `publish-apply`: GitHub Issues publication with a mandatory preview-and-confirm gate (port of sdlc/publish.py).
//
//  * buildPreview is offline and read-only: it renders exactly what would be published and returns a `digest` over that content.
//  * applyPublication mutates only when the supplied digest equals the digest of a fresh preview of the current files, then
//    publishes exactly the previewed content through the provider boundary.
//  * Local Markdown stays authoritative: publishing appends a non-material `## Publication` record to the Story.

import crypto from "node:crypto";
import path from "node:path";
import * as frontmatter from "./frontmatter.js";
import { AmbiguousResult, GitHubCli, type Provider, ProviderError, redact } from "./github.js";
import { REF_SECTIONS } from "./markdown.js";
import { Diagnostic, FILENAME_RE, Outcome, categoryOf, cmpId, idKind } from "./model.js";
import * as publication from "./publication.js";
import { type Doc, type Project, scanDocuments } from "./project.js";
import { canonicalJson, cmpStr, cmpTuple, pyErrorString, pyStr, repr, today } from "./pyfmt.js";
import * as technical from "./technical.js";
import { validate } from "./validate.js";

const EXCLUDED_SECTIONS = ["references", "implementation record", "review record", "publication"];
const ALLOWED_KEYS = new Set(["provider", "repository"]);
const cutText = (s: string, n: number): string => [...s].slice(0, n).join("");

// --- configuration ---------------------------------------------------------------------------------

export function loadPublishing(project: Project): [{ provider: string; repository: string } | null, Diagnostic[]] {
  const rel = ".sdlc/config.md";
  const cfg = project.config?.["publishing"] as Record<string, unknown> | undefined;
  if (!cfg || (typeof cfg === "object" && Object.keys(cfg).length === 0)) {
    return [null, [new Diagnostic("error", "publishing-config-missing", "no publishing configuration: add 'publishing: {provider: github, repository: owner/name}' to .sdlc/config.md (never put credentials there)", rel)]];
  }
  const diags: Diagnostic[] = [];
  const provider = cfg["provider"];
  const repository = cfg["repository"];
  if (provider !== "github") diags.push(new Diagnostic("error", "publishing-unsupported-provider", `publishing.provider must be 'github' (got ${repr(provider)}); other providers are not supported`, rel));
  if (typeof repository !== "string" || !publication.REPO_RE.test(repository)) diags.push(new Diagnostic("error", "publishing-config-invalid", `publishing.repository must be 'owner/name' (got ${repr(repository)})`, rel));
  const unknown = Object.keys(cfg).filter((k) => !ALLOWED_KEYS.has(k)).sort(cmpStr);
  if (unknown.length) diags.push(new Diagnostic("warning", "unknown-publishing-key", `ignored publishing keys: ${unknown.join(", ")}`, rel));
  if (diags.some((d) => d.severity === "error")) return [null, diags];
  return [{ provider: provider as string, repository: repository as string }, diags];
}

// --- Issue rendering -------------------------------------------------------------------------------

function refLabel(href: string): string {
  const name = path.posix.basename(href);
  const m = FILENAME_RE.exec(name);
  return m ? m[1]! : name;
}

/** (title, body) for a Story: the Story's own text verbatim minus local/operational sections and the H1; TBDs are never dropped. */
export function renderIssue(doc: Doc): [string, string] {
  const text = doc.text.replaceAll("\r\n", "\n");
  const lines = text.split("\n");
  const [, bodyStart] = frontmatter.split(text);
  const drop = new Set<number>();
  for (let i = 0; i < bodyStart; i++) drop.add(i);
  for (const sec of technical.sections(text)) {
    if (sec.level === 2 && EXCLUDED_SECTIONS.includes(sec.title.toLowerCase())) for (let i = sec.line - 1; i < sec.end; i++) drop.add(i);
    else if (sec.level === 1) drop.add(sec.line - 1);
  }
  let kept = lines.filter((_, i) => !drop.has(i)).join("\n").replace(/^\n+|\n+$/g, "");
  kept = kept.replace(/\n{3,}/g, "\n\n");

  const head = [`> Published from local Story **${doc.id}**. The local Markdown file (\`${doc.rel}\`) is authoritative; edits to this Issue are not imported back.`, ""];
  head.push(`**Purpose:** ${typeof doc.meta["purpose"] === "string" ? doc.meta["purpose"] : pyStr(doc.meta["purpose"] ?? null)}`);
  const covers = doc.covers.length ? doc.covers.map((c) => `\`${c}\``).join(", ") : "none — standalone Story";
  head.push(`**Covers:** ${covers}`);
  for (const section of REF_SECTIONS) {
    const labels = [...new Set(doc.parsed.refs.filter((r) => r.section === section && r.href).map((r) => refLabel(r.href!)))]
      .sort((a, b) => cmpId(a, b) || cmpStr(a, b)); // ties among non-ID names: code-point order (Python's set order is not deterministic)
    if (labels.length) head.push(`**${section}:** ${labels.join(", ")}`);
  }
  return [`[${doc.id}] ${doc.title}`, head.join("\n") + (kept ? "\n\n" + kept : "") + "\n"];
}

function warningsFor(doc: Doc, secs: technical.Section[]): Diagnostic[] {
  const out: Diagnostic[] = [];
  const warn = (sev: "warning" | "notice", code: string, msg: string) => out.push(new Diagnostic(sev, code, msg, doc.rel, doc.id));
  const status = doc.meta["status"];
  if (status !== "Approved") warn("warning", "story-not-approved", `document status is ${status}, not Approved; the Issue will show the current text`);
  const tbd = technical.unresolvedTbdBullets(secs);
  if (tbd) warn("warning", "unresolved-acceptance", `${tbd} unresolved acceptance behavior (TBD) item(s); they are included in the Issue as written`);
  if (technical.acceptanceCriteriaCount(secs) === 0) warn("warning", "no-acceptance-criteria", "the Story has no numbered acceptance criteria");
  const excluded = new Set<number>();
  for (const sec of secs) if (sec.level === 2 && EXCLUDED_SECTIONS.includes(sec.title.toLowerCase())) for (let i = sec.line; i <= sec.end; i++) excluded.add(i);
  const relative = [...new Set(doc.parsed.links.filter(([line]) => !excluded.has(line)).map(([, href]) => href))].sort(cmpStr);
  if (relative.length) warn("warning", "relative-links", `body contains relative link(s) that will not resolve on GitHub: ${relative.slice(0, 5).join(", ")}`);
  if (doc.covers.length === 0) warn("notice", "story-no-coverage", "standalone Story: covers is empty (publishable)");
  return out;
}

// --- preview ---------------------------------------------------------------------------------------

export interface StoryItem {
  id: string; path: string | null; title: string | null; issue_title: string | null; issue_body: string | null; labels: string[];
  known_publication: Record<string, unknown> | null; other_publications: Record<string, unknown>[]; action: "create" | "skip" | "blocked"; blockers: string[]; warnings: string[];
}

function digestOf(provider: string, repository: string, stories: StoryItem[]): string {
  const payload = { provider, repository, stories: stories.map((s) => ({ id: s.id, action: s.action, title: s.issue_title, body: s.issue_body, known: s.known_publication })) };
  return "sha256:" + crypto.createHash("sha256").update(canonicalJson(payload), "utf8").digest("hex");
}

function normaliseSelection(raw: string[]): [string[], Diagnostic[]] {
  const diags: Diagnostic[] = [];
  const out: string[] = [];
  for (const item of raw) {
    if (idKind(item) !== "document" || categoryOf(item) !== "US") diags.push(new Diagnostic("error", "bad-selection", `${repr(item)} is not a Story ID (expected e.g. US-001)`, null, item));
    else if (!out.includes(item)) out.push(item);
  }
  if (raw.length === 0) diags.push(new Diagnostic("error", "no-selection", "name the Stories to publish; nothing is published by default"));
  return [out.sort(cmpId), diags];
}

const pubDict = (p: publication.Publication) => ({ id: p.id, date: p.date, provider: p.provider, repository: p.repository, issue: p.issue, url: p.url });

export function buildPreview(project: Project, selection: string[]): Outcome {
  let [ids, diags] = normaliseSelection(selection);
  const [config, cfgDiags] = loadPublishing(project);
  diags = [...diags, ...cfgDiags];
  if (config === null || diags.some((d) => d.severity === "error")) {
    return new Outcome(diags.some((d) => d.code === "bad-selection" || d.code === "no-selection") ? 2 : 1, {}, diags);
  }

  const [docs] = scanDocuments(project);
  const byId = new Map<string, Doc[]>();
  for (const d of docs) { const l = byId.get(d.id); if (l) l.push(d); else byId.set(d.id, [d]); }
  const projectDiags = validate(project).diagnostics;
  const otherErrors = projectDiags.filter((d) => d.severity === "error");

  const stories: StoryItem[] = [];
  for (const sid of ids) {
    const matches = (byId.get(sid) ?? []).filter((d) => d.isStory);
    const item: StoryItem = { id: sid, path: null, title: null, issue_title: null, issue_body: null, labels: [], known_publication: null, other_publications: [], action: "blocked", blockers: [], warnings: [] };
    stories.push(item);
    if (matches.length === 0) {
      diags.push(new Diagnostic("error", "story-not-found", `no Story ${sid} exists`, null, sid));
      item.blockers.push("story-not-found");
      continue;
    }
    const doc = matches[0]!;
    item.path = doc.rel;
    item.title = doc.title;
    const mine = projectDiags.filter((d) => d.severity === "error" && d.path === doc.rel);
    if (matches.length > 1) mine.push(new Diagnostic("error", "duplicate-id", `${sid} is used by more than one document`, doc.rel, sid));
    if (mine.length) {
      for (const d of mine) {
        diags.push(new Diagnostic("error", "story-invalid", `${d.message} (${d.code})`, doc.rel, sid, d.line));
        item.blockers.push(d.code);
      }
      continue;
    }
    const secs = technical.sections(doc.text);
    let [pubs, pubDiags] = publication.parse(doc.rel, sid, secs);
    if (pubDiags.length) { // an unreadable record could hide a prior publication: block rather than risk a duplicate
      diags.push(...pubDiags.map((d) => new Diagnostic("error", "story-invalid", d.message, doc.rel, sid, d.line)));
      item.blockers.push("publication-invalid");
      continue;
    }
    const [title, body] = renderIssue(doc);
    item.issue_title = title;
    item.issue_body = body;
    for (const w of warningsFor(doc, secs)) { diags.push(w); item.warnings.push(w.code); }
    const same = pubs.filter((p) => p.provider === config.provider && p.repository === config.repository);
    const elsewhere = pubs.filter((p) => !same.includes(p));
    item.other_publications = elsewhere.map(pubDict);
    for (const p of elsewhere) {
      diags.push(new Diagnostic("notice", "published-elsewhere", `also published to ${p.provider}:${p.repository}${p.issue}; that does not affect publication to ${config.repository}`, doc.rel, sid));
    }
    pubs = same;
    if (pubs.length) {
      const last = pubs[pubs.length - 1]!;
      item.known_publication = pubDict(last);
      item.action = "skip";
      diags.push(new Diagnostic("notice", "already-published", `already published as ${last.repository}${last.issue}; nothing will be created (M5 does not update existing Issues)`, doc.rel, sid));
    } else item.action = "create";
  }

  const blocked = stories.filter((s) => s.action === "blocked").map((s) => s.id);
  const creating = stories.filter((s) => s.action === "create").map((s) => s.id);
  if (otherErrors.length && blocked.length === 0) {
    const selectedPaths = new Set(stories.map((s) => s.path));
    const unrelated = otherErrors.filter((d) => !selectedPaths.has(d.path));
    if (unrelated.length) diags.push(new Diagnostic("warning", "project-has-errors", `the project has ${unrelated.length} other validation error(s) unrelated to the selected Stories; run validate`, null));
  }
  const rank = { error: 0, warning: 1, notice: 2 } as const;
  const result = {
    provider: config.provider, repository: config.repository, stories, will_create: creating, blocked, can_apply: creating.length > 0 && blocked.length === 0,
    digest: digestOf(config.provider, config.repository, stories), mutations: 0, access_checked: false,
  };
  return new Outcome(blocked.length ? 1 : 0, result, [...diags].sort((a, b) => cmpTuple([rank[a.severity], a.id ?? "", a.code], [rank[b.severity], b.id ?? "", b.code])));
}

// --- apply -----------------------------------------------------------------------------------------

export const defaultProvider = (): Provider => new GitHubCli();

/** Result of an apply that made no mutation. Deliberately omits the digest and Issue bodies. */
function refusal(preview: Record<string, unknown>): Record<string, unknown> {
  return { provider: preview["provider"], repository: preview["repository"], stories: [], will_create: [], blocked: preview["blocked"], can_apply: false, mutations: 0, outcomes: [], published: 0, access_checked: false };
}

type Outcome_ = Record<string, unknown>;

export function applyPublication(project: Project, selection: string[], confirmDigest: string | null, provider?: Provider): Outcome {
  const preview = buildPreview(project, selection);
  if (Object.keys(preview.result).length === 0) return preview;
  const pr = preview.result as unknown as { provider: string; repository: string; stories: StoryItem[]; blocked: string[]; digest: string };
  if (!confirmDigest || confirmDigest !== pr.digest) {
    let code: string, msg: string;
    if (confirmDigest) {
      code = "preview-stale";
      msg = "the confirmed digest does not match the current proposed publication (Story content, selection, configuration or publication state changed); nothing was published — run publish-preview, show it to the human, and ask again";
    } else {
      code = "confirmation-missing";
      msg = "no confirmed digest supplied; nothing was published — run publish-preview and obtain explicit human confirmation";
    }
    return new Outcome(1, refusal(preview.result), [...preview.diagnostics.filter((d) => d.severity === "error"), new Diagnostic("error", code, msg)]);
  }
  if (pr.blocked.length) return new Outcome(1, refusal(preview.result), preview.diagnostics);

  const prov = provider ?? defaultProvider();
  const repository = pr.repository;
  const diags = [...preview.diagnostics];
  const outcomes: Outcome_[] = [];
  const todo = pr.stories.filter((s) => s.action === "create");

  if (todo.length) {
    try { prov.checkAccess(repository); }
    catch (exc) {
      if (exc instanceof ProviderError) {
        diags.push(new Diagnostic("error", exc.code, exc.message));
        return new Outcome(1, refusal(preview.result), diags);
      }
      throw exc;
    }
  }

  let mutations = 0;
  let stop = false;
  for (const story of pr.stories) {
    const sid = story.id;
    if (story.action === "skip") { outcomes.push({ id: sid, outcome: "skipped", reason: "already published", publication: story.known_publication }); continue; }
    if (stop) { outcomes.push({ id: sid, outcome: "not-attempted", reason: "stopped after an earlier inconsistency" }); continue; }
    let ref;
    try {
      ref = prov.createIssue(repository, story.issue_title!, story.issue_body!);
    } catch (exc) {
      if (exc instanceof AmbiguousResult) {
        diags.push(new Diagnostic("error", exc.code, `${sid}: ${exc.message}`, story.path, sid));
        outcomes.push({ id: sid, outcome: "unconfirmed", error: exc.message });
        stop = true; // an Issue may exist: do not create more or retry blindly
        continue;
      }
      if (exc instanceof ProviderError) {
        diags.push(new Diagnostic("error", exc.code, `${sid}: ${exc.message}`, story.path, sid));
        outcomes.push({ id: sid, outcome: "failed", error: exc.message });
        continue;
      }
      const message = redact(pyErrorString(exc)); // defensive: an unexpected provider failure must never read as success
      diags.push(new Diagnostic("error", "provider-failed", `${sid}: ${message}`, story.path, sid));
      outcomes.push({ id: sid, outcome: "failed", error: message });
      continue;
    }
    mutations++;
    let pubId: string;
    try {
      pubId = publication.appendRecord(path.join(project.root, story.path!), today(), "github", repository, ref.number, ref.url);
    } catch (exc) {
      const where = ref.url || `${repository}#${ref.number}`;
      const err = pyErrorString(exc);
      diags.push(new Diagnostic("error", "record-failed",
        `INCONSISTENCY: ${sid} WAS published as ${where} but recording it in ${story.path} failed (${err}); do not publish this Story again — add the PUB record by hand (see publishing-conventions.md) so a duplicate is not created`, story.path, sid));
      outcomes.push({ id: sid, outcome: "published-unrecorded", issue: `#${ref.number}`, url: ref.url, error: err });
      stop = true;
      continue;
    }
    outcomes.push({ id: sid, outcome: "published", issue: `#${ref.number}`, url: ref.url, record: pubId });
  }

  const published = outcomes.filter((o) => o["outcome"] === "published" || o["outcome"] === "published-unrecorded").length;
  const failed = outcomes.some((o) => ["failed", "unconfirmed", "published-unrecorded", "not-attempted"].includes(o["outcome"] as string));
  return new Outcome(failed ? 1 : 0, { ...preview.result, mutations, outcomes, published }, diags);
}

export { cutText };
