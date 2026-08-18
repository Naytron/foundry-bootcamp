# Day 2: Ground and Extend the Support Agent

Day 2 turns the basic chat application into a source-backed support assistant. You will index synthetic content, add semantic and hybrid retrieval, expose citations, and add deterministic tools.

## Learning objectives

By the end of this day, you can:

- Design a search index for grounded generation.
- Explain keyword, semantic, vector, and hybrid retrieval.
- Create embeddings through a Foundry project endpoint.
- Preserve source identity from retrieval through the browser.
- Give an agent typed tools without giving it unrestricted authority.
- Test indirect prompt injection, citation integrity, and tool boundaries.

## Labs

1. [Build the support knowledge index](01-index-knowledge.md)
2. [Ground answers and render citations](02-ground-the-agent.md)
3. [Add deterministic support tools](03-add-support-tools.md)
4. [Test trust boundaries](04-test-trust-boundaries.md)

## Day checkpoint

You are complete when:

- The dry-run validates all synthetic Markdown documents.
- A warranty question ranks the warranty policy first.
- Azure mode combines semantic ranking with a vector query when an embeddings deployment is configured.
- The chat stream includes structured citation metadata.
- Warranty lookup uses only synthetic records.
- The case tool returns `submitted: false`.
- All Day 2 tests pass.

The `day-2-complete` Git tag records the reference checkpoint after repository generation.

