# Quickstart Guide: Interactive TUI Prompts

This guide demonstrates how to utilize the new interactive menus for profile configuration, switching, and deletion.

---

## 1. Guided Setup Wizard

To set up a profile interactively without remembering option flags, execute:

```bash
frappe-cli config set
```

The CLI will prompt you to enter the Site URL, API Key, API Secret, date format, and number format. Follow the steps and pick your settings using the arrow keys.

---

## 2. Interactive Profile Switcher

If you have multiple connection profiles configured, you can switch between them interactively without typing the profile name:

```bash
frappe-cli config use
```

An interactive menu will list all configured profile names. Select your desired profile with the arrow keys and press Enter to select it as the active default site.

---

## 3. Interactive Profile Deletion

Remove connection profiles from your configuration file interactively:

```bash
frappe-cli config remove
```

Select the profile you want to delete from the list, and confirm the deletion.

---

## 4. Validating Headless / Non-TTY Environment Fallback

To verify that the CLI correctly disables prompts and avoids hanging in automated environments (like background scripts or CI/CD pipelines), redirect standard input:

```bash
frappe-cli config use < /dev/null
```

The CLI will immediately fail with the error:
`Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.`
and return exit code `1` rather than waiting for user input.
