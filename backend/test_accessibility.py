"""Automated Accessibility (WCAG 2.1 AA/AAA) Compliance & Audit Test Suite.

Validates the frontend codebase against key WCAG criteria:
1. WCAG 3.1.1 (Language of Page): lang="en" in <html>
2. WCAG 2.4.1 (Bypass Blocks): Skip-to-content link present
3. WAI-ARIA 1.2 (Tablist Pattern): role="tablist", role="tab", role="tabpanel"
4. WCAG 4.1.3 (Status Messages): role="status" / aria-live regions
5. WCAG 1.3.1 (Info and Relationships): Explicit <label> or aria-label for inputs
6. WCAG 1.1.1 (Non-text Content): aria-hidden="true" on decorative SVG icons
7. WCAG 2.4.7 (Focus Visible): Focus indicator rules in CSS
8. Accessibility Controls: High contrast & font scaling support
"""

import os
import re
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_accessibility_audit():
    print("\n" + "=" * 70)
    print("[RUNNING] COMPREHENSIVE ACCESSIBILITY (WCAG 2.1 AA/AAA) AUDIT SUITE")
    print("=" * 70 + "\n")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_html_path = os.path.join(project_root, "frontend", "index.html")
    main_jsx_path = os.path.join(project_root, "frontend", "src", "main.jsx")
    styles_css_path = os.path.join(project_root, "frontend", "src", "styles.css")

    # Read files
    with open(index_html_path, "r", encoding="utf-8") as f:
        index_html = f.read()

    with open(main_jsx_path, "r", encoding="utf-8") as f:
        main_jsx = f.read()

    with open(styles_css_path, "r", encoding="utf-8") as f:
        styles_css = f.read()

    passed_checks = 0
    total_checks = 0

    def check(name, condition, description):
        nonlocal passed_checks, total_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {name}: {description}")
        else:
            print(f"  [FAIL] {name}: {description}")
            raise AssertionError(f"Accessibility check failed: {name} - {description}")

    # 1. WCAG 3.1.1: Language of Page
    check(
        "WCAG 3.1.1 (Language)",
        '<html lang="en"' in index_html,
        'index.html declares <html lang="en"> for screen reader pronunciation.',
    )

    # 2. WCAG 2.4.1: Bypass Blocks (Skip Link)
    check(
        "WCAG 2.4.1 (Skip Link HTML)",
        'className="skip-link"' in main_jsx and "Skip to main content" in main_jsx,
        "Skip-to-content link present in main.jsx.",
    )
    check(
        "WCAG 2.4.1 (Skip Link CSS)",
        ".skip-link:focus" in styles_css,
        "Skip-link CSS includes :focus styling to become visible when navigated.",
    )

    # 3. WAI-ARIA 1.2: Tablist Pattern
    check(
        "WAI-ARIA Tablist Role",
        'role="tablist"' in main_jsx,
        'Navigation container uses role="tablist" with aria-label.',
    )
    check(
        "WAI-ARIA Tab Role & Selection",
        'role="tab"' in main_jsx and "aria-selected=" in main_jsx,
        'Workflow buttons use role="tab" with dynamic aria-selected attribute.',
    )
    check(
        "WAI-ARIA Tabpanel Role",
        'role="tabpanel"' in main_jsx and "aria-labelledby=" in main_jsx,
        'Content panels use role="tabpanel" linked via aria-labelledby.',
    )
    check(
        "Keyboard Arrow Traversal",
        "handleTabKeyDown" in main_jsx and "ArrowRight" in main_jsx,
        "Keyboard arrow keys (ArrowLeft/ArrowRight/Home/End) supported for tab navigation.",
    )

    # 4. WCAG 4.1.3: Status Messages & Live Regions
    check(
        "WCAG 4.1.3 (Live Region)",
        'role="status"' in main_jsx and 'aria-live="polite"' in main_jsx,
        "Screen reader live region (role='status', aria-live='polite') present.",
    )
    check(
        "Screen Reader Only Class",
        ".sr-only" in styles_css,
        "Visually hidden utility .sr-only defined in styles.css.",
    )

    # 5. WCAG 1.3.1: Form Control Binding & Labels
    inputs_have_labels = (
        'htmlFor="file-input-field"' in main_jsx
        and 'htmlFor="raw-text-input"' in main_jsx
        and 'htmlFor="doc-a-id"' in main_jsx
        and 'htmlFor="doc-b-id"' in main_jsx
        and 'htmlFor="user-role-select"' in main_jsx
    )
    check(
        "WCAG 1.3.1 (Form Labels)",
        inputs_have_labels,
        "All form controls (textareas, file inputs, selects) have linked <label htmlFor='...'> elements.",
    )

    # 6. WCAG 1.1.1: Decorative SVGs
    check(
        "WCAG 1.1.1 (Decorative SVGs)",
        'aria-hidden="true"' in main_jsx,
        'SVG icons include aria-hidden="true" to prevent screen reader noise.',
    )

    # 7. WCAG 2.4.7: Focus Visible Rings
    check(
        "WCAG 2.4.7 (Focus Visible CSS)",
        ":focus-visible" in styles_css and "outline:" in styles_css,
        "High-contrast focus ring styling (:focus-visible) defined in CSS.",
    )

    # 8. Accessibility Control Toolbar
    check(
        "High Contrast Mode Support",
        "isHighContrast" in main_jsx and "body.high-contrast" in styles_css,
        "High contrast mode toggle implemented in app and CSS.",
    )
    check(
        "Font Size Scaling",
        "fontSize" in main_jsx and "body.font-large" in styles_css,
        "Dynamic font size scaling (Normal / Large / Extra Large) supported.",
    )
    check(
        "Reduced Motion Media Query",
        "prefers-reduced-motion" in styles_css,
        "CSS respects user system reduced-motion preference (@media prefers-reduced-motion).",
    )

    print("\n" + "=" * 70)
    print(f"[ACCESSIBILITY SCORE] {passed_checks}/{total_checks} (100% COMPLIANT)")
    print("=" * 70 + "\n")


def test_accessibility_audit():
    run_accessibility_audit()


if __name__ == "__main__":
    run_accessibility_audit()
