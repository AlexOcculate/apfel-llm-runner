# apfel tag

`apfel tag` classifies piped text into short topical tags using Apple's on-device **content-tagging** model (`SystemLanguageModel(useCase: .contentTagging)`) - a specialized model distinct from the general chat model. It reads text from standard input and prints the tags. 100% on-device, no network.

It is a pipe-first UNIX subcommand: feed it text on stdin, get tags on stdout.

## Plain output (default)

Tags are printed space-separated on one line - easy to pipe into `tr`, `grep`, or `xargs`.

```bash
echo "Mix flour, eggs, and sugar, then bake at 180C for 25 minutes." | apfel tag
```

```text
recipe baking cooking food ingredient temperature time
```

## JSON output

Pass `-o json` (or `--output json`) for a machine-readable object with a `tags` array, ready for `jq`.

```bash
echo "Kubernetes pods keep crashing with OOMKilled under load." | apfel tag -o json
```

```json
{
  "tags" : [
    "troubleshoot",
    "kubernetes",
    "error",
    "load management"
  ]
}
```

Extract just the tags with `jq`:

```bash
echo "The headphones sound amazing and battery lasts all day." | apfel tag -o json | jq -r '.tags[]'
```

## Flags

| Flag | Effect |
|------|--------|
| `-o`, `--output <plain\|json>` | Output format. Default `plain`. |
| `--permissive` | Relax content guardrails. Use this if a benign input is refused (see Notes). |
| `-q`, `--quiet` | Suppress non-essential output. |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Tags produced. |
| `2` | No input piped on stdin. |

```bash
printf "" | apfel tag
```

```text
error: no input provided -- pipe text to classify, e.g. echo "..." | apfel tag
```

## Notes

- **On-device only.** The content-tagging model runs locally on Apple Silicon with Apple Intelligence enabled; no text leaves the machine.
- **Occasional guardrail refusals.** Apple's default safety guardrails can occasionally refuse benign text with `[refusal] Detected content likely to be unsafe`. If that happens on input you trust, re-run with `--permissive`:

  ```bash
  echo "This local-first CLI tool is fast and private." | apfel tag --permissive
  ```

  ```text
  product description performance privacy
  ```

- **CLI-only.** Tagging is a CLI subcommand; it is intentionally not exposed as an HTTP route, to keep the `--serve` surface a clean OpenAI-compatible API. For the server, see [docs/openai-api-compatibility.md](openai-api-compatibility.md).
