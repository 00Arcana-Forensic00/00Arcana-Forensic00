# Arcalume accessibility

Target: WCAG 2.2 AA, then a published VPAT 2.5 (INT) conformance report. Only ABBYY
FineReader among the desktop tools in docs/BENCHMARK.md publishes one today.

## Automated in CI (`tests/test_app_ui.py`, real UI in Chromium)
- axe-core, WCAG 2.0/2.1/2.2 A and AA rule sets, zero violations on: start screen, workspace
  (with filled areas, reading order and report open), Vaults, License, shortcuts dialog,
  upgrade dialog, seal dialog and its result, in light and dark themes.
- Keyboard-only: skip link first; tabs with arrow keys, Home and End; compare slider with arrows,
  Home and End and a spoken value ("51% original, 49% recovered"); Alt+1/2/3 view modes; Alt+M
  filled areas; F1 help; dialogs return focus to the control that opened them.
- Every focusable control shows a focus outline.
- Reflow at 320 CSS px with no horizontal scrolling; 200% text with no horizontal scrolling.
- Target size at least 24 px (checkboxes count their label).
- Errors are announced (role=alert) and marked `aria-invalid` on the field.

## Built in, not yet automatically tested
- Follows the system light/dark setting, `prefers-contrast: more`, Windows contrast themes
  (`forced-colors`) and `prefers-reduced-motion`.
- Filled areas use a hatch pattern plus a text legend, never colour alone; findings carry a
  hidden "Done/Check/Note" word as well as an icon and colour.
- No single-letter shortcuts (WCAG 2.1.4); passphrase fields allow paste and password managers
  (3.3.8).

## Still to do before claiming conformance
- Manual screen-reader passes: NVDA and JAWS (WebView2), Narrator, VoiceOver (WKWebView), Orca.
- Native file dialogs are the operating system's own and inherit its accessibility.
- Write the VPAT from the results above.
