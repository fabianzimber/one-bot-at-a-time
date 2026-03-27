# Frontend Redesign Plan

## TL;DR

> **Quick Summary**: Complete radical redesign of the Next.js frontend to an abstract, extremely minimalist Single Page Application (SPA). All gradients removed, using pure flat brand colors. File upload integrated seamlessly into the chatbox. No intro pages, just immediate chat UI.
>
> **Deliverables**:
>
> - Reconfigured `globals.css` with pure flat brand colors (Tailwind v4 `@theme`).
> - Single `app/page.tsx` displaying only the abstract Chat SPA.
> - Minimalist `ChatContainer`, `MessageBubble`, and `InputBar` (with invisible/seamless file upload).
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 (CSS Config) → Task 2 (Layout) → Task 3 & 4 (Components)

---

## Context

### Original Request

Improve frontend styling significantly to be an extremely minimalist and abstract single page, using theming from `one-bot-at-a-time-colors.txt` and NO gradients. Integrate file upload minimally.

### Interview Summary

**Key Discussions**:

- **Design Philosophy**: No intro, no multi-step. User lands directly on the chat. Flat, sharp styling.
- **Colors**: Strict adherence to the provided text file. Midnight (#0D1117), Electric Indigo (#6366F1), etc.

**Research Findings**:

- **Tailwind v4 Theming**: We use Context7-verified CSS variables inside `@theme inline` block and reset default colors with `--color-*: initial;`.
- **Current CSS State**: `app/globals.css` currently contains `--page-gradient`, `.hero-orb`, and `.text-gradient-brand`. These must be permanently deleted.

### Metis Review

**Identified Gaps (Addressed)**:

- **Scope Creep**: This is a _styling_ task. Backend wiring is explicitly not part of this plan. We will build mock state into the UI to prove the styling works.
- **Dependency Guardrail**: No new dependencies (like `framer-motion` or `react-markdown`) unless strictly necessary. We will use CSS for animations and standard React for rendering.
- **BotIdClient Preservation**: The `layout.tsx` contains `BotIdClient` for auth infrastructure. We must NOT remove this.
- **Fonts**: Bot uses `IBM Plex Mono`, User uses `Space Grotesk`. Both are already defined in `layout.tsx`.
- **Edge cases**: The upload must gracefully show state (e.g. filename) inside the minimalist bar. Empty message submission must be prevented.

---

## Work Objectives

### Core Objective

Create a pure, abstract, gradient-free chat interface serving as the sole page of the application.

### Concrete Deliverables

- `frontend/app/globals.css` (rewritten)
- `frontend/app/page.tsx` (SPA chat root)
- `frontend/components/chat/ChatContainer.tsx` (minimal layout with mock state)
- `frontend/components/chat/InputBar.tsx` (text + minimalist file upload icon)
- `frontend/components/chat/MessageBubble.tsx` (mono-font for bot, sans for user)

### Definition of Done

- [ ] Tailwind v4 config is gradient-free and uses exact hex codes.
- [ ] Landing on `/` shows the immediate chatbox, nothing else.
- [ ] `grep -i gradient frontend/app/globals.css` returns 0 results.
- [ ] QA Scenarios pass successfully via Playwright.

### Must Have

- Flat colors only.
- Dark mode only/default (`Midnight` background #0D1117).
- Mono-font for bot responses (`font-mono`).
- Sans-font for user responses (`font-sans`).

### Must NOT Have (Guardrails)

- NO gradients (e.g. `bg-gradient-to-r`, `radial-gradient`, `--page-gradient`).
- NO "landing page" or "hero section" (must be immediate chat).
- NO unit/e2e tests via Playwright/Jest in the code (explicitly requested).
- NO removal of `BotIdClient` in `layout.tsx`.

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.
> No E2E test scripts are checked in, but the implementing agent MUST verify UI via Playwright tool.

### Test Decision

- **Infrastructure exists**: NO
- **Automated tests**: None
- **Framework**: None
- **Agent-Executed QA**: ALWAYS. The executor will use Playwright to open the dev server and verify visuals and interactions.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Foundation):
├── Task 1: Rewrite globals.css (Colors & Typography) [visual-engineering]
└── Task 2: Build main app/page.tsx skeleton [visual-engineering]

Wave 2 (Components):
├── Task 3: Abstract ChatContainer & MessageBubble [visual-engineering]
└── Task 4: Minimalist InputBar with File Upload [visual-engineering]

Wave FINAL:
├── Task F1: Plan compliance audit
├── Task F2: Code quality review
├── Task F3: Real manual QA
└── Task F4: Scope fidelity check

---

## TODOs

- [ ] 1. Rewrite globals.css with Flat Brand Colors

  **What to do**:
  - Edit `frontend/app/globals.css`.
  - Keep the Tailwind and Shadcn imports.
  - In the `@theme inline` block, clear all default colors using `--color-*: initial;`.
  - Define only the colors from `one-bot-at-a-time-colors.txt` (Midnight: #0D1117, Electric Indigo: #6366F1, etc.).
  - Map the shadcn CSS variables (`--background`, `--foreground`, etc.) to use these strictly flat brand colors. For `dark` scheme, use `brand-midnight` as background.
  - Completely DELETE `--page-gradient`, `.text-gradient-brand`, and `radial-gradient` / `linear-gradient` references.
  - Keep `float-slow`, `pulse-soft` animations if needed, but remove any gradient-based classes like `.hero-orb` and `.brand-grid`.

  **Must NOT do**:
  - Do not leave any existing gradient definitions.
  - Do not use Tailwind default colors (like `gray-900` or `blue-500`).

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 3, 4
  - **Blocked By**: None

  **QA Scenarios**:

  ```
  Scenario: Verify pure flat background
    Tool: Bash
    Preconditions: None
    Steps:
      1. cat frontend/app/globals.css | grep -i gradient
    Expected Result: Command returns empty/fails (no gradients present)
    Evidence: .sisyphus/evidence/task-1-grep-gradient.txt
  ```

- [ ] 2. Build main app/page.tsx skeleton

  **What to do**:
  - Edit `frontend/app/page.tsx`.
  - Remove the `WorkInProgressPage` import and usage.
  - Make the layout purely encompass a central `ChatContainer`.
  - The page should be a full-height flex container with a pure `bg-background` (which maps to Midnight).

  **Must NOT do**:
  - No "Get Started" buttons. The user must be in the chat immediately.
  - Do not touch `layout.tsx` (preserve `BotIdClient`).

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 3, 4
  - **Blocked By**: None

  **QA Scenarios**:

  ```
  Scenario: Verify abstract layout renders
    Tool: Playwright
    Preconditions: Next.js dev server running
    Steps:
      1. Navigate to http://localhost:3000
      2. Assert page has no "Work in Progress" text
      3. Take full page screenshot
    Expected Result: An empty, dark, abstract interface is visible immediately.
    Evidence: .sisyphus/evidence/task-2-layout.png
  ```

- [ ] 3. Abstract ChatContainer & MessageBubble

  **What to do**:
  - Create `frontend/components/chat/ChatContainer.tsx` and `MessageBubble.tsx`.
  - Implement `ChatContainer` as a scrollable, borderless minimalist pane. Provide a hardcoded mock message list to visualize it.
  - Implement `MessageBubble`:
    - Bot responses: `font-mono`, text color `brand-ghost` or `brand-slate-light`, no background bubble (just text), or a very subtle flat `brand-secondary` background.
    - User messages: `font-sans`, right-aligned, flat `brand-electric-indigo` background.
  - No unnecessary shadows (use solid borders if any).

  **Must NOT do**:
  - No 3D shadows. Use flat design.
  - No complex state management (Zustand/Redux). Use simple React `useState`.

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: 1, 2

  **QA Scenarios**:

  ```
  Scenario: Verify Chat Bubbles typography
    Tool: Playwright
    Preconditions: Next.js dev server running
    Steps:
      1. Navigate to http://localhost:3000
      2. Inspect Bot message bubble typography (ensure it uses monospace)
    Expected Result: Bot message uses a mono font and User message uses sans-serif.
    Evidence: .sisyphus/evidence/task-3-bubbles.png
  ```

- [ ] 4. Minimalist InputBar with File Upload

  **What to do**:
  - Create `frontend/components/chat/InputBar.tsx`.
  - Style it as a simple, flat input box at the bottom.
  - Integrate file upload purely as a minimalist icon (e.g. `Paperclip` from `lucide-react`) inside the input bar.
  - Add simple mock state: clicking the paperclip opens standard file dialog, selecting a file displays a tiny pill with the filename above or inside the input.
  - Empty message submission should be disabled.

  **Must NOT do**:
  - No massive drag-and-drop zones taking up screen space by default.
  - Do not build a real backend upload API route (keep it frontend UI only).

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: None
  - **Blocked By**: 1, 2

  **QA Scenarios**:

  ```
  Scenario: Verify Input Bar & Upload UI
    Tool: Playwright
    Preconditions: Next.js dev server running
    Steps:
      1. Navigate to http://localhost:3000
      2. Assert the input bar exists at bottom with an attachment icon
      3. Type text into the input
      4. Take screenshot of the input bar
    Expected Result: Input bar looks minimal, flat, and accepts text.
    Evidence: .sisyphus/evidence/task-4-inputbar.png
  ```

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [ ] F1. **Plan Compliance Audit** — `oracle`
      Read the plan end-to-end. Verify implementation exists (no gradients, correct colors).
- [ ] F2. **Code Quality Review** — `unspecified-high`
      Run `tsc --noEmit` + linter.
- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
      Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Save to `.sisyphus/evidence/final-qa/`.
- [ ] F4. **Scope Fidelity Check** — `deep`
      Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep).

---

## Commit Strategy

- `feat(frontend): implement abstract minimalist SPA chat`

## Success Criteria

### Final Checklist

- [ ] All gradients removed.
- [ ] Immediate chat UI on `/`.
- [ ] Exact brand colors used via CSS variables.
