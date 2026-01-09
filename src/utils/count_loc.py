"""
LOC (Lines of Code) Counter for LCR Project.

Counts total lines, code lines, and comment lines for files in the project,
supporting Python docstrings as comments.
"""

import os
import sys
import json
import argparse
import tokenize
from pathlib import Path
from typing import Dict, List, Tuple

def count_lines_python(input_source) -> Tuple[int, int, int]:
    """
    Count lines for Python code using tokenize to handle docstrings correctly.
    Accepts valid file path (Path/str) or io.BytesIO stream.
    Returns (total, code, comment).
    """
    import io
    
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    
    stream = None
    should_close = False

    try:
        # Determine if input is path or stream
        if isinstance(input_source, (str, Path)):
            stream = open(input_source, 'rb')
            should_close = True
        elif hasattr(input_source, 'read') and hasattr(input_source, 'seek'):
            stream = input_source
            # Ensure stream is at start
            if stream.seekable():
                stream.seek(0)
        else:
            raise ValueError("Invalid input source. Must be file path or BytesIO stream.")

        # Read content to count total lines
        content = stream.read()
        total_lines = content.count(b'\n') + (1 if content else 0)
        
        # Reset pointer for tokenization
        if stream.seekable():
            stream.seek(0)
        
        # Tokenize expects readline of bytes
        tokens = list(tokenize.tokenize(stream.readline))
        
        # Track lines that have code/docstrings
        # We use sets to avoid double counting lines with multiple tokens
        code_line_nums = set()
        comment_line_nums = set()
        docstring_line_nums = set()
        
        for token in tokens:
            token_type = token.type
            start_line = token.start[0]
            end_line = token.end[0]
            
            if token_type in (tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT):
                continue
            
            if token_type == tokenize.COMMENT:
                comment_line_nums.add(start_line)
            
            elif token_type == tokenize.STRING:
                # Check if it's a docstring (module level or function/class start)
                # Simplified heuristic: check if it's a triple-quoted string
                text = token.string
                if text.startswith('"""') or text.startswith("'''") or \
                   text.startswith('b"""') or text.startswith("b'''") or \
                   text.startswith('u"""') or text.startswith("u'''"):
                    # Mark all lines covered by this token as comment/docstring
                    for line_num in range(start_line, end_line + 1):
                        docstring_line_nums.add(line_num)
                else:
                    # Normal string, counts as code
                    for line_num in range(start_line, end_line + 1):
                        code_line_nums.add(line_num)
            else:
                # Anything else (NAME, OP, NUMBER, etc.) is code
                for line_num in range(start_line, end_line + 1):
                    code_line_nums.add(line_num)

        # Reconcile logic
        final_code_lines = len(code_line_nums)
        potential_comments = comment_line_nums | docstring_line_nums
        final_comment_lines = len(potential_comments - code_line_nums)
        
        return total_lines, final_code_lines, final_comment_lines

    except Exception:
        # Fallback for non-tokenize-able files or encoding errors
        # If input was stream, we might not be able to rewind easily if not seekable, 
        # but count_lines_generic usually expects file path.
        # For stream fallback, simple line counting?
        if isinstance(input_source, (str, Path)):
             return count_lines_generic(Path(input_source))
        return 0, 0, 0 # Fail gracefully for stream
        
    finally:
        if should_close and stream:
            stream.close()

def code_lines_python_set(tokens):
    s = set()
    for token in tokens:
        if token.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.STRING, tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT):
             s.add(token.start[0])
        elif token.type == tokenize.STRING:
             # If it's not a docstring... difficult to check context perfectly here.
             # We assume docstrings (triple quoted) are comments per requirements.
             if not (token.string.startswith('"""') or token.string.startswith("'''")):
                 for l in range(token.start[0], token.end[0]+1):
                     s.add(l)
    return s


def count_lines_generic(file_path: Path) -> Tuple[int, int, int]:
    """
    Simple counter for non-python files.
    """
    total = 0
    code = 0
    comment = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total += 1
                stripped = line.strip()
                if not stripped:
                    continue
                
                if stripped.startswith('#') or stripped.startswith('//'):
                    comment += 1
                else:
                    code += 1
    except Exception:
        pass
        
    return total, code, comment

def print_table(title: str, headers: List[str], rows: List[List[str]], alignments: List[str]):
    """Print a formatted table."""
    print(f"\n[{title}]")
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Add padding
    col_widths = [w + 2 for w in col_widths]
    
    # Header
    header_str = ""
    for i, h in enumerate(headers):
        align = alignments[i]
        width = col_widths[i]
        if align == '<':
            header_str += f"{h:<{width}}"
        else:
            header_str += f"{h:>{width}}"
    print(header_str)
    print("-" * len(header_str))
    
    # Rows
    for row in rows:
        row_str = ""
        for i, cell in enumerate(row):
            align = alignments[i]
            width = col_widths[i]
            if align == '<':
                row_str += f"{str(cell):<{width}}"
            else:
                row_str += f"{str(cell):>{width}}"
        print(row_str)
    print("-" * len(header_str))

