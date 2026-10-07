// Overlap-score parity: formatting/rounding and the scoring formula against expectations generated from the Python oracle.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { fixed, pyRound } from "../src/pyfmt.js";
import { overlapScore, tokens } from "../src/query.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EXP = JSON.parse(fs.readFileSync(path.join(process.env["SDLC_PARITY_DIR"] ?? path.join(HERE, "..", "..", "parity"), "numeric-expectations.json"), "utf8")) as {
  format: { x: string; f2: string; f3: string; r3: string }[];
  tokens: { text: string; tokens: string[] }[];
  score: { title: string; purpose: string; refs: string; sp: boolean; sr: boolean; score: string; r3: string; f2_of_r3: string }[];
};

test("`.2f`, `.3f` and round(x, 3) match CPython for every exact tie and 8,000+ other values", () => {
  const failures: string[] = [];
  let ties = 0;
  for (const c of EXP.format) {
    const x = Number(c.x);
    if (fixed(x, 2) !== c.f2) failures.push(`.2f ${c.x}: ${fixed(x, 2)} != ${c.f2}`);
    if (fixed(x, 3) !== c.f3) failures.push(`.3f ${c.x}: ${fixed(x, 3)} != ${c.f3}`);
    if (pyRound(x, 3) !== Number(c.r3)) failures.push(`round3 ${c.x}: ${pyRound(x, 3)} != ${c.r3}`);
    if (x.toFixed(2) !== c.f2 || x.toFixed(3) !== c.f3) ties++; // cases where plain JavaScript toFixed would have been wrong
  }
  assert.deepEqual(failures.slice(0, 10), []);
  assert.ok(ties >= 4, `expected the numbers to include JS-vs-Python rounding differences (exact ties), saw ${ties}`);
});

test("the find-overlaps score formula, rounding and displayed score are identical to the oracle", () => {
  const failures: string[] = [];
  for (const c of EXP.score) {
    const s = overlapScore(Number(c.title), Number(c.purpose), Number(c.refs), c.sp, c.sr);
    if (s !== Number(c.score)) failures.push(`score ${JSON.stringify(c)}: ${s}`);
    if (pyRound(s, 3) !== Number(c.r3)) failures.push(`r3 ${c.score}: ${pyRound(s, 3)} != ${c.r3}`);
    if (fixed(pyRound(s, 3), 2) !== c.f2_of_r3) failures.push(`f2 ${c.r3}: ${fixed(pyRound(s, 3), 2)} != ${c.f2_of_r3}`);
  }
  assert.deepEqual(failures.slice(0, 10), []);
});

test("overlap tokenisation (lowercasing, stopwords, plural stripping) matches the oracle", () => {
  const failures = EXP.tokens.filter((c) => JSON.stringify([...tokens(c.text)].sort()) !== JSON.stringify(c.tokens)).map((c) => `${JSON.stringify(c.text)}: ${[...tokens(c.text)].sort()} != ${c.tokens}`);
  assert.deepEqual(failures, []);
});
