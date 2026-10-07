// `node dist/test/corpus-report.js [--all] [--only SUBSTRING]`: replay the applicable corpus cases and print a report.
import { Corpus, applicable, command, replayAll } from "./replay-lib.js";

const argv = process.argv.slice(2);
const all = argv.includes("--all");
const only = argv.includes("--only") ? argv[argv.indexOf("--only") + 1]! : "";
const commands = argv.includes("--commands") ? argv[argv.indexOf("--commands") + 1]!.split(",") : null;
const corpus = new Corpus();
const cases = corpus.cases.filter((c) => (all ? c.replayable : applicable(c)) && c.id.includes(only) && (commands === null || commands.includes(command(c))));
const results = await replayAll(corpus, cases);
const by: Record<string, { pass: number; exempt: number; fail: number }> = {};
for (const r of results) {
  const b = (by[r.command] ??= { pass: 0, exempt: 0, fail: 0 });
  if (r.status === "pass") b.pass++; else if (r.status === "exempt-pass") b.exempt++; else b.fail++;
}
const failed = results.filter((r) => r.status === "fail");
console.log(`corpus cases applicable to this build: ${cases.length} of ${corpus.cases.length}`);
console.log(`passed ${results.filter((r) => r.status === "pass").length}, passed under approved exemption ${results.filter((r) => r.status === "exempt-pass").length}, FAILED ${failed.length}`);
for (const [cmd, b] of Object.entries(by).sort()) console.log(`  ${cmd.padEnd(16)} pass ${String(b.pass).padStart(4)}  exempt ${String(b.exempt).padStart(3)}  fail ${String(b.fail).padStart(3)}`);
for (const r of failed.slice(0, 60)) { console.log(`  FAIL ${r.id}`); for (const p of r.problems) console.log(`       - ${p}`); }
process.exitCode = failed.length ? 1 : 0;
