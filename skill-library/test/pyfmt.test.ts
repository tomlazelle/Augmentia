import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { atomicWrite, cmpStr, isRealDate, lexists, quote, readText, relpath, repr, reprStr, resolvePath, splitWs, strip, unquote } from "../src/pyfmt.js";

test("strip/split use Python's whitespace set, not JavaScript's", () => {
  assert.equal(strip("\x1c x \x85"), "x");            // Python strips \x1c-\x1f and \x85; JS trim() does not
  assert.equal(strip("﻿x"), "﻿x");           // JS trim() strips the BOM; Python does not
  assert.deepEqual(splitWs("  a b c  "), ["a", "b", "c"]);
});

test("repr of strings follows CPython", () => {
  assert.equal(reprStr("abc"), "'abc'");
  assert.equal(reprStr("it's"), '"it\'s"');
  assert.equal(reprStr('say "hi"'), `'say "hi"'`);
  assert.equal(reprStr(`both ' and "`), `'both \\' and "'`);
  assert.equal(reprStr("a\\b\n\t\r"), "'a\\\\b\\n\\t\\r'");
  assert.equal(reprStr("\x00\x1f\x7f"), "'\\x00\\x1f\\x7f'");
  assert.equal(reprStr("café"), "'café'");
  assert.equal(reprStr(" "), "'\\xa0'");
  assert.equal(reprStr(" "), "'\\u2028'");
  assert.equal(reprStr("\u{1F600}"), "'\u{1F600}'");
  assert.equal(repr(null), "None");
  assert.equal(repr(true), "True");
  assert.equal(repr(["a", 1]), "['a', 1]");
});

test("urllib quote/unquote", () => {
  assert.equal(quote("a b/c-d_e.f~g"), "a%20b/c-d_e.f~g");
  assert.equal(quote("é/ü"), "%C3%A9/%C3%BC");
  assert.equal(unquote("a%20b%2Fc"), "a b/c");
  assert.equal(unquote("%zz100%"), "%zz100%");          // malformed escapes are left alone (decodeURIComponent would throw)
  assert.equal(unquote("%C3%A9"), "é");
  assert.equal(unquote("%FF"), "�");              // invalid UTF-8 is replaced
});

test("string ordering is by code point", () => {
  assert.ok(cmpStr("\u{1F600}", "￿") > 0);        // UTF-16 code-unit order would say the opposite
  assert.ok(cmpStr("a", "b") < 0 && cmpStr("b", "a") > 0 && cmpStr("x", "x") === 0 && cmpStr("a", "ab") < 0);
});

test("relpath returns '.' for equal paths", () => {
  assert.equal(relpath("/a/b", "/a/b"), ".");
  assert.equal(relpath("/a/b/c.md", "/a"), "b/c.md");
  assert.equal(relpath("/a/x", "/a/b/c"), "../../x");
});

test("dates are validated like datetime.date.fromisoformat", () => {
  assert.ok(isRealDate("2026-02-28") && isRealDate("2024-02-29"));
  assert.ok(!isRealDate("2026-02-29") && !isRealDate("2026-13-01") && !isRealDate("0000-01-01") && !isRealDate("26-01-01"));
});

test("readText translates newlines like Python; atomicWrite renames over the target; lexists sees dangling links", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pyfmt-"));
  try {
    fs.writeFileSync(path.join(dir, "a.txt"), "x\r\ny\rz\n");
    assert.equal(readText(path.join(dir, "a.txt")), "x\ny\nz\n");
    atomicWrite(path.join(dir, "sub", "b.txt"), "hello");
    assert.equal(fs.readFileSync(path.join(dir, "sub", "b.txt"), "utf8"), "hello");
    assert.ok(!fs.existsSync(path.join(dir, "sub", "b.txt.tmp")));
    fs.symlinkSync("nowhere", path.join(dir, "dangling"));
    assert.ok(lexists(path.join(dir, "dangling")) && !fs.existsSync(path.join(dir, "dangling")));
    fs.symlinkSync(dir, path.join(os.tmpdir(), path.basename(dir) + "-link"));
    assert.equal(resolvePath(path.join(os.tmpdir(), path.basename(dir) + "-link", "missing", "x")), path.join(fs.realpathSync(dir), "missing", "x"));
    fs.rmSync(path.join(os.tmpdir(), path.basename(dir) + "-link"));
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});
