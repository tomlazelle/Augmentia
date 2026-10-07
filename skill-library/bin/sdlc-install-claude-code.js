#!/usr/bin/env node
import { claudeCodeMain } from "../dist/src/adapters.js";

process.exitCode = claudeCodeMain(process.argv.slice(2));
