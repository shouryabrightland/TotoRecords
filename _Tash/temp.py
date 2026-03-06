def format_report_table(data: dict, use_color=True) -> str:

    # ANSI colors
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    def color(text, c):
        return f"{c}{text}{RESET}" if use_color else text

    # normalize keys
    rows = [(k.replace("_", " ").title(), str(v)) for k, v in data.items()]

    summary_keys = {"total", "grade", "percentage", "result"}

    subjects = []
    summary = []

    for k, v in rows:
        if k.lower() in summary_keys:
            summary.append((k, v))
        else:
            subjects.append((k, v))

    # widths
    key_w = max(len(k) for k, _ in rows)
    val_w = max(len(v) for _, v in rows)

    def line(l, m, r):
        return l + "─" * (key_w + 2) + m + "─" * (val_w + 2) + r

    out = []

    # header
    out.append(line("┌", "┬", "┐"))

    title = "REPORT CARD"
    total_width = key_w + val_w + 5
    out.append(f"│ {color(title.center(total_width-2), CYAN)} │")

    out.append(line("├", "┬", "┤"))

    # subjects
    for k, v in subjects:
        out.append(
            f"│ {k:<{key_w}} │ {color(v, GREEN):>{val_w + (9 if use_color else 0)}} │"
        )

    # summary section
    if summary:
        out.append(line("├", "┼", "┤"))

        for k, v in summary:
            out.append(
                f"│ {color(k, YELLOW):<{key_w + (9 if use_color else 0)}} │ {v:>{val_w}} │"
            )

    out.append(line("└", "┴", "┘"))

    return "\n".join(out) 


print("\n" + format_report_table({"Math": 95, "Science": 88, "Total": 183, "Grade": "A"}))