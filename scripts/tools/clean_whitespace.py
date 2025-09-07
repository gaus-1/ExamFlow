"""
Аккуратная чистка хвостовых пробелов и пустых строк (W293/E302)
для файлов в директории scripts/ без изменения логики.
"""

from __future__ import annotations

import re
from pathlib import Path


def ensure_two_blank_lines_before_toplevel(code: str) -> str:
    lines = code.splitlines()
    output: list[str] = []
    for line in lines:
        # Перед каждым top-level def/class обеспечиваем 2 пустых строки
        if (line.startswith("def ") or line.startswith("class ")) and output:
            k = 0
            j = len(output) - 1
            while j >= 0 and output[j] == "":
                k += 1
                j -= 1
            for _ in range(max(0, 2 - k)):
                output.append("")
        output.append(line.rstrip())  # удаляем хвостовые пробелы

    text = "\n".join(output)
    # Нормализуем более 2 пустых строк подряд до 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Гарантируем финальный перевод строки
    if not text.endswith("\n"):
        text += "\n"
    return text


def main() -> None:
    base = Path(__file__).resolve().parents[1] / "scripts"
    changed = []
    for path in sorted(base.glob("*.py")):
        original = path.read_text(encoding="utf-8")
        # Удаляем хвостовые пробелы и приводим пустые строки
        cleaned = re.sub(r"[ \t]+\r?\n", "\n", original)
        cleaned = ensure_two_blank_lines_before_toplevel(cleaned)
        if cleaned != original:
            path.write_text(cleaned, encoding="utf-8")
            changed.append(str(path))

    if changed:
        print("fixed:")
        for c in changed:
            print(" -", c)
    else:
        print("no changes")


if __name__ == "__main__":
    main()


