# CLI Input/Output Contracts: Interactive Prompts

This document defines the interface contracts for the interactive configuration and site profile subcommands.

---

## 1. `config set` Wizard Contract

### Execution (Arguments Omitted)
```bash
frappe-cli config set
```

### Prompt Sequence (Standard input is TTY)
1. **Prompt 1**: `Site URL: ` (User inputs string)
2. **Prompt 2**: `API Key: ` (User inputs string)
3. **Prompt 3**: `API Secret: ` (User inputs masked string)
4. **Prompt 4**: `Date Format (plain, us, french, german) [plain]: ` (User selects option using arrow keys)
5. **Prompt 5**: `Number Format (plain, us, french, german) [plain]: ` (User selects option using arrow keys)
6. **Prompt 6**: `Profile Name [default]: ` (User inputs string or presses Enter for default)

### Success Output (stdout)
```
Configuration saved successfully for profile '<profile_name>'!
```

---

## 2. `config use` Selector Contract

### Execution (Arguments Omitted)
```bash
frappe-cli config use
```

### Prompt Sequence (Standard input is TTY)
1. **Prompt**: `Select profile to use: ` (Scrollable list picker containing all profile keys in config, e.g., `dev`, `production`)

### Success Output (stdout)
```
Default profile set to '<profile_name>'.
```

---

## 3. `config remove` Selector Contract

### Execution (Arguments Omitted)
```bash
frappe-cli config remove
```

### Prompt Sequence (Standard input is TTY)
1. **Prompt 1**: `Select profile to remove: ` (List picker containing configured profile names)
2. **Prompt 2**: `Are you sure you want to remove profile '<profile_name>'? (y/N)` (Confirmation prompt)

### Success Output (stdout)
```
Profile '<profile_name>' removed successfully.
```

---

## 4. Headless Execution Failure Contract

### Execution (Stdin is redirected/non-TTY)
```bash
frappe-cli config use < /dev/null
```

### Output (stderr)
```
Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.
```

### Exit Code
`1`
