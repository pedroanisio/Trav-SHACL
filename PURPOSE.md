---
disclaimer:
  notice: >-
    No information within this document should be taken for granted.
    Any statement or premise not backed by a real logical definition
    or verifiable reference may be invalid, erroneous, or a hallucination.
  generated_by: "GPT-5 via Codex CLI"
  date: "2026-05-17"
---

# Trav-SHACL

## Why We Built This

We believe data validation should not become slower or less truthful just
because the data is connected. Teams should be able to check large, linked
datasets without waiting for rules to run in the least helpful order, and
without being told unsupported rules are safely handled when they are not.

The status quo makes validation feel like a blind pass over a maze. Invalid
entities are found late, useful knowledge is wasted, and partial language
support can be mistaken for full conformance.

Trav-SHACL exists to make validation work with the shape of the problem while
making both results and semantic boundaries auditable.

---

## How We Approach This

- **Traversal before brute force** - Validation order should be planned from
  the relationships between rules, not left to file order or chance.
- **Early invalidation matters** - The system should use known failures as soon
  as they are discovered, because late feedback wastes work.
- **Conformance before convenience** - A supported feature should have parser,
  query, validation, and regression evidence; otherwise the limitation should
  be explicit.
- **Exact parsing over guessing** - SHACL terms should be recognized by their
  real identifiers, not by fragile name fragments or accidental matches.
- **Reports are contracts** - Validation output should be structured enough to
  round-trip, inspect, and compare against engine state.
- **Reusable, inspectable engine** - The same core should serve command line
  use, library use, services, tests, and research while keeping query and rule
  behavior visible.

---

## What It Does

### Core Capabilities

- Parses supported SHACL shape schemas from Turtle and legacy JSON through an
  explicit SHACL term registry.
- Plans shape traversal from dependencies, targets, degrees, and constraint
  counts.
- Represents supported SHACL paths as structured path expressions before SPARQL
  generation.
- Generates and rewrites SPARQL queries for target and constraint validation.
- Validates against SPARQL endpoints and in-memory RDFLib graphs.
- Reports valid and invalid instances, with optional SHACL validation reports
  for consumers that need structured evidence.

### What This Is Not

This project does **not**:

- Aim to implement the entire SHACL language at once.
- Treat partial support as complete conformance.
- Replace the need to inspect generated queries, unsupported features, and
  validation limits.
- Accept parser-only support as enough for a feature to be called complete.
- Treat generated reports as trustworthy unless they can be parsed and checked.
- Optimize for hiding the underlying validation model behind a black box.

---

## Who This Is For

- **Researchers** - To study traversal-aware validation of connected data.
- **Data engineers** - To validate linked datasets with clearer execution
  trade-offs.
- **Library and service integrators** - To embed SHACL validation in Python
  workflows or service deployments.
