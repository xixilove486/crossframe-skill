# CrossFrame ProMax README Visual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the repository README homepage as a technical dossier that establishes CrossFrame ProMax as a runnable, auditable, repairable v8 reasoning runtime and accurately credits the CrossFrame author × ChatGPT 5.6 Sol (Ultra) collaboration.

**Architecture:** Keep `README.md` as the single public homepage and preserve its existing Suite, Max, installation, workflow, skill-map, and documentation sections. Add a compact ProMax-first hero, a verifiable metrics band, a runtime flow, an eight-capability matrix, model-style suppression explanation, precise activation/dependency guidance, and a bounded cost warning; enforce the new public claims through the existing repository integrity checker.

**Tech Stack:** GitHub-flavored Markdown, GitHub-safe inline HTML, Shields.io badges, Python 3.11 repository integrity checker.

---

## File map

- Modify `README.md`: public homepage hierarchy, ProMax hero, metrics, complete capability explanation, attribution, activation, dependencies, and cost boundary.
- Modify `scripts/check_crossframe_skill_integrity.py`: fail closed when required ProMax homepage claims or attribution boundaries disappear.
- Reference `docs/superpowers/specs/2026-07-24-readme-promax-visual-design.md`: approved visual and content contract; no implementation text is added there.

### Task 1: Freeze the ProMax homepage content contract

**Files:**
- Modify: `scripts/check_crossframe_skill_integrity.py`

- [ ] **Step 1: Add required README markers to the integrity checker**

Inside `check_repo_adapters`, after reading `README.md`, require the exact public markers that prove the homepage covers positioning, attribution, scale, capabilities, routing, and cost:

```python
    readme_text = read(repo / "README.md")
    required_promax_homepage_markers = (
        "CROSSFRAME · V8 STRUCTURAL REASONING RUNTIME",
        "可运行、可审计、可修复的重型 AI 结构推演系统",
        "ChatGPT 5.6 Sol（Ultra）",
        "共创模型不是运行依赖",
        "3,980",
        "3,863 个段落",
        "117 张表",
        "709 个概念",
        "P0–P11",
        "五向真实检索",
        "如何抑制模型自身风味",
        "17,000,000 token",
    )
    for marker in required_promax_homepage_markers:
        require(
            marker in readme_text,
            f"{label}: README missing ProMax homepage marker: {marker}",
        )
```

- [ ] **Step 2: Run the checker and confirm the new contract fails before the README edit**

Run:

```powershell
uv run --python 3.11 --with jsonschema --with pytest --with pyyaml python scripts/check_crossframe_skill_integrity.py --repo .
```

Expected: non-zero exit with the first missing homepage marker, beginning with `CROSSFRAME · V8 STRUCTURAL REASONING RUNTIME`.

### Task 2: Build the technical-dossier homepage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the top hero with the approved ProMax-first hierarchy**

The centered hero must contain this information in this order:

```markdown
<p><strong>CROSSFRAME · V8 STRUCTURAL REASONING RUNTIME</strong></p>

# CrossFrame ProMax

### 可运行、可审计、可修复的重型 AI 结构推演系统

**不是“让模型多想一会儿”的提示词，而是把 v8 全源知识、结构推演、真实检索、反方攻击、明确裁决、完整长文与机器验证锁进同一条运行链的独立 runtime。**

由 **CrossFrame 作者 × ChatGPT 5.6 Sol（Ultra）**共同设计、实现、攻击与验证。
```

Keep the existing release/site links and add a direct `crossframe-promax` skill link. Retain the Suite identity in one subordinate sentence so existing users understand that ProMax belongs to the wider repository.

- [ ] **Step 2: Add the four-metric evidence band and runtime flow**

Use a GitHub-safe four-cell HTML table with these exact meanings:

```html
<table>
  <tr>
    <td align="center"><strong>3,980</strong><br>全源读取事件<br><sub>3,863 个段落 + 117 张表</sub></td>
    <td align="center"><strong>709 个概念</strong><br>逐项处置<br><sub>定义、邻接、误用边界</sub></td>
    <td align="center"><strong>P0–P11</strong><br>阶段状态机<br><sub>冻结、验证、定向修复</sub></td>
    <td align="center"><strong>五向真实检索</strong><br>案例校准<br><sub>支持、反例、边界条件</sub></td>
  </tr>
</table>
```

Follow it with this concise runtime flow:

