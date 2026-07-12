import json
import sys
import ast

def validate_notebook(notebook_path):
    print(f"Validating {notebook_path}...")
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load notebook: {e}")
        return False

    errors_found = False
    
    for i, cell in enumerate(nb.get("cells", [])):
        if cell["cell_type"] == "code":
            # Extract code lines, ignoring magic commands
            lines = []
            for line in "".join(cell["source"]).split("\n"):
                stripped = line.strip()
                if not stripped.startswith("!") and not stripped.startswith("%"):
                    lines.append(line)
                else:
                    # Keep empty line to maintain line numbers for error reporting
                    lines.append("")
                    
            code = "\n".join(lines)
            if not code.strip():
                continue
                
            try:
                # Compile code allowing top-level await (IPython semantics)
                compile(code, f"cell_{i+1}", "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            except SyntaxError as e:
                print(f"❌ SyntaxError in cell {i+1} at line {e.lineno}: {e.msg}")
                if e.lineno:
                    print(f"   Line code: {code.split('\n')[e.lineno-1]}")
                errors_found = True
            except Exception as e:
                print(f"❌ Compilation error in cell {i+1}: {e}")
                errors_found = True

    if errors_found:
        print("❌ Validation failed! Please fix the errors above before pushing to Kaggle.")
        return False
        
    print("✅ Notebook syntax validation passed!")
    return True

if __name__ == "__main__":
    if not validate_notebook("kaggle_submission/notebook.ipynb"):
        sys.exit(1)
