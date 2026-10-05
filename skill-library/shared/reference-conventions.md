# Reference Conventions

Documents declare their relationships in a `## References` section:

```markdown
## References

### Derived From
- [BR-001 — Business Overview](../BR/BR-001-business-overview.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.
```

- **Derived From:** source requirements. **Related To:** peers or relevant downstream documents. **Supporting Artifacts:** research, design or evidence.
- A document may have no upstream links. Never create a BRD just because a PRD was requested.
- All links are relative to the containing file and must resolve. On rename or move, update affected links, then run `update-map`.
- Requirement IDs may appear in a reference item (`- [PR-001](…) — PR-001-R003`); `validate` checks that they exist and are not retired.
- **Stories** cite the requirement IDs they satisfy in front matter (`covers: [PR-001-R003]`) **and** link each source document under `Derived From`. `validate` errors when a covered ID does not exist, is retired, or its document is not linked. `covers: []` is allowed for a standalone Story.
- Incoming references are derived, not stored: `sdlc references <ID>`.
