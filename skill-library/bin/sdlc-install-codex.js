#!/usr/bin/env node
import { codexMain } from "../dist/src/adapters.js";

process.exitCode = codexMain(process.argv.slice(2));
