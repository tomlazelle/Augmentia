# Map Conventions

Every managed content directory has a `map.md`: the root, `BR/`, `PR/`, `Stories/`, `Artifacts/`, and each existing `Artifacts/<sub>/`. `.sdlc/` is internal configuration and has no map.

A map answers: what is this folder for, what documents exist, what is each for, how do they relate.

- **Generated region.** Between `<!-- sdlc:generated:start -->` and `<!-- sdlc:generated:end -->`. Contains the Documents table (ID, linked title, purpose, status — plus Delivery for Stories), the Relationships table (from each document's References), and, for `Artifacts/`, the subdirectory links. It is produced only by `python -m sdlc update-map` from document metadata; never edit it by hand.
- **Hand-written text.** The title, purpose paragraph and Open Questions outside the markers belong to humans and are preserved on regeneration.
- Maps are indexes, not sources of truth. A stale map is fixed by `update-map`, never by changing document content to match it.
- Run `update-map` after creating, renaming, deleting or re-statusing a document, or changing its References. `Artifacts/<sub>/` directories come from `create-dir`, on first use.
