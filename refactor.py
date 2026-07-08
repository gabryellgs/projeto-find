import os
import re
import glob

def refactor_css_file(filepath):
    print(f"Refactoring {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if '@media (max-width' not in content:
        return False

    # This is a complex problem. Let's just do a simple replacement for now,
    # or identify if we can just invert the logic.
    # Actually, a full AST parsing is needed. Let's try to install tinycss2 and use it.
    pass

if __name__ == '__main__':
    print("Script ready.")
