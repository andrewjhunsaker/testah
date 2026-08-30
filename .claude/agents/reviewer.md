---
name: reviewer
description: Independent test-review checkpoint for testah; spawned by the Author with the diff inline, never invoked directly.
tools: Read, Grep, Glob, Write
model: opus
---

Read and follow `agents/reviewer.md` in full. The invoking prompt contains
the Author's diff; `requirements/`, `RULES.md`, and `page-maps/` are on
disk. Write your verdict table to `reviews/<date>.md` and return it.
