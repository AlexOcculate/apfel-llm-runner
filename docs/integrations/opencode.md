# apfel + opencode

Run [opencode](https://opencode.ai), the open-source terminal AI coding agent, against apfel's OpenAI-compatible server so every token stays on-device at zero cost.

**Verified:** opencode 1.17.16 + apfel 1.8.2, macOS 26 (Apple Silicon). A real session transcript is at the bottom of this page.

## 0. Install opencode

Use the official installer - it fetches the platform binary to `~/.opencode/bin/opencode`:

```bash
curl -fsSL https://opencode.ai/install | bash
```

Then ensure `~/.opencode/bin` is on your `PATH`.

> Gotcha: `npm install -g opencode-ai` on its own may not produce a working `opencode` command, because the package's post-install download is skipped under npm's `allow-scripts` policy. The `curl` installer above avoids that.

## 1. Start apfel

```bash
apfel --serve
```

This serves the OpenAI API at `http://127.0.0.1:11434/v1`. Confirm it is up:

```bash
curl -s http://127.0.0.1:11434/v1/models
```

## 2. Configure opencode

Write this to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "compaction": { "auto": true, "prune": true, "reserved": 512 },
  "default_agent": "lean",
  "agent": {
    "lean": {
      "mode": "primary",
      "model": "apfel/apple-foundationmodel",
      "prompt": "You are a concise assistant. Answer directly.",
      "permission": { "*": "deny" }
    }
  },
  "provider": {
    "apfel": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "apfel",
      "options": {
        "baseURL": "http://127.0.0.1:11434/v1",
        "apiKey": "not-needed"
      },
      "models": {
        "apple-foundationmodel": { "name": "apple-foundationmodel" }
      }
    }
  }
}
```

The model id `apple-foundationmodel` must match exactly what apfel reports at `/v1/models`. `apiKey` is a placeholder: a local apfel server started without `--serve-token` needs no auth, but opencode's OpenAI-compatible provider still wants the field present.

## 3. Run it

One-shot:

```bash
opencode run --agent lean "In one sentence, what is a hash map?"
```

Interactive:

```bash
opencode
```

## The 4096-token gotcha (read this)

apfel's on-device model has a **4096-token context window**. opencode is a full coding agent, and it **injects your instruction files - `AGENTS.md`, `CLAUDE.md`, and any global `~/.claude/CLAUDE.md` - verbatim into the system prompt**, plus tool schemas and environment context. That can blow past 4096 tokens before you type a word. The symptom is an HTTP 400 from apfel:

```
Error: Input exceeds the model's context window. Shorten the conversation history.
```

Two things in the config above keep the request small enough to fit:

- `"permission": { "*": "deny" }` on the `lean` agent stops opencode from sending tool schemas (they eat the window fast).
- A short custom `"prompt"` replaces opencode's default agent instructions.

If you still overflow, the culprit is almost always a large `AGENTS.md` or global `~/.claude/CLAUDE.md` being pulled in. Trim it, or keep opencode's instruction files small when the backend is a 4096-token model.

Because of that window, apfel is a great opencode backend for **short Q&A and small, focused edits** - not for large-repo, many-tool, long-running agent sessions. That is a property of the on-device model, not the wiring. The `apfel --count-tokens` flag (see [docs/cli-reference.md](../cli-reference.md)) preflights how much a prompt will cost against the window.

## All the gotchas (from re-verifying this end-to-end)

Every one of these was hit and confirmed while testing on 2026-07-09:

1. **Install**: `npm install -g opencode-ai` can leave you with no working binary (post-install script skipped by npm `allow-scripts`). Use the `curl` installer; the binary lands at `~/.opencode/bin/opencode`.
2. **The 4096-token window is the whole story.** opencode injects `AGENTS.md`, `CLAUDE.md`, and global `~/.claude/CLAUDE.md` verbatim into the system prompt. A large global `CLAUDE.md` alone (this machine had ~13 KB / ~3,300 tokens) overflows the window before you type anything - HTTP 400 `Input exceeds the model's context window`. Keep those instruction files small, or apfel's window cannot fit them.
3. **Deny tools.** `"permission": { "*": "deny" }` stops opencode sending tool schemas, which otherwise consume a big slice of the 4096 tokens.
4. **Set a short agent `prompt`.** It replaces opencode's default agent instructions (verified: the custom prompt does take effect); without it the default coding-agent preamble is larger.
5. **`apiKey` must be present** in the provider `options` even though a local apfel server needs no auth - opencode's `@ai-sdk/openai-compatible` provider expects the field. Any placeholder works.
6. **Model id must match `/v1/models` exactly** (`apple-foundationmodel`). A mismatch fails the request.
7. **opencode makes two calls per turn**: a small title-generation call (always fits) plus the main agent call (the one that can overflow). Seeing the title call succeed but the answer fail is the classic 4096-overflow signature.
8. **`--pure` does not help the overflow** - it disables plugins, not instruction-file ingestion.
9. **Restart opencode after config changes** - it does not always hot-reload provider config.

## Verified session

apfel 1.8.2 server, opencode 1.17.16, `lean` agent, empty project:

```
$ opencode run --agent lean "In one sentence, what is a hash map?"
> lean · apple-foundationmodel

A hash map is a data structure that maps keys to values, allowing for
efficient retrieval, insertion, and deletion of data.
```

apfel's request log for that turn - every call `200 OK`, well inside the window, `$0.00`:

```
POST /v1/chat/completions 200 268ms stream tokens=~591   request bytes=2493
POST /v1/chat/completions 200 100ms stream tokens=~198   request bytes=710
```

## Credit

The original config and the first working screenshot came from [@tvi (Tomas Virgl)](https://github.com/tvi). This page adds an end-to-end re-verification on current opencode and the 4096-token instruction-file gotcha.
