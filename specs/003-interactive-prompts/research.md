# Research Report: Interactive Prompting and TTY Verification

This document consolidates findings and architecture choices for integrating interactive terminal prompting and detecting non-interactive execution contexts.

---

## 1. Interactive Library Choice

### Decision
Use **`InquirerPy`** as the core prompt utility for all list selections, password inputs, and confirmations.

### Rationale
- **Arrow-key List Navigation**: Unlike Click's standard text prompts, `InquirerPy` provides scrollable, visual lists. This is a requirement for picking profile names from the configuration file without typing them.
- **Hidden Input**: Simple password-style input hiding for sensitive secrets (`api_secret`).
- **Low Memory Footprint**: Loads quickly and adds minimal delay to CLI startup.

### Alternatives Considered
* **`click.prompt`**: Very lightweight, but only supports raw text inputs. It has no support for list pickers or arrow-key selection.
* **`questionary`**: Similar functionality to InquirerPy, but `InquirerPy` provides better typing support and a slightly smaller dependency chain in some environments.

---

## 2. Non-Interactive TTY Detection

### Decision
Verify environment interactivity using a combined check of `sys.stdin.isatty()` and `sys.stdout.isatty()`.

### Rationale
In automated scripts, CI/CD pipelines, or background daemons (like the MCP HTTP daemon), there is no attached keyboard terminal. If a command runs `InquirerPy` prompts in this state, the process will block/hang waiting for input that can never arrive.

To prevent this:
1. Every command requiring interactive prompt fallbacks will execute:
   ```python
   import sys
   if not (sys.stdin.isatty() and sys.stdout.isatty()):
       # Stdin/stdout is redirected or running headless
       raise NonInteractiveError()
   ```
2. If it is non-interactive and the required options/arguments are missing, the command immediately exits with code 1 and writes a clear error message to `sys.stderr`.
