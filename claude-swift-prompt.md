# The definitive Claude Code setup for SwiftUI macOS development

**Claude Code transforms SwiftUI development when configured with the right MCP servers, hooks, tools, and project scaffolding.** The optimal setup combines XcodeBuildMCP for build integration, automated SwiftLint/SwiftFormat hooks, a carefully crafted CLAUDE.md, and a handful of essential MCP servers — producing a workflow where Claude can independently write code, compile it, catch errors, and iterate until things work. This guide covers every layer of that stack with copy-paste configurations tested against the latest 2025–2026 tooling.

The core insight from developers who have shipped production macOS apps entirely with Claude Code: the **deterministic compiler feedback loop** is the single most powerful capability. Claude writes probabilistic code, xcodebuild provides deterministic error feedback, and Claude fixes its own mistakes — often resolving all compilation errors within one or two cycles. Everything in this guide is designed to tighten that loop.

---

## Project scaffolding and the CLAUDE.md foundation

The highest-leverage configuration point in any Claude Code project is the `CLAUDE.md` file. Claude reads it at the start of every session, and its contents directly shape code quality. For a macOS SwiftUI project, this file must accomplish three things: declare modern API preferences (preventing deprecated API usage), provide build/test commands (enabling the feedback loop), and establish architectural patterns.

Here is a production-ready CLAUDE.md for a macOS SwiftUI project:

```markdown
# Project: [AppName]

## Quick Reference
- **Platform**: macOS 15+ (Sequoia)
- **Language**: Swift 6.1, strict concurrency
- **UI Framework**: SwiftUI
- **Architecture**: MVVM with @Observable
- **Testing**: Swift Testing (@Test, #expect)

## Build & Test
- Build: `xcodebuild -scheme MyApp -destination 'platform=macOS' build -quiet`
- Test: `xcodebuild test -scheme MyApp -destination 'platform=macOS' -quiet`
- Lint: `swiftlint lint --quiet`
- Format: `swiftformat .`

## After Every Code Change
1. Run build command to verify compilation
2. Run swiftlint to check for violations
3. Fix any issues before moving on

## Modern Swift Requirements (MUST follow)
- Use `@Observable` macro, NOT `ObservableObject`
- Use `@State` with @Observable objects, `@Bindable` for bindings
- Use `NavigationSplitView` for sidebar patterns, NEVER `NavigationView`
- Use `.foregroundStyle()` NOT `.foregroundColor()`
- Use `.task { }` for async work, NOT `.onAppear` with Task { }
- Use `async/await` and `@MainActor`, NOT DispatchQueue
- Prefer `containerRelativeFrame()` over `GeometryReader`
- Avoid fixed `.frame(width:height:)` — use flexible layouts
- Break views into components at ~100 lines max

## DO NOT
- Use deprecated APIs (NavigationView, foregroundColor, ObservableObject)
- Use force unwrapping (!) without justification
- Use UIKit/AppKit when SwiftUI equivalents exist
- Ignore Swift 6 concurrency warnings
- Add unnecessary GeometryReader usage
- Create monolithic views exceeding 150 lines
```

**Keep CLAUDE.md under 300 lines.** Research shows Claude reliably follows approximately 150–200 instructions. Beyond that, compliance drops. Use progressive disclosure — tell Claude how to find information rather than embedding everything. Nested CLAUDE.md files in subdirectories (e.g., `Features/Auth/CLAUDE.md`) provide context that loads only when Claude works in that directory.

The complete project directory structure should look like this:

```
MyApp/
├── CLAUDE.md                    # Project context (committed)
├── .mcp.json                    # Shared MCP servers (committed)
├── .swiftlint.yml               # Linting rules
├── .swiftformat                 # Formatting rules
├── Makefile                     # Build automation
├── .claude/
│   ├── settings.json            # Team settings (committed)
│   ├── settings.local.json      # Personal overrides (gitignored)
│   ├── commands/                # Custom slash commands
│   │   ├── build.md
│   │   ├── test.md
│   │   └── create-view.md
│   ├── agents/                  # Custom subagents
│   │   └── swift-reviewer.md
│   └── hooks/                   # Hook scripts
│       └── post-swift-edit.sh
├── docs/
│   ├── PRD.md                   # Product requirements
│   ├── ARCHITECTURE.md          # System architecture
│   └── tasks/                   # Task breakdowns
├── MyApp/                       # Source code
│   ├── App/
│   ├── Features/
│   ├── Core/
│   └── Resources/
└── Tests/
```