```text
request → v8 full-source → concept closure → local world model
        → claim-path → retrieval → red-team → position lock
        → dossier + essay → validator → phase-aware repair
```

- [ ] **Step 3: Add the complete eight-capability matrix**

Create a `## ProMax 完整能力` section with eight rows: v8 full-source loading, concept closure, local-world modeling, claim/path deduction, real retrieval, self-attack, explicit adjudication, and verifiable delivery. Every row must name both the capability and its concrete artifact/runtime mechanism; do not describe capabilities only with adjectives.

- [ ] **Step 4: Explain how ProMax limits model-specific output flavor**

Add a `### 如何抑制模型自身风味` subsection explaining these five controls:

1. v8 definitions override pretrained same-name concepts.
2. Frozen artifacts prevent later sections from silently changing the problem or evidence.
3. Retrieval and red-team roles attack the draft rather than agree with it.
4. Position lock forces a post-attack stance, alternatives, withdrawal, stop, and rollback conditions.
5. Fresh validator and phase-aware repair prevent fluent prose from self-certifying completion.

State explicitly that the system constrains and audits model variation but cannot make different foundation models literally identical.

- [ ] **Step 5: Preserve precise activation, attribution, dependency, and consumption boundaries**

Retain all four exact invocation forms, Max/ProMax priority, no suite auto-upgrade, and no fallback to Max. State:

```markdown
> **共创边界：** ChatGPT 5.6 Sol（Ultra）参与了 ProMax skill 的架构设计、实现、攻击测试与验证；CrossFrame v8 的框架定义仍以作者提供的 v8 原始材料为权威。共创模型不是运行依赖，其他具备文件、Python 与可选网络能力的 Agent 型 AI 也可以调用。
```

Retain Python 3.11, `jsonschema`, optional network, bundled v8 snapshot, and the user-observed DeepSeek V4 Pro `17,000,000 token` warning. Label the token figure as a single observed run, never a universal benchmark.

### Task 3: Verify readability and repository integrity

**Files:**
- Verify: `README.md`
- Verify: `scripts/check_crossframe_skill_integrity.py`

- [ ] **Step 1: Run the updated homepage contract**

Run:

```powershell
uv run --python 3.11 --with jsonschema --with pytest --with pyyaml python scripts/check_crossframe_skill_integrity.py --repo .
```

Expected: `ok: crossframe skill integrity checks passed`.

- [ ] **Step 2: Run continuity, mirror, and whitespace checks**

Run:

```powershell
uv run --python 3.11 --with jsonschema python scripts/check_source_continuity.py --materials-only --repo .
uv run --python 3.11 python scripts/sync_skill_mirrors.py --check
git diff --check
```

Expected: all commands exit zero; mirror check reports the Claude skill mirror is synchronized.

- [ ] **Step 3: Audit README links, anchors, and public numbers**

Run a Python 3.11 read-only audit that extracts local Markdown links and HTML `href` values, verifies every relative target exists, confirms every navigation fragment has a matching explicit `<a id="...">`, and compares the published numbers against:

```text
skills/crossframe-promax/references/source_manifest.json
skills/crossframe-promax/references/concept-registry/v8-concept-registry.json
skills/crossframe-promax/scripts/promax_runtime/state_machine.py
```

Expected: zero missing local targets, zero missing explicit navigation anchors, 3,863 paragraphs, 117 tables, 3,980 read events, 709 concepts, and phases P0 through P11.

- [ ] **Step 4: Review the final diff for scope and attribution accuracy**

Confirm the diff modifies only the approved README presentation, integrity contract, design/plan documentation, and no ProMax runtime, schema, v8 source, Max surface, or Suite routing files.

- [ ] **Step 5: Commit the implementation**

```powershell
git add README.md scripts/check_crossframe_skill_integrity.py docs/superpowers/plans/2026-07-24-readme-promax-visual.md
git commit -m "docs: showcase CrossFrame ProMax on README"
```

Expected: one implementation commit after the already committed design specification.

- [ ] **Step 6: Push and merge through GitHub checks**

```powershell
git push -u origin codex/readme-promax-visual
gh pr create --base main --head codex/readme-promax-visual --title "Showcase CrossFrame ProMax on the README" --body "Redesign the README as a ProMax technical dossier; credit the CrossFrame author and ChatGPT 5.6 Sol (Ultra) collaboration; document all eight runtime capabilities, exact activation, dependencies, validation, and observed token cost."
```

Expected: a non-draft pull request. Wait for all required GitHub checks to pass before merging to `main`.
