---
description: "Search the local astrology library and knowledge graph for rule sources, with page citations and edition disputes."
argument-hint: "<rule or query>"
disable-model-invocation: true
allowed-tools: mcp__plugin_astrology-consultation_astrology__search_astrology_sources mcp__plugin_astrology-consultation_astrology__get_rule_sources
---
# /astro-sources

Use this when a question needs a source: which book, page, edition or school supports a rule, or what the local
library says about a topic. It is a thin wrapper over two MCP tools:

- `search_astrology_sources(query, sources)` — page-cited full-text search of the user's own local astrology
  library (if configured).
- `get_rule_sources(rule)` — which books in the local knowledge graph support or dispute a rule (book, page, tier,
  school).

## When to use

- "Which book and page says Mars in the 7th is Kuja?"
- "What does Shrimali say about pakka ghar, and where does the 1952 edition disagree?"
- "Show me the rule sources for Rahu in house 11."

## Rules

- **Cite what the tool returns, not from memory.** Give book, page, tier and school exactly as returned.
- **Say plainly when the public edition can't resolve a KB locator.** If `search_astrology_sources` or
  `get_rule_sources` returns no result (library not configured, public edition without the knowledge base, or the
  rule isn't recorded), say: "The local library isn't configured, so I can't cite a book and page for that rule." Do
  not invent a page or a verse.
- **Record disputes, don't merge them.** When two editions or schools disagree, show both with their locators; never
  pick one silently.
- **No birth data in queries.** Queries are about rules and books, not charts.
- **Read-only.** This skill never writes, commits or pushes.

## Output shape

For each rule, give:

1. The rule in plain words.
2. Each supporting source: book, edition, page/section, tier, school.
3. Any recorded dispute (edition vs. edition, school vs. school) with its locators.
4. "Not recorded in the local library" when nothing is found — never a fabricated citation.