---

## Essential MCP servers ranked by impact

MCP (Model Context Protocol) servers extend Claude Code's capabilities by connecting it to external tools through a standardized protocol. Not all servers are equally useful — Claude Code already has built-in file editing, terminal access, and web search. The servers below fill genuine capability gaps.

### Tier 1: Must-have for SwiftUI development

**XcodeBuildMCP** is the single most important MCP server for any Xcode-based project. Built by Sentry's Cameron Cooke, it exposes **59 tools** covering building, testing, debugging, simulator management, and even UI automation. Rather than Claude constructing raw `xcodebuild` commands (which are verbose and error-prone), XcodeBuildMCP provides clean tool interfaces like `simulator/build`, `simulator/test`, and `simulator/screenshot`.

```json
{
  "mcpServers": {
    "XcodeBuildMCP": {
      "command": "npx",
      "args": ["-y", "xcodebuildmcp@latest", "mcp"]
    }
  }
}
```

Install via CLI: `claude mcp add XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp`

**Context7** fetches version-specific library documentation directly into Claude's context, solving the stale training data problem that causes Claude to generate deprecated SwiftUI APIs. Add "use context7" to prompts when working with framework APIs, or configure automatic invocation in CLAUDE.md.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**GitHub MCP Server** (the official Go-based server, not the deprecated npm package) handles PR management, issues, code review, and CI/CD. The remote HTTP transport requires no local installation:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_PAT"
      }
    }
  }
}
```

### Tier 2: Highly recommended

**Apple Developer Documentation MCP** (`@kimsungwhee/apple-docs-mcp`) provides deep access to Apple's documentation API, WWDC video search, and sample code discovery — complementing Context7's broader library coverage with Apple-specific depth. **Sequential Thinking** (`@modelcontextprotocol/server-sequential-thinking`) enables structured step-by-step reasoning with branch/revision support, valuable for complex architectural decisions. **Memory MCP** (`@modelcontextprotocol/server-memory`) provides a persistent knowledge graph across sessions, useful for maintaining architecture decisions and coding patterns.

Place shared MCP configuration in `.mcp.json` at the project root (committed to git) and personal servers in `~/.claude.json` at the user level. Each MCP server consumes context window tokens for tool definitions, but Claude Code's **Tool Search** feature (active when definitions exceed 10% of context) dynamically loads only needed tools, reducing overhead by roughly **85%**.

---

## Swift tooling that closes the quality loop

Install every essential tool in one command:

```bash
brew install swiftlint swiftformat xcbeautify periphery
```

**SwiftLint** handles safety and logic rules — force unwrapping detection, naming conventions, complexity limits. **SwiftFormat** (nicklockwood's version, not Apple's built-in `swift-format`) handles style — indentation, spacing, brace placement. Using both together with non-overlapping concerns eliminates the most common code quality issues. Configure SwiftLint for safety rules and disable its style rules to avoid conflicts with SwiftFormat.

A starter `.swiftlint.yml`:

```yaml
disabled_rules:
  - trailing_whitespace
  - line_length
opt_in_rules:
  - force_unwrapping
  - force_cast
  - empty_count
  - implicitly_unwrapped_optional
excluded:
  - .build
  - DerivedData
line_length:
  warning: 150
  error: 200
  ignores_function_declarations: true
function_body_length:
  warning: 100
  error: 150
identifier_name:
  min_length:
    error: 3
  excluded: [id, x, y, i]
```

**Periphery** detects dead code — unused classes, functions, properties, and protocols that accumulate as Claude generates and refactors code. Run it periodically with `periphery scan --schemes MyApp --targets MyApp`. **xcbeautify** transforms xcodebuild's verbose output into clean, readable formatting and can generate JUnit reports for CI.

For testing, **Swift Testing** (included in Xcode 16+) is the recommended framework for new unit tests, using `@Test` macros, `#expect` assertions, and built-in parameterized tests. Keep XCTest for UI tests and performance tests. They coexist in the same test bundle.

```swift
import Testing

@Suite("Authentication Tests")
struct AuthTests {
    @Test("Login succeeds with valid credentials")
    func validLogin() async throws {
        let auth = AuthService()
        let result = try await auth.login(email: "test@test.com", password: "pass")
        #expect(result.isSuccess)
    }

    @Test("Login fails with invalid emails", arguments: ["", "notanemail", "@missing"])
    func invalidEmail(_ email: String) {
        #expect(!EmailValidator.isValid(email))
    }
}
```

---

