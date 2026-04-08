import argparse
import asyncio
import logging

from infrastructure.di_container import Container

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(prog="mapper", description="AI Tribal Knowledge Mapper")
    sub = parser.add_subparsers(dest="command")

    idx = sub.add_parser("index", help="Index a codebase or single module")
    idx.add_argument("path", help="Root path to the repository")
    idx.add_argument("--module", default=None, help="Index a single module instead of the whole codebase")

    args = parser.parse_args()

    if args.command == "index":
        container = Container()
        report = asyncio.run(container.index_codebase.execute(args.path))
        print(
            f"Indexing complete: {report.succeeded} succeeded, "
            f"{report.skipped} skipped, {report.failed} failed"
        )
        for err in report.errors:
            print(f"  ERROR: {err}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
