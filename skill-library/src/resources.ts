// Packaged resources: the AGENTS.md / CLAUDE.md project-instruction templates.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** `templates/` at the package root (the same layout in a source checkout and in the installed package). */
export function templateText(name: string): string {
  const candidates = [path.join(HERE, "..", "..", "templates", name)];
  for (const c of candidates) if (fs.existsSync(c)) return fs.readFileSync(c, "utf8").replace(/\r\n?/g, "\n");
  throw new Error(`template ${name} not found`);
}
