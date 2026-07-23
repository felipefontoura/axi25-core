---
name: axi25-query
description: >
  Query AXI25 wiki for answers. Use when the user asks questions about their
  knowledge, life areas, decisions, patterns, or anything stored in the wiki.
  Triggers on: "what do I know about", "query", "search the wiki", "how is my area
  of", "which decisions", "what patterns", "summarize my knowledge", "compare X vs
  Y", "what should I focus on", or any question that references accumulated
  knowledge. Also use when the user asks about connections between concepts, status
  of areas, or wants synthesis across multiple wiki pages. Also use study notes when
  the user asks about in-progress study. If the user says "save this" after a query,
  save the answer as a synthesis page.
---

# Query

Answer questions using the wiki. Cite sources with `[[links]]`.

This is the **retrieval** step of the wiki-llm pattern. Distinguish canonical
knowledge (`20-wiki/`) from in-progress study (`25-studies/`).

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Steps

1. Read `index.md` to find relevant pages
2. Read those pages
3. If the question asks about recent/in-progress study, read `25-studies/`
4. If the question asks about interior/spiritual life, read `40-journal/daily/`, `40-journal/signals/`, and relevant area pages
5. Synthesize an answer with `[[citations]]` to wiki pages and state what is canonical vs in-progress
6. Include a confidence level and note any gaps

## If the user says "save this"

Create → `20-wiki/syntheses/synthesis-<topic>.md`:
```markdown
---
type: synthesis
date: YYYY-MM-DD
trigger: query
---

# Question/Topic

## Analysis
[the synthesized answer]

## Key Insight
[1-2 sentence core takeaway]

## Connected
- [[page-1]]
- [[page-2]]
```

Update `index.md` and `log.md`.

## Query Routing

| Question type | Read from |
|--------------|-----------|
| "What do I know about X?" | concepts + entities matching X |
| "What am I studying about X?" | `25-studies/` + relevant wiki pages |
| "How is my [area]?" | `20-wiki/areas/` + recent signals |
| "How is my spiritual life?" | `20-wiki/areas/spirituality.md` + daily journal + signals |
| "Compare X vs Y" | both concept pages |
| "What decisions?" | `20-wiki/decisions/` |
| "What patterns?" | `20-wiki/patterns/` |
| "What should I focus on?" | areas + projects + patterns |
