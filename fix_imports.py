import os
import re

def fix_imports(root_dir):
    patterns = [
        (r'from core(\.|\s)', r'from backend.core\1'),
        (r'from app(\.|\s)', r'from backend.app\1'),
        (r'from ocr(\.|\s)', r'from backend.ocr\1'),
        (r'from parsing(\.|\s)', r'from backend.parsing\1'),
        (r'from worker(\.|\s)', r'from backend.worker\1'),
        (r'from cli(\.|\s)', r'from backend.cli\1'),
        (r'import core(\.|\s)', r'import backend.core\1'),
        (r'import app(\.|\s)', r'import backend.app\1'),
        (r'import ocr(\.|\s)', r'import backend.ocr\1'),
        (r'import parsing(\.|\s)', r'import backend.parsing\1'),
        (r'import worker(\.|\s)', r'import backend.worker\1'),
        (r'import cli(\.|\s)', r'import backend.cli\1'),
    ]

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content = content
                for pattern, replacement in patterns:
                    new_content = re.sub(pattern, replacement, new_content)

                if new_content != content:
                    print(f"Fixing {path}")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == "__main__":
    fix_imports('backend')
