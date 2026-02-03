#!/usr/bin/env python3
"""
Create Evolution Task - Helper script to create evolution tasks in Notion

This script parses evolution task files and creates corresponding
entries in the Notion Evolution Database.

Usage:
    python create_evolution_task.py <task_file.md>
    python create_evolution_task.py --title "Task Title" --type code --level 2 --description "Description"
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.notion_service import notion_service


def parse_evolution_file(file_path: str) -> dict:
    """Parse an evolution task markdown file into a task dict."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    task = {
        "title": "",
        "type": "code",
        "level": "Level 3",
        "description": "",
        "files_modified": "",
        "verification_steps": ""
    }

    # Extract title from first heading
    title_match = re.search(r'^#\s*進化任務[：:]\s*(.+)$', content, re.MULTILINE)
    if title_match:
        task["title"] = title_match.group(1).strip()
    else:
        # Fallback: use first heading
        heading_match = re.search(r'^#\s*(.+)$', content, re.MULTILINE)
        if heading_match:
            task["title"] = heading_match.group(1).strip()

    # Extract safety level
    level_match = re.search(r'Level[：:\s]*(\d)', content, re.IGNORECASE)
    if level_match:
        task["level"] = f"Level {level_match.group(1)}"

    # Extract sections
    sections = {
        "目標": "description",
        "描述": "description",
        "Description": "description",
        "修改範圍": "files_modified",
        "Files": "files_modified",
        "修改檔案": "files_modified",
        "驗證方式": "verification_steps",
        "驗證": "verification_steps",
        "Verification": "verification_steps",
    }

    for section_name, field_name in sections.items():
        pattern = rf'##\s*{section_name}.*?\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            task[field_name] = match.group(1).strip()

    # Detect type from content
    if "prompt" in content.lower() or "system_prompt" in content.lower():
        task["type"] = "prompt"
    elif "frontend" in content.lower() or "web-frontend" in content.lower():
        task["type"] = "frontend"
    elif "config" in content.lower() or ".env" in content.lower():
        task["type"] = "config"
    else:
        task["type"] = "code"

    return task


async def create_task_from_file(file_path: str) -> str:
    """Create a Notion task from a markdown file."""
    task = parse_evolution_file(file_path)

    if not task["title"]:
        task["title"] = Path(file_path).stem

    task_id = await notion_service.create_evolution_task(
        title=task["title"],
        task_type=task["type"],
        level=task["level"],
        description=task["description"],
        files_modified=task["files_modified"],
        verification_steps=task["verification_steps"]
    )

    return task_id


async def create_task_from_args(
    title: str,
    task_type: str,
    level: int,
    description: str,
    files_modified: str = "",
    verification_steps: str = ""
) -> str:
    """Create a Notion task from command line arguments."""
    task_id = await notion_service.create_evolution_task(
        title=title,
        task_type=task_type,
        level=f"Level {level}",
        description=description,
        files_modified=files_modified,
        verification_steps=verification_steps
    )

    return task_id


async def main():
    parser = argparse.ArgumentParser(description="Create Evolution Task in Notion")
    parser.add_argument("file", nargs="?", help="Path to evolution task markdown file")
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--type", choices=["prompt", "code", "frontend", "config"], default="code", help="Task type")
    parser.add_argument("--level", type=int, choices=[0, 1, 2, 3], default=3, help="Safety level (0-3)")
    parser.add_argument("--description", help="Task description")
    parser.add_argument("--files", help="Files to modify (newline-separated)")
    parser.add_argument("--verification", help="Verification steps")

    args = parser.parse_args()

    if args.file:
        # Create from file
        if not Path(args.file).exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        task_id = await create_task_from_file(args.file)
        print(task_id)

    elif args.title and args.description:
        # Create from arguments
        task_id = await create_task_from_args(
            title=args.title,
            task_type=args.type,
            level=args.level,
            description=args.description,
            files_modified=args.files or "",
            verification_steps=args.verification or ""
        )
        print(task_id)

    else:
        print("Error: Either provide a task file or --title and --description", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
