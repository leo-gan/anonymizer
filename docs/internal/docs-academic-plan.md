# Implementation plan: academic-style documentation

**Status:** complete (2026-11-23)
**Audience:** maintainers only
**Do not publish.** This directory is excluded from the MkDocs / GitHub Pages build (`exclude_docs` in `mkdocs.yml`). Do not link it from `README.md`, `docs/index.md`, or the public nav.

## Goal

Make the public documentation simpler, more uniform, and academic in tone — especially the introductory course (`docs/101/`) — matching the restrained, citation-backed style already used in `docs/project/eval-results.md`, `docs/project/mapping-security.md`, and `docs/id-extract/`.

## Design decisions

1. **Math rendering:** Enable `pymdownx.arithmatex` (`generic: true`) with KaTeX so formal definitions (e.g., $(\varepsilon, \delta)$-differential privacy, syntactic table criteria, precision/recall/$F_1$) render as proper equations without breaking currency literals.
2. **Narrative essay (`fairy-tale.md`):** Move out of `docs/101/` into a separate top-level **Essays** section (`docs/essays/`) so the course remains strictly lecture-style.
3. **Theme and chrome:** Stay on `mkdocs-material` with a restrained monochrome palette (`white`/`black` header, `indigo` accent), `IBM Plex Sans` + `IBM Plex Mono`, built-in `footnotes`, `navigation.indexes`, no emojis in titles/headings/tables, and collapsed country navigation under `id-extract`.
4. **Full scope:** Execute both the course/theme/accuracy overhaul (Phase 1) and the landing-page/CLI/recipes simplification (Phase 2).

## Progress

### Phase 1 — Course, configuration, and correctness

- [x] 1. Fix `mkdocs.yml` duplicate keys (`pymdownx.superfences`, `plugins`), configure academic palette/fonts, enable `footnotes` and `pymdownx.arithmatex` + `docs/javascripts/katex.js`, simplify navigation (`navigation.indexes`, collapsed `id-extract` countries, single `Terminology` entry, grouped `Project Docs`, top-level `Essays`), and add `validation.links.anchors: warn`.
- [x] 2. Move `docs/101/fairy-tale.md` to `docs/essays/fairy-tale.md` with `docs/essays/index.md`.
- [x] 3. Rewrite `docs/101/` as four concise, non-overlapping academic lectures (`index.md`, `why-anonymization.md`, `history.md`, `techniques.md`, `how-different.md`) with uniform structure, KaTeX formalism, worked examples, primary references, and corrected attributions/dates (Machanavajjhala et al. 2006 for $\ell$-diversity; WP29 Opinion 05/2014 in 2014; Ohm 2010; accurate description of optional tabular `--k`).
- [x] 4. Fix broken anchors (`architecture.md#table-path-csv-excel`, `cli-usage.md` → `recipes.md`), remove leaked internal planning references (`item N`, `PR #44`), and resolve doc/code drift (`purge`, `--opt-in`, `--cache`, `--encrypt-secret`, `table_privacy`, `api-reference.md`, `terminology.md`, `api-usage.md`, `troubleshooting.md`).
- [x] 5. Enforce `mkdocs build --strict` in `.github/workflows/deploy-docs.yml` and `Makefile`.

### Phase 2 — Landing page, CLI reference, and recipes simplification

- [x] 6. Simplify `docs/index.md` into a concise abstract, entry points, and minimal Quick Start without duplicating the full `README.md` feature matrix.
- [x] 7. Remove the redundant `## History` changelog section from `docs/project/cli-usage.md`, remove icon shortcodes, and update cross-links in `README.md` and `packages/pdf-anonymizer-cli/README.md`.
- [x] 8. Streamline `docs/project/recipes.md`: add a categorized top-level index, merge duplicated residual-apply prose, update SDK persistence snippet to `save_results` (`0600`), and trim repetitive filler while keeping all flags, constraints, SDK snippets, and benchmark facts intact.

## Verification criteria

1. `mkdocs build --strict` exits 0 with zero warnings.
2. Rendered HTML in `101/` contains KaTeX `.arithmatex` blocks, zero raw `$\epsilon$`, and zero misparsed currency strings.
3. `internal/` and `temp/` remain excluded from the built site.
4. No public doc references internal plan numbers (`item 10`, `item 13`, `item 14`, `item 19`, `item 22`, `item 23`, `PR #44`), `101/fairy-tale`, or `cli-usage.md#history`.
5. `pytest` passes without regression.
