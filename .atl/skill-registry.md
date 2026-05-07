# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| When building AI chat features - breaking changes from v4. | ai-sdk-5 | /home/jorge/.config/opencode/skills/ai-sdk-5/SKILL.md |
| When writing Angular components, services, templates, or making architectural decisions about component placement. | scope-rule-architect-angular | /home/jorge/.config/opencode/skills/angular/SKILL.md |
| When creating a pull request, opening a PR, or preparing changes for review. | branch-pr | /home/jorge/.config/opencode/skills/branch-pr/SKILL.md |
| When implementing CDP-based network capture, debugging, or tracing in a Chrome Extension. | cdp-chrome-debugger | /home/jorge/.config/opencode/skills/cdp-chrome-debugger/SKILL.md |
| when a PR would exceed 400 changed lines, when planning chained PRs, stacked PRs, or reviewable slices. | chained-pr | /home/jorge/.config/opencode/skills/chained-pr/SKILL.md |
| When building Chrome/Edge extensions, writing manifest.json V3, service workers, content scripts, DevTools panels, or using chrome.* APIs. | chrome-extension-mv3 | /home/jorge/.config/opencode/skills/chrome-extension-mv3/SKILL.md |
| when writing guides, READMEs, RFCs, onboarding docs, architecture docs, or review-facing documentation. | cognitive-doc-design | /home/jorge/.config/opencode/skills/cognitive-doc-design/SKILL.md |
| when drafting or posting feedback, review comments, maintainer replies, Slack messages, or GitHub comments. | comment-writer | /home/jorge/.config/opencode/skills/comment-writer/SKILL.md |
| When building REST APIs with Django - ViewSets, Serializers, Filters. | django-drf | /home/jorge/.config/opencode/skills/django-drf/SKILL.md |
| When writing C# code, .NET APIs, or Entity Framework models. | dotnet | /home/jorge/.config/opencode/skills/dotnet/SKILL.md |
| When writing Go tests, using teatest, or adding test coverage. | go-testing | /home/jorge/.config/opencode/skills/go-testing/SKILL.md |
| When user asks to release, bump version, update homebrew, or publish a new version. | homebrew-release | /home/jorge/.config/opencode/skills/homebrew-release/SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature. | issue-creation | /home/jorge/.config/opencode/skills/issue-creation/SKILL.md |
| When user asks to create an epic, large feature, or multi-task initiative. | jira-epic | /home/jorge/.config/opencode/skills/jira-epic/SKILL.md |
| When user asks to create a Jira task, ticket, or issue. | jira-task | /home/jorge/.config/opencode/skills/jira-task/SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen". | judgment-day | /home/jorge/.config/opencode/skills/judgment-day/SKILL.md |
| When working with Next.js - routing, Server Actions, data fetching. | nextjs-15 | /home/jorge/.config/opencode/skills/nextjs-15/SKILL.md |
| When writing E2E tests - Page Objects, selectors, MCP workflow. | playwright | /home/jorge/.config/opencode/skills/playwright/SKILL.md |
| When user wants to review PRs (even if first asking what's open), analyze issues, or audit PR/issue backlog. | pr-review | /home/jorge/.config/opencode/skills/pr-review/SKILL.md |
| When writing Python tests - fixtures, mocking, markers. | pytest | /home/jorge/.config/opencode/skills/pytest/SKILL.md |
| When writing React components - no useMemo/useCallback needed. | react-19 | /home/jorge/.config/opencode/skills/react-19/SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI. | skill-creator | /home/jorge/.config/opencode/skills/skill-creator/SKILL.md |
| When building a presentation, slide deck, course material, stream web, or talk slides. | stream-deck | /home/jorge/.config/opencode/skills/stream-deck/SKILL.md |
| When styling with Tailwind - cn(), theme variables, no var() in className. | tailwind-4 | /home/jorge/.config/opencode/skills/tailwind-4/SKILL.md |
| When reviewing technical exercises, code assessments, candidate submissions, or take-home tests. | technical-review | /home/jorge/.config/opencode/skills/technical-review/SKILL.md |
| When writing TypeScript code - types, interfaces, generics. | typescript | /home/jorge/.config/opencode/skills/typescript/SKILL.md |
| when implementing a change, preparing commits, splitting PRs, or planning chained or stacked PRs. | work-unit-commits | /home/jorge/.config/opencode/skills/work-unit-commits/SKILL.md |
| When using Zod for validation - breaking changes from v3. | zod-4 | /home/jorge/.config/opencode/skills/zod-4/SKILL.md |
| When managing React state with Zustand. | zustand-5 | /home/jorge/.config/opencode/skills/zustand-5/SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### ai-sdk-5
- Import `useChat` from `@ai-sdk/react` (NOT `ai`) in AI SDK 5
- Use `sendMessage()` instead of `handleSubmit` + `handleInputChange`
- Use `DefaultChatTransport` from `ai` package
- Streaming: use `onFinish` callback for completion handling
- Breaking: `api` config option replaced by transport pattern

### scope-rule-architect-angular
- ALL components standalone by default in Angular 20 — no `standalone: true` needed
- Use `input()`/`output()` functions instead of `@Input()`/`@Output()` decorators
- Use `inject()` instead of constructor DI
- Use signals (`signal()`, `computed()`, `effect()`) — no lifecycle hooks like `ngOnInit`
- Apply `ChangeDetectionStrategy.OnPush` on all components
- Scope Rule: place components in the domain directory they serve (screaming architecture)

### branch-pr
- Every PR MUST link an approved issue — no exceptions
- Every PR MUST have exactly one `type:*` label
- Automated checks must pass before merge
- Blank PRs without issue linkage are blocked by GitHub Actions
- Branch naming: `{type}/{issue-number}-{short-description}`

### cdp-chrome-debugger
- Attach debugger via `chrome.debugger.attach({tabId}, "1.3")` in Service Worker
- Use `Network.enable` + `Network.requestWillBeSent` / `Network.responseReceived` for capture
- Detach in `onSuspend` listener — never leave dangling debugger sessions
- Mock `chrome.debugger` in Vitest with `chrome.debugger.onEvent.addListener`
- Playwright: use `page.on('request')` / `page.on('response')` for CDP-free E2E validation

### chained-pr
- Split when PR exceeds 400 changed lines or tasks forecast high budget risk
- Each PR in chain: ≤400 lines, reviewable in ~60 minutes
- Name like `feature/1-of-3-base`, `feature/2-of-3-api`, `feature/3-of-3-ui`
- Merge base first, then rebase dependents sequentially
- Document dependency graph in PR description with `depends-on: #N`

### chrome-extension-mv3
- Service Worker is EPHEMERAL — terminates after ~30s idle; use `chrome.storage` or IndexedDB for state
- Messaging: `chrome.runtime.sendMessage` (SW↔content script), `chrome.tabs.sendMessage` (SW→tab)
- No persistent connections — use `chrome.runtime.connect` only with reconnect logic
- MV3 requires `"service_worker"` not `"background"` in manifest
- Use `chrome.scripting.executeScript` instead of `tabs.executeScript`
- `chrome.debugger` API requires `"debugger"` permission in manifest

### cognitive-doc-design
- Lead with the answer — put decision/action first, context after
- Progressive disclosure: summary → details → references
- Chunking: split long docs into sections with clear headings
- Recognition over recall: use tables, checklists, examples
- Signposting: tell reader what's coming and where they are

### comment-writer
- Start with the actionable point — no PR recap before feedback
- Be warm but direct: "This works, but consider X for edge case Y"
- Use bullet points for multiple points
- Acknowledge good solutions explicitly
- Ask questions instead of making demands when unsure

### django-drf
- Use `viewsets.ModelViewSet` for CRUD endpoints
- Separate serializers per action: `ListSerializer` ≠ `DetailSerializer`
- Override `get_queryset()` for per-user filtering, not in `queryset` attribute
- Use `@action(detail=True/False)` for custom routes
- Use `filterset_class` + `django-filter` for search/filter
- Permission classes on ViewSet, not per-method (except `get_permissions()` override)

### dotnet
- Use Minimal APIs for ALL new endpoints — no Controllers
- Group routes: `app.MapGroup("/api/orders").RequireAuthorization()`
- EF Core: use `AsNoTracking()` for read-only queries
- Use `Results.Ok<T>()`, `Results.NotFound()`, `Results.ValidationProblem()` typed results
- Validation: use `FluentValidation` with endpoint filters
- Prefer primary constructors for DI

### go-testing
- Table-driven tests with `[]struct{name string; ...}` slice
- Use `t.Run(name, fn)` for sub-tests
- Bubbletea: use `teatest.NewModel()` with `WithInitialModel(tmodel)`
- Assert terminal output with `tm.View()` string matching
- Golden files for complex output matching
- Use `cmp` or `require.Equal` for assertions

### homebrew-release
- Supported projects: GGA (`V{version}` tags), Gentleman.Dots (`v{version}` tags)
- Update formula: version + url + sha256 in `.rb` file
- SHA256 via `curl -sL {tarball-url} | shasum -a 256`
- Create PR to `gentleman-programming/homebrew-tap` with formula changes
- Tag must exist before formula update

### issue-creation
- Must use template (bug report or feature request) — blank issues disabled
- Every new issue gets `status:needs-review` automatically
- Maintainer must add `status:approved` before any PR
- Questions go to Discussions, not issues

### jira-epic
- Format: `# {Title}`, **Figma:** link, **Context:** why, **Out of scope:** what not to do
- Split into technical tasks per component (API, UI, SDK)
- Each task references the epic
- Include acceptance criteria per epic, not per task

### jira-task
- Split multi-component work into separate tasks per component
- Task template: Summary, Acceptance Criteria, Technical Notes, Definition of Done
- Link parent epic when applicable
- Include priority and component labels

### judgment-day
- Launch TWO independent, blind judges simultaneously — no communication between them
- Judges analyze code independently, produce structured findings
- Synthesize: reconcile, vote, apply fixes for agreed issues
- Re-judge until both pass (max 2 iterations), then escalate to human
- Each judge uses skill registry for context

### nextjs-15
- App Router: `app/` directory with `layout.tsx`, `page.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`
- Route groups `(group)` for URL-free organization
- Server Components by default — add `'use client'` for interactivity
- Data fetching: `async function Page()` — fetch directly, no `getServerSideProps`
- Server Actions: `'use server'` in a file or `"use server"` in a function
- Dynamic routes: `[slug]/page.tsx` with `generateStaticParams`

### playwright
- Use Playwright MCP tools FIRST: navigate → snapshot → interact → screenshot → verify → write tests
- Page Object Model: one class per page/view, locators as properties
- Use `getByRole`, `getByText`, `getByTestId` — prefer ARIA roles over CSS selectors
- Test user flows, not implementation details
- `test.use({ storageState })` for authenticated sessions

### pr-review
- Full flow: list open PRs → analyze → structured review
- Review template: Summary → Positive → Changes Requested → Questions → Nitpicks
- Check for: correctness, test coverage, edge cases, security, style consistency
- Different depth per contributor: first-timer (gentle), regular (thorough), maintainer (deep)

### pytest
- Class-based: `class TestThing:` with `def test_*` methods
- Fixtures for setup/teardown, use `conftest.py` for shared fixtures
- `pytest.mark.parametrize` for multiple test cases
- `pytest.raises(Error)` for expected exceptions
- `mocker` fixture from `pytest-mock` for mocking
- `tmp_path` fixture for temp files

### react-19
- No `useMemo`/`useCallback` — React Compiler auto-memoizes
- `use()` hook for promises and context — replaces `useEffect` for data fetching
- Server Components by default, `'use client'` only when interactivity/hooks needed
- `ref` is a regular prop — no `forwardRef` wrapper needed
- Actions: `useActionState` for form mutations, `useOptimistic` for optimistic UI
- Metadata: export `metadata` object from page/layout

### skill-creator
- Create `SKILL.md` in the `skills/` directory with YAML frontmatter
- Structure: Purpose → When to Use → Critical Patterns → Rules
- Keep compact rules 5-15 lines
- Include trigger phrases in `description` frontmatter
- Register via `skill-registry` after creation

### stream-deck
- Single-page HTML, no frameworks, no build step, no vertical scroll
- Kanagawa Blur theme: dark bg, cyan/teal/pink accents, inline SVG diagrams
- SVG rules: `viewBox` not width/height, `<path>` over `<rect>`, high contrast strokes
- Slides as `<section>` siblings with CSS scroll-snap
- Diagrams inline in HTML, not external files

### tailwind-4
- No `var()` in `className` — use inline `style` for dynamic values
- Use `cn()` for conditional classes: `cn("base", condition && "variant")`
- Static-only classes don't need `cn()`
- Theme via `@theme` directive, not `tailwind.config.js`
- `@import "tailwindcss"` in CSS entry point

### technical-review
- Explore structure first (Task agent), then read key files in parallel
- Check for tests — presence/absence is a major signal for senior roles
- Look for red flags: security issues, leaked data, no error handling
- Score each factor 0-10 with specific evidence from code
- Output as Markdown table per candidate

### typescript
- Const types: create `as const` object first, then extract type via `(typeof X)[keyof typeof X]`
- Prefer `interface` for public API shapes, `type` for unions/utility types
- Use `satisfies` for type validation without widening
- `strict: true` in tsconfig — no `any` unless absolutely necessary
- Generic constraints: `<T extends SomeType>` not bare `<T>`

### work-unit-commits
- Each commit is a deliverable work unit: code + its tests + its docs
- NOT file-type batches (don't group all tests in one commit)
- Keep each commit independently reviewable (<400 lines)
- Align commit boundaries with SDD task boundaries
- Use conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`

### zod-4
- Breaking: `z.string().email()` → `z.email()`, `z.string().uuid()` → `z.uuid()`, `z.string().url()` → `z.url()`
- Breaking: `z.string().nonempty()` → `z.string().min(1)`
- New: branded types with `.brand()` for nominal typing
- New: `z.pipe()` for pipeline transformations
- Parsing errors: use ` ZodError.format()` for nested error messages

### zustand-5
- Store: `create<StoreType>((set, get) => ({...}))`
- Actions inside the store with `set()` — no external action creators
- Selectors for derived state: `useStore(s => s.count)`
- Middleware: `persist` for localStorage, `devtools` for Redux DevTools
- No context provider needed — store is global by default

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | /home/jorge/.config/opencode/AGENTS.md | OpenCode agent config — persona, rules, memory protocol |

Read the convention files listed above for project-specific patterns and rules.
