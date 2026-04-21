#!/usr/bin/env python3
"""
CV Manager — Interactive CLI to add entries to your LaTeX CV.

Usage:
    python cv_manager.py              # Interactive mode
    python cv_manager.py --compile    # Compile PDF only

Zero dependencies — uses only the Python standard library.
"""

import sys
import os
import re
import shutil
import subprocess

TEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.tex")

# ── ANSI colors (matches CV navy #1B3A5C) ──
NAVY = "\033[38;2;27;58;92m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Section comment markers in main.tex (order matters)
SECTIONS = [
    ("experience", "% ── Experience"),
    ("education", "% ── Education"),
    ("projects", "% ── Projects"),
    ("publications", "% ── Publications"),
    ("skills", "% ── Skills"),
    ("honors", "% ── Honors"),
]


def banner():
    print(f"""
{NAVY}{BOLD}╔══════════════════════════════════════════╗
║          CV Manager — LaTeX CLI          ║
╚══════════════════════════════════════════╝{RESET}
""")


def read_tex():
    with open(TEX_FILE, "r", encoding="utf-8") as f:
        return f.read()


def write_tex(content):
    shutil.copy2(TEX_FILE, TEX_FILE + ".bak")
    with open(TEX_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def escape_latex(text):
    """Escape common special LaTeX characters in user input."""
    for char in ["&", "%", "$", "#", "_"]:
        text = text.replace(char, "\\" + char)
    return text


def find_next_section_pos(content, after_key):
    """Find the byte position of the next section comment after the given one."""
    found = False
    for key, marker in SECTIONS:
        if key == after_key:
            found = True
            continue
        if found:
            pos = content.find(marker)
            if pos != -1:
                return pos
    pos = content.find("\\end{document}")
    return pos if pos != -1 else len(content)


def find_section_top(content, section_key):
    """Find where section content begins (after \\section*{...} + blank line)."""
    marker = dict(SECTIONS).get(section_key)
    if not marker:
        return None
    marker_pos = content.find(marker)
    if marker_pos == -1:
        return None
    section_pos = content.find("\\section*{", marker_pos)
    if section_pos == -1:
        return None
    line_end = content.find("\n", section_pos)
    if line_end == -1:
        return None
    pos = line_end + 1
    while pos < len(content) and content[pos] == "\n":
        pos += 1
    return pos


# ── Prompts ──


def prompt(label, required=True, default=""):
    while True:
        suffix = f" [{default}]" if default else ""
        try:
            val = input(f"  {CYAN}{label}{suffix}:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return default if default else ""
        if not val and default:
            return default
        if val or not required:
            return val
        print(f"  {YELLOW}⚠ Required field.{RESET}")


def prompt_bullets():
    print(f"  {DIM}Enter bullet points (empty line to finish):{RESET}")
    bullets = []
    i = 1
    while True:
        try:
            b = input(f"  {DIM}{i}.{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not b:
            break
        bullets.append(b)
        i += 1
    return bullets


def prompt_choice(label, options):
    """Prompt user to pick from numbered options. Returns the chosen value."""
    print(f"  {CYAN}{label}:{RESET}")
    for i, opt in enumerate(options, 1):
        print(f"    {NAVY}{i}{RESET}  {opt}")
    while True:
        try:
            val = input(f"  {BOLD}>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return options[0]
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val) - 1]
        print(f"  {YELLOW}Pick 1–{len(options)}.{RESET}")


# ── Add functions ──


def add_experience():
    print(f"\n{NAVY}{BOLD}── Add Experience ──{RESET}")
    company = prompt("Company")
    location = prompt("Location")
    title = prompt("Job title")
    dates = prompt("Date range (e.g., Feb 2025 -- Aug 2025)")
    position = prompt_choice(
        "Insert position",
        ["Bottom (oldest role)", "Top (most recent role)"],
    )
    print()
    bullets = prompt_bullets()
    if not bullets:
        print(f"  {YELLOW}⚠ No bullets entered, cancelled.{RESET}")
        return

    items = "\n".join(f"    \\item {escape_latex(b)}" for b in bullets)
    entry_lines = (
        f"\\textbf{{{escape_latex(company)}}}\\hfill {escape_latex(location)}\\\\[1pt]\n"
        f"\\textit{{{escape_latex(title)}}} \\hfill \\textit{{{dates}}}\n"
        f"\\begin{{itemize}}\n{items}\n\\end{{itemize}}\n"
    )

    content = read_tex()

    if "Top" in position:
        pos = find_section_top(content, "experience")
        if pos is None:
            print(f"  {RED}✗ Experience section not found.{RESET}")
            return
        content = content[:pos] + entry_lines + "\n\\vspace{1pt}\n" + content[pos:]
    else:
        pos = find_next_section_pos(content, "experience")
        content = content[:pos] + "\n\\vspace{1pt}\n" + entry_lines + "\n" + content[pos:]

    write_tex(content)
    print(f"\n  {GREEN}✓ Added {title} at {company}.{RESET}")


def add_education():
    print(f"\n{NAVY}{BOLD}── Add Education ──{RESET}")
    school = prompt("School")
    dates = prompt("Date range")
    degree = prompt("Degree (e.g., B.S. in Computer Science)")
    gpa = prompt("GPA (leave empty to skip)", required=False)

    gpa_str = f" \\hfill GPA: {escape_latex(gpa)}" if gpa else ""
    entry = (
        f"\n\\textbf{{{escape_latex(school)}}} \\hfill \\textbf{{{dates}}}\\\\\n"
        f"{escape_latex(degree)}{gpa_str}\n"
    )

    content = read_tex()
    pos = find_next_section_pos(content, "education")
    content = content[:pos] + entry + "\n" + content[pos:]
    write_tex(content)
    print(f"\n  {GREEN}✓ Added {degree} at {school}.{RESET}")


def add_project():
    print(f"\n{NAVY}{BOLD}── Add Project ──{RESET}")
    name = prompt("Project name")
    url = prompt("GitHub/URL (leave empty to skip)", required=False)
    tech = prompt("Tech stack (e.g., Python, Flask)")
    description = prompt("One-line description")

    if url:
        title_tex = f"\\textbf{{\\href{{{url}}}{{{escape_latex(name)}}}}}"
    else:
        title_tex = f"\\textbf{{{escape_latex(name)}}}"

    entry = (
        f"\n\\vspace{{1pt}}\n"
        f"{title_tex} \\hfill \\textit{{{escape_latex(tech)}}}\\\\\n"
        f"{escape_latex(description)}\n"
    )

    content = read_tex()
    pos = find_next_section_pos(content, "projects")
    content = content[:pos] + entry + "\n" + content[pos:]
    write_tex(content)
    print(f"\n  {GREEN}✓ Added project: {name}.{RESET}")


def add_publication():
    print(f"\n{NAVY}{BOLD}── Add Publication ──{RESET}")
    authors = prompt("Authors (e.g., Doe J., Smith A.)")
    your_name = prompt("Your name as it appears", default="Arredondo-Valle A.")
    year = prompt("Year")
    title = prompt("Title")
    venue = prompt("Journal / Conference")

    entry = (
        f"    \\item {escape_latex(authors)}, "
        f"\\underline{{{escape_latex(your_name)}}} ({year}). "
        f"\\textit{{{escape_latex(title)}}}. {escape_latex(venue)}.\n"
    )

    content = read_tex()
    pub_start = content.find("% ── Publications")
    if pub_start == -1:
        print(f"  {RED}✗ Publications section not found.{RESET}")
        return
    end_itemize = content.find("\\end{itemize}", pub_start)
    if end_itemize == -1:
        print(f"  {RED}✗ Could not find itemize in Publications.{RESET}")
        return
    content = content[:end_itemize] + entry + content[end_itemize:]
    write_tex(content)
    print(f"\n  {GREEN}✓ Added publication: {title}.{RESET}")


def add_award():
    print(f"\n{NAVY}{BOLD}── Add Award ──{RESET}")
    name = prompt("Award name")
    details = prompt("Details (e.g., Competition (Year))")

    entry = f"\\\\\n\\textbf{{{escape_latex(name)}}} -- {escape_latex(details)}"

    content = read_tex()
    honors_start = content.find("% ── Honors")
    if honors_start == -1:
        print(f"  {RED}✗ Honors section not found.{RESET}")
        return
    end_doc = content.find("\\end{document}", honors_start)
    chunk = content[honors_start:end_doc].rstrip()
    insert_pos = honors_start + len(chunk)
    content = content[:insert_pos] + entry + content[insert_pos:]
    write_tex(content)
    print(f"\n  {GREEN}✓ Added award: {name}.{RESET}")


def add_skill():
    print(f"\n{NAVY}{BOLD}── Add / Update Skill ──{RESET}")
    category = prompt_choice(
        "Skill category",
        ["Languages", "Frameworks", "Cloud \\& DevOps", "Databases"],
    )
    skill = prompt("Skill(s) to append (comma-separated)")

    content = read_tex()
    # Find the matching \textbf{Category:} line and append
    pattern = re.compile(
        r"(\\textbf\{" + re.escape(category) + r":\}\s*)(.*?)(\\\\|$)",
        re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        print(f"  {RED}✗ Could not find '{category}' in Skills section.{RESET}")
        return
    existing = match.group(2).rstrip()
    separator = ", " if existing else ""
    new_line = match.group(1) + existing + separator + escape_latex(skill) + match.group(3)
    content = content[: match.start()] + new_line + content[match.end() :]
    write_tex(content)
    print(f"\n  {GREEN}✓ Added '{skill}' to {category}.{RESET}")


def compile_pdf():
    print(f"\n{NAVY}{BOLD}── Compiling PDF ──{RESET}")
    if shutil.which("latexmk"):
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    elif shutil.which("pdflatex"):
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    else:
        print(f"  {RED}✗ Neither latexmk nor pdflatex found. Install a TeX distribution.{RESET}")
        return

    print(f"  {DIM}Running: {' '.join(cmd)}{RESET}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(TEX_FILE))
    if result.returncode == 0:
        print(f"  {GREEN}✓ Compiled → main.pdf{RESET}")
        # Check page count if pdfinfo available
        if shutil.which("pdfinfo"):
            info = subprocess.run(
                ["pdfinfo", "main.pdf"],
                capture_output=True, text=True,
                cwd=os.path.dirname(TEX_FILE),
            )
            pages = re.search(r"Pages:\s+(\d+)", info.stdout)
            if pages:
                n = int(pages.group(1))
                color = GREEN if n == 1 else RED
                print(f"  {color}Pages: {n}{RESET}")
                if n > 1:
                    print(f"  {YELLOW}⚠ CV exceeds 1 page — trim content before pushing.{RESET}")
    else:
        print(f"  {RED}✗ Compilation failed:{RESET}")
        for line in result.stdout.splitlines():
            if line.startswith("!") or "error" in line.lower():
                print(f"  {RED}  {line}{RESET}")


def undo_last():
    bak = TEX_FILE + ".bak"
    if not os.path.exists(bak):
        print(f"  {YELLOW}No backup found.{RESET}")
        return
    shutil.copy2(bak, TEX_FILE)
    print(f"  {GREEN}✓ Reverted to last backup.{RESET}")


# ── Menu ──

ACTIONS = {
    "1": ("Add Experience", add_experience),
    "2": ("Add Education", add_education),
    "3": ("Add Project", add_project),
    "4": ("Add Publication", add_publication),
    "5": ("Add Award", add_award),
    "6": ("Add Skill", add_skill),
    "7": ("Compile PDF", compile_pdf),
    "8": ("Undo last change", undo_last),
    "0": ("Quit", None),
}


def show_menu():
    print(f"\n{BOLD}What would you like to do?{RESET}")
    for key in ["1", "2", "3", "4", "5", "6", "7", "8", "0"]:
        label = ACTIONS[key][0]
        print(f"  {NAVY}{key}{RESET}  {label}")
    print()


def main():
    if not os.path.exists(TEX_FILE):
        print(f"{RED}✗ {TEX_FILE} not found. Run from the CV repo root.{RESET}")
        sys.exit(1)

    if "--compile" in sys.argv:
        compile_pdf()
        return

    banner()

    while True:
        show_menu()
        try:
            choice = input(f"  {BOLD}›{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {GREEN}Bye! 🚀{RESET}\n")
            break

        if choice == "0":
            print(f"\n  {GREEN}Done. Happy job hunting! 🚀{RESET}\n")
            break
        elif choice in ACTIONS:
            try:
                ACTIONS[choice][1]()
            except KeyboardInterrupt:
                print(f"\n  {YELLOW}Cancelled.{RESET}")
            except Exception as e:
                print(f"  {RED}✗ Error: {e}{RESET}")
        else:
            print(f"  {YELLOW}Invalid option.{RESET}")


if __name__ == "__main__":
    main()