def main():
    parser = argparse.ArgumentParser(description="Count Lines of Code Analysis")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--target", help="Specific directory to scan (default: src/)")
    args = parser.parse_args()
    
    # Determine target and title
    if args.target:
        scan_root = Path(args.target).resolve()
        report_title = f"Legacy Code Assets ({scan_root.name})"
    else:
        # Default to src if no target specified
        scan_root = Path("src").resolve()
        if not scan_root.exists():
             # Fallback to current dir if src doesn't exist (e.g. run from wrong place)
             scan_root = Path(".").resolve()
             report_title = "Project Root Scan"
        else:
             report_title = "LCR Core & UI"
            
    if not scan_root.exists():
        print(f"[ERROR] Target directory not found: {scan_root}")
        sys.exit(1)
    
    # Excludes
    exclude_dirs = {'.venv', '__pycache__', '.git', 'build', 'dist', '.idea', '.vscode', 'node_modules', 'lcr.egg-info', 'core'} 
    # Note: 'core' exclusion logic might be tricky if user targets it. 
    # But usually we exclude generated/noise. I'll rely on standar excludes.
    # User requested: .venv, __pycache__, .git, build, dist.
    # Don't exclude 'core' source!
    exclude_dirs = {'.venv', '__pycache__', '.git', 'build', 'dist', '.idea', '.vscode', 'node_modules', 'lcr.egg-info'}

    # Aggregation Structures
    # Directory -> {files, total, code, comment}
    dir_stats = {}
    total_stats = {'files': 0, 'total': 0, 'code': 0, 'comment': 0}
    
    # Traverse
    for root, dirs, files in os.walk(scan_root):
        # Modify dirs in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        rel_path = Path(root).relative_to(scan_root.parent).as_posix()
        if rel_path == ".": rel_path = scan_root.name
        
        # Use relative path from scan_root for clearer grouping?
        # User wants "Directory-based aggregation".
        # Let's group by relative directory path.
        try:
            display_dir = Path(root).relative_to(scan_root).as_posix()
            if display_dir == ".": display_dir = "(root)"
        except ValueError:
            display_dir = Path(root).name
            
        if display_dir not in dir_stats:
            dir_stats[display_dir] = {'files': 0, 'total': 0, 'code': 0, 'comment': 0}
            
        for file in files:
            file_path = Path(root) / file
            # simple check to skip binary/unknown if needed, but we count all
            ext = file_path.suffix.lower()
            
            if ext == '.py':
                t, c, cm = count_lines_python(file_path)
            else:
                t, c, cm = count_lines_generic(file_path)
            
            # Add to dir stats
            dir_stats[display_dir]['files'] += 1
            dir_stats[display_dir]['total'] += t
            dir_stats[display_dir]['code'] += c
            dir_stats[display_dir]['comment'] += cm
            
            # Add to total
            total_stats['files'] += 1
            total_stats['total'] += t
            total_stats['code'] += c
            total_stats['comment'] += cm

    # Calculate Summaries
    sloc = total_stats['code']
    total_lines_sum = total_stats['total']
    comment_sum = total_stats['comment']
    
    avg_comment_ratio = 0.0
    if (sloc + comment_sum) > 0:
        avg_comment_ratio = (comment_sum / (sloc + comment_sum)) * 100
    
    # Output
    if args.json:
        output = {
            "title": report_title,
            "summary": {
                "total_files": total_stats['files'],
                "total_sloc": sloc,
                "total_lines": total_lines_sum,
                "comment_ratio_percent": round(avg_comment_ratio, 2)
            },
            "directories": dir_stats
        }
        print(json.dumps(output, indent=2))
    else:
        # Table 1: Directory Breakdown
        headers = ["Directory", "Files", "Total", "Code", "Comment"]
        rows = []
        # sort by directory name
        sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[0])
        
        for d, s in sorted_dirs:
            # Filter out empty dirs
            if s['files'] > 0:
                rows.append([d, s['files'], s['total'], s['code'], s['comment']])
                
        print_table(report_title + " - Directory Breakdown", headers, rows, ['<', '>', '>', '>', '>'])
        
        # Summary Section
        print(f"\n[Summary Report]")
        print(f"{'Total Files Analyzed':<25}: {total_stats['files']}")
        print(f"{'Total Layout Lines':<25}: {total_lines_sum}")
        print(f"{'Total SLOC':<25}: {sloc}")
        print(f"{'Total Comments':<25}: {comment_sum}")
        print(f"{'Comment Ratio':<25}: {avg_comment_ratio:.1f}%")
        print("=" * 40)

if __name__ == "__main__":
    main()
