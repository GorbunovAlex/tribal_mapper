import argparse
import asyncio
import logging
import sys
from pathlib import Path

from domain.entities.code_module import CodeModule
from infrastructure.di_container import Container

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mapper", description="AI Tribal Knowledge Mapper"
    )
    sub = parser.add_subparsers(dest="command")

    idx = sub.add_parser("index", help="Index a codebase or single module")
    idx.add_argument("path", help="Root path to the repository")
    idx.add_argument(
        "--module",
        default=None,
        help="Index a single module instead of the whole codebase",
    )

    args = parser.parse_args()

    if args.command == "index":
        container = Container(root=args.path)

        if not container.config.openai_api_key:
            print(
                "Error: OpenAI API key not configured.\n"
                "Set 'openai_api_key' in config/mapper.yaml "
                "or export OPENAI_API_KEY env var."
            )
            sys.exit(1)

        if args.module:
            _index_single_module(container, args.path, args.module)
        else:
            report = asyncio.run(container.index_codebase.execute(args.path))
            print(
                f"Indexing complete: {report.succeeded} succeeded, "
                f"{report.skipped} skipped, {report.failed} failed"
            )
            for err in report.errors:
                print(f"  ERROR: {err}")
    else:
        parser.print_help()


def _index_single_module(container: Container, root: str, module_path: str) -> None:
    fpath = Path(root) / module_path
    if not fpath.is_file():
        print(f"File not found: {fpath}")
        return

    try:
        content = fpath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Cannot read {fpath}: {e}")
        return

    module = CodeModule(
        file_path=module_path,
        raw_content=content,
        language=fpath.suffix.lstrip("."),
    )
    ok = container.index_module.execute(module)
    if ok:
        print(f"Indexed: {module_path}")
    else:
        print(f"Skipped: {module_path} (validation failed)")


if __name__ == "__main__":
    main()