## Hooks that automate quality enforcement

Claude Code hooks are deterministic shell commands that fire at specific lifecycle points — unlike CLAUDE.md instructions (which are advisory), hooks are **guarantees**. The most impactful hook for Swift development auto-formats and lints every file Claude writes or edits.

Create `.claude/hooks/post-swift-edit.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.swift ]]; then
  if command -v swiftformat &> /dev/null; then
    swiftformat "$FILE_PATH" 2>/dev/null || true
  fi
  if command -v swiftlint &> /dev/null; then
    swiftlint lint --fix "$FILE_PATH" 2>/dev/null || true
  fi
fi
exit 0
```

Configure it in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "MultiEdit",
      "Glob", "Grep", "LS",
      "Bash(xcodebuild *)",
      "Bash(swift *)",
      "Bash(swiftlint *)",
      "Bash(swiftformat *)",
      "Bash(git *)",
      "Bash(xcrun simctl *)",
      "Bash(make *)",
      "mcp__XcodeBuildMCP__*"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-swift-edit.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude needs attention\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

Claude Code supports **12 hook events**: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `TeammateIdle`, and `TaskCompleted`. The `matcher` field accepts regex against tool names (`Write`, `Edit`, `Bash`, `Read`, etc.). Exit code **0** allows the action, exit code **2** blocks it with stderr fed back to Claude as an error message.

A PreToolUse hook can protect sensitive files from accidental modification — useful for preventing Claude from editing `.env` files, `Secrets.swift`, or `GoogleService-Info.plist`.

---

## Extended thinking and the plan-first workflow

Claude Code maps specific keywords to thinking token budgets: **"think"** allocates ~4K tokens, **"think hard"** or **"megathink"** allocates ~10K tokens, and **"ultrathink"** allocates ~32K tokens. As of January 2026, extended thinking is enabled by default at 31,999 tokens for supported models, making the keywords less critical but still useful as explicit signals of problem complexity.

The most effective workflow for complex features follows four phases:

1. **Explore** — Let Claude read the codebase in read-only Plan Mode (`Shift+Tab` to toggle). Ask it to understand existing patterns before writing anything.
2. **Plan** — "Ultrathink about implementing [feature]. Analyze the codebase structure and propose a detailed plan. Don't write code yet." This produces a plan Claude can execute methodically.
3. **Implement** — Execute the plan. Claude creates its own TODO lists and works through them step by step.
4. **Verify** — Build, test, lint. The hooks handle formatting automatically, but explicitly ask Claude to run the full test suite.

**Write specifications to markdown files, then start fresh sessions to implement them.** This avoids polluting implementation context with planning conversations. For a complex macOS app, write `docs/specs/001-sidebar-navigation.md` in one session, then `/clear` and start a new session with "Implement the spec in `docs/specs/001-sidebar-navigation.md`."

Custom slash commands encode these patterns into reusable workflows. Create `.claude/commands/create-view.md`:

```markdown
---
description: Create a new SwiftUI view with ViewModel
argument-hint: <ViewName>
allowed-tools: Read, Write, Bash(xcodebuild *)
---
Create the SwiftUI view "$ARGUMENTS" following project conventions:
1. Create `Features/$ARGUMENTS/Views/$ARGUMENTSView.swift` with a SwiftUI view
2. Create `Features/$ARGUMENTS/ViewModels/$ARGUMENTSViewModel.swift` using @Observable
3. Add a #Preview block
4. Create a test file in Tests/
5. Build to verify compilation
```

Invoke with `/create-view UserProfile`.

---

## Context management for large codebases

Claude Code's context window is **200K tokens** by default (expandable to 1M on Max/Team/Enterprise plans), with roughly 30K–40K consumed by system prompts and tool definitions before you type anything. Performance degrades around **147K–152K tokens**, and auto-compaction triggers at 64–75% capacity.

The most effective context management strategies for a large SwiftUI codebase:

**Use subagents aggressively.** Each subagent gets its own isolated 200K token context window, and only a summary returns to your main conversation. Up to **10 subagents** can run concurrently. Ask Claude to "use a subagent to investigate how the navigation system works" before implementing changes — this keeps your main context clean. Subagents cannot spawn other subagents, preventing infinite nesting.

**Run `/compact` proactively** at logical breakpoints rather than waiting for auto-compaction. Add a focus directive: `/compact focus on the sidebar implementation changes`. Use `/clear` liberally between unrelated tasks — it preserves CLAUDE.md context while freeing the entire conversation history.

