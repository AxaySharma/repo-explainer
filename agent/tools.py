import os
import pathlib
import json
import re

def _is_binary_file(path: pathlib.Path) -> bool:
    """Helper to detect if a file is binary or unreadable."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(8192)
            if b'\x00' in chunk:
                return True
            try:
                chunk.decode('utf-8')
            except UnicodeDecodeError as e:
                # If decode failure is not close to the end, it is binary
                if e.start < len(chunk) - 4:
                    return True
        return False
    except Exception:
        return True

def read_file(path: str) -> str:
    """Read a file from disk and return its contents with line numbers."""
    try:
        p = pathlib.Path(path)
        if not p.exists() or not p.is_file():
            return f"ERROR: File not found: {path}"
        
        if _is_binary_file(p):
            return f"ERROR: Cannot read binary file: {path}"
            
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        show_lines = lines[:500]
        
        formatted_lines = []
        width = max(3, len(str(total_lines)))
        for i, line in enumerate(show_lines, 1):
            formatted_lines.append(f"{i:>{width}} | {line.rstrip()}")
            
        result = "\n".join(formatted_lines)
        if total_lines > 500:
            result += f"\n... [truncated: file has {total_lines} total lines. Use search_code to find specific sections]"
        return result
    except Exception:
        return f"ERROR: Cannot read binary file: {path}"

def list_directory(path: str) -> str:
    """List all files and subdirectories at the given path up to 2 levels deep."""
    try:
        root = pathlib.Path(path)
        if not root.is_dir():
            return f"ERROR: Directory not found: {path}"
            
        ignored_names = {'__pycache__', 'node_modules', '.git', 'venv', '.venv', 'dist', 'build'}
        
        def traverse(current_dir: pathlib.Path, depth: int) -> list[str]:
            if depth > 2:
                return []
                
            try:
                entries = list(current_dir.iterdir())
            except Exception:
                return []
                
            filtered_entries = []
            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                if entry.name in ignored_names:
                    continue
                filtered_entries.append(entry)
                
            dirs = sorted([e for e in filtered_entries if e.is_dir()], key=lambda e: e.name.lower())
            files = sorted([e for e in filtered_entries if e.is_file()], key=lambda e: e.name.lower())
            
            lines = []
            
            for d in dirs:
                rel_path = f"/{d.relative_to(root).as_posix()}"
                lines.append(f"DIR  {rel_path}")
                if depth < 2:
                    lines.extend(traverse(d, depth + 1))
                    
            for f in files:
                rel_path = f"/{f.relative_to(root).as_posix()}"
                try:
                    size_bytes = f.stat().st_size
                except Exception:
                    size_bytes = 0
                size_kb = size_bytes / 1024.0
                lines.append(f"FILE   {size_kb:.1f} KB  {rel_path}")
                
            return lines

        result_lines = traverse(root, 1)
        return "\n".join(result_lines)
    except Exception:
        return f"ERROR: Directory not found: {path}"

def search_code(repo_path: str, pattern: str) -> str:
    """Search for a string pattern across all files in the repo recursively."""
    try:
        root = pathlib.Path(repo_path)
        if not root.is_dir():
            return f"ERROR: Repository path not found: {repo_path}"
            
        ignored_names = {'__pycache__', 'node_modules', '.git', 'venv', '.venv', 'dist', 'build'}
        matches = []
        pattern_lower = pattern.lower()
        
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ignored_names]
            
            for filename in filenames:
                file_path = pathlib.Path(dirpath) / filename
                
                try:
                    with open(file_path, 'rb') as f:
                        content_bytes = f.read()
                    content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                    
                rel_path = file_path.relative_to(root).as_posix()
                for line_num, line in enumerate(lines, 1):
                    if pattern_lower in line.lower():
                        matches.append(f"{rel_path}:{line_num}: {line.rstrip()}")
                        if len(matches) >= 50:
                            break
                if len(matches) >= 50:
                    break
            if len(matches) >= 50:
                break
                
        if not matches:
            return f"No matches found for pattern: '{pattern}'"
            
        result = "\n".join(matches[:50])
        if len(matches) >= 50:
            result += "\n[Search truncated: 50 matches shown]"
        return result
    except Exception:
        return f"ERROR: Repository path not found: {repo_path}"

def get_file_tree(repo_path: str) -> str:
    """Return a clean ASCII tree of the entire repo structure."""
    try:
        root = pathlib.Path(repo_path).resolve()
        if not root.is_dir():
            return f"ERROR: Repository path not found: {repo_path}"
            
        ignored_names = {'__pycache__', 'node_modules', '.git', 'venv', '.venv', 'dist', 'build'}
        root_name = root.name + "/"
        
        def build_tree(current_dir: pathlib.Path, prefix: str = "") -> list[str]:
            try:
                entries = list(current_dir.iterdir())
            except Exception:
                return []
                
            filtered = []
            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                if entry.name in ignored_names:
                    continue
                filtered.append(entry)
                
            dirs = sorted([e for e in filtered if e.is_dir()], key=lambda e: e.name.lower())
            files = sorted([e for e in filtered if e.is_file()], key=lambda e: e.name.lower())
            
            sorted_entries = dirs + files
            entry_count = len(sorted_entries)
            
            lines = []
            for i, entry in enumerate(sorted_entries):
                is_last = (i == entry_count - 1)
                connector = "└── " if is_last else "├── "
                
                name_suffix = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{connector}{entry.name}{name_suffix}")
                
                if entry.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(build_tree(entry, next_prefix))
                    
            return lines

        tree_lines = [root_name] + build_tree(root)
        return "\n".join(tree_lines)
    except Exception:
        return f"ERROR: Repository path not found: {repo_path}"

def detect_language_and_framework(repo_path: str) -> str:
    """Detect the primary programming language and framework of the repo."""
    try:
        root = pathlib.Path(repo_path).resolve()
        if not root.is_dir():
            return json.dumps({"error": "Repository path not found"})
            
        try:
            entries = list(root.iterdir())
        except Exception:
            return json.dumps({"error": "Repository path not found"})
            
        config_files_in_root = []
        for entry in entries:
            if entry.is_file():
                config_files_in_root.append(entry.name)
                
        config_mappings = {
            "package.json": "JavaScript/TypeScript",
            "requirements.txt": "Python",
            "Pipfile": "Python",
            "pyproject.toml": "Python",
            "go.mod": "Go",
            "Cargo.toml": "Rust",
            "pom.xml": "Java (Maven)",
            "build.gradle": "Java/Kotlin (Gradle)",
            "composer.json": "PHP"
        }
        
        config_files_found = []
        languages_detected = []
        
        for filename in config_files_in_root:
            if filename in config_mappings:
                config_files_found.append(filename)
            elif filename.endswith('.csproj'):
                config_files_found.append(filename)
                
        config_files_found.sort()
        
        for filename in config_files_found:
            if filename in config_mappings:
                lang = config_mappings[filename]
            elif filename.endswith('.csproj'):
                lang = "C#"
            else:
                continue
            if lang not in languages_detected:
                languages_detected.append(lang)
                
        primary_lang = languages_detected[0] if languages_detected else "Unknown"
        framework = None
        notes_list = []
        
        if "requirements.txt" in config_files_found:
            try:
                req_path = root / "requirements.txt"
                with open(req_path, 'r', encoding='utf-8', errors='replace') as f:
                    req_content = f.read().lower()
                if "fastapi" in req_content:
                    framework = "FastAPI"
                elif "django" in req_content:
                    framework = "Django"
                elif "flask" in req_content:
                    framework = "Flask"
            except Exception as e:
                notes_list.append(f"Could not read requirements.txt: {str(e)}")
                
        if not framework and "package.json" in config_files_found:
            try:
                pkg_path = root / "package.json"
                with open(pkg_path, 'r', encoding='utf-8', errors='replace') as f:
                    pkg_content = f.read().lower()
                if "next" in pkg_content:
                    framework = "Next.js"
                elif "react" in pkg_content:
                    framework = "React"
                elif "express" in pkg_content:
                    framework = "Express"
                elif "vue" in pkg_content:
                    framework = "Vue"
            except Exception as e:
                notes_list.append(f"Could not read package.json: {str(e)}")
                
        if primary_lang != "Unknown":
            notes_str = f"Detected {primary_lang} as the primary language."
            if len(languages_detected) > 1:
                other_langs = [l for l in languages_detected if l != primary_lang]
                notes_str += f" Also found config files for: {', '.join(other_langs)}."
        else:
            notes_str = "No config files or recognized languages detected."
            
        if notes_list:
            notes_str += " " + " ".join(notes_list)
            
        result_dict = {
            "language": primary_lang,
            "framework": framework,
            "config_files_found": config_files_found,
            "notes": notes_str
        }
        return json.dumps(result_dict, indent=2)
    except Exception:
        return json.dumps({"error": "Repository path not found"})

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read a file from disk and return its contents with line numbers. Truncates files larger than 500 lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path of the file to read."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List all files and subdirectories at the given path up to 2 levels deep, showing types and file sizes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative directory path to list."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_code",
        "description": "Search for a string pattern across all files in the repository recursively. Matches case-insensitively, limits to 50 results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "The path to the repository directory to search."
                },
                "pattern": {
                    "type": "string",
                    "description": "The case-insensitive text pattern to search for."
                }
            },
            "required": ["repo_path", "pattern"]
        }
    },
    {
        "name": "get_file_tree",
        "description": "Return a clean ASCII tree representation of the repository directory structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "The path to the repository directory."
                }
            },
            "required": ["repo_path"]
        }
    },
    {
        "name": "detect_language_and_framework",
        "description": "Detect the primary programming language and framework of the repository based on root configuration files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "The path to the repository directory."
                }
            },
            "required": ["repo_path"]
        }
    }
]
