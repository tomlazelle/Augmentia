// Locate the packaged Skill library (skills/ and shared/) in an installed package or a source checkout.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** The package root, which contains `skills/` and `shared/` (the same layout in a source checkout and in the installed package). */
export function libraryRoot(): string {
  const root = path.join(HERE, "..", "..");
  if (fs.existsSync(path.join(root, "skills")) && fs.existsSync(path.join(root, "shared"))) return root;
  throw new Error("the Skill library (skills/ and shared/) was not found");
}

export const skillsDir = (): string => path.join(libraryRoot(), "skills");
