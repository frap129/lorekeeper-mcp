---
description: Craft a detailed plan to implement an OpenSpec change/
---

<ChangeId>
  $ARGUMENTS
</ChangeId>
<!-- OPENSPEC:START -->
**Guardrails**
- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.

**Steps**

1. Call the skills_writing_plans tool.
2. Read `openspec/changes/<id>/tasks.md`.
3. Draft `openspec/changes/<id>/plan.md`, using the concepts from the writing plans skill to develop a detailed plan.
4. Ask the user if they would like to proceed with implementation.

<!-- OPENSPEC:END -->