**Disable unused MCP servers.** Each server's tool definitions consume tokens. Run `/mcp` inside Claude Code to check per-server costs. Start with only the essential three (XcodeBuildMCP, Context7, GitHub) and add others as needed.

**Use file line ranges** when reading code: "Read lines 40–90 of Sources/Auth/AuthService.swift" instead of reading entire files. For quick questions that don't need to persist in context, use `/btw` — it appears in a dismissible overlay and never enters conversation history.

---

## Common SwiftUI pitfalls that AI code generators hit

Claude — like all LLMs — has specific failure patterns with SwiftUI that the CLAUDE.md configuration above is designed to prevent. Understanding these patterns helps you catch issues during diff review.

**Deprecated API usage is the most frequent issue.** Claude often generates `NavigationView` (deprecated since iOS 16), `foregroundColor()` (replaced by `foregroundStyle()`), and `ObservableObject` with `@Published` (superseded by `@Observable`). The CLAUDE.md "DO NOT" section addresses this, but Claude occasionally ignores instructions during long sessions — watch for it after compaction events.

**Platform confusion between iOS and macOS** manifests as UIKit type references (`UIColor`, `UIDevice`, `UIGraphicsImageRenderer`) that don't exist on macOS, incorrect navigation patterns, and missing macOS-specific window management. Always specify the platform explicitly in prompts: "This is a macOS app."

**Over-reliance on GeometryReader and fixed frame sizes** produces brittle layouts. Claude reaches for `GeometryReader` when `containerRelativeFrame()` or `visualEffect()` would work better, and adds unnecessary `.frame(width: 300, height: 200)` modifiers that break at different window sizes.

**Swift 6 strict concurrency** trips up AI code generators frequently. Claude sometimes falls back to `DispatchQueue.main.async` when encountering concurrency errors instead of properly using `@MainActor` and structured concurrency. Peter Steinberger's open-source `swift-concurrency.md` agent skill (in the `steipete/agent-rules` repository) provides comprehensive concurrency guidance that significantly improves Claude's output.

**The "unable to type-check this expression in reasonable time" error** appears when Claude generates overly complex SwiftUI view expressions in a single `body` property. The fix is decomposition — extract subviews into separate structs, which also improves AI readability for future modifications.

---

## Putting it all together: the complete setup sequence

Run these commands to set up the complete environment from scratch:

```bash
# 1. Install Swift development tools
brew install swiftlint swiftformat xcbeautify periphery

# 2. Install essential MCP servers
claude mcp add XcodeBuildMCP -- npx -y xcodebuildmcp@latest mcp
claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp@latest
claude mcp add --scope user --transport http github \
  https://api.githubcopilot.com/mcp \
  -H "Authorization: Bearer $GITHUB_PAT"
claude mcp add sequential-thinking --scope user -- \
  npx -y @modelcontextprotocol/server-sequential-thinking
claude mcp add apple-docs --scope user -- \
  npx -y @kimsungwhee/apple-docs-mcp

# 3. Verify MCP servers
claude mcp list

# 4. Initialize project (from project root)
claude
> /init
```

After `/init` generates a starter CLAUDE.md, replace it with the production-ready version from the scaffolding section above. Create the `.claude/settings.json` with the hooks and permissions configuration. Add `.mcp.json` with the project-level MCP servers (XcodeBuildMCP and Context7). Create your custom slash commands and the post-edit hook script.

The resulting workflow is: Claude writes Swift code → the PostToolUse hook auto-formats with SwiftFormat and lints with SwiftLint → Claude runs `xcodebuild` (via XcodeBuildMCP or direct bash) to catch compiler errors → Claude reads errors and fixes them → the cycle repeats until compilation succeeds and tests pass. This loop, combined with a CLAUDE.md that enforces modern API usage and a Context7 server that provides current documentation, produces remarkably clean SwiftUI code with minimal manual intervention.

## Conclusion

The difference between a frustrating Claude Code experience and a productive one comes down to **three configuration layers working together**: CLAUDE.md preventing known failure modes before they occur, hooks enforcing quality standards deterministically after every edit, and MCP servers (especially XcodeBuildMCP) providing Claude with the tools to verify its own work. The developers who report shipping entire macOS applications with Claude Code universally emphasize the build-test-fix feedback loop over any prompting technique. Invest your setup time in tightening that loop — automated formatting, automated linting, automated compilation checks — and Claude Code becomes a remarkably capable SwiftUI development partner rather than a code generator that requires constant supervision.