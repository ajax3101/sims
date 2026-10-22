"""sims import <file-or-dir>... — import rosters into the database configured by SIMS_DATABASE_URL."""
import argparse
import asyncio
import sys
from collections.abc import Iterable
from pathlib import Path

from sims.core.db import create_engine, make_sessionmaker
from sims.modules.imports.import_service import SUPPORTED_SUFFIXES, import_file
from sims.modules.imports.schemas import ImportReport


def collect_files(paths: Iterable[Path | str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(
                x for x in p.iterdir()
                if x.is_file() and x.suffix.lower() in SUPPORTED_SUFFIXES and not x.name.startswith("~$")
            )
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(p)
    return files


def format_report(r: ImportReport) -> str:
    d = r.dictionaries_created
    lines = [
        f"{r.source_filename} — {r.status}",
        f"  студентів: створено {r.students_created}, оновлено {r.students_updated}, дублікатів {r.duplicates}"
        f" | груп нових {r.groups_created}, наявних {r.groups_matched}"
        f" | довідники: org_unit {d['org_unit']}, program {d['program']}, specialty {d['specialty']}"
        f" | помилок {r.errors}, попереджень {r.warnings}",
    ]
    for i in r.issues:
        where = " ".join(f"{k}={v}" for k, v in i.location.items())
        lines.append(f"  {i.severity.upper()} {i.code} [{where}] {i.message}")
    return "\n".join(lines)


async def _import(paths: list[Path], database_url: str | None) -> list[ImportReport]:
    engine = create_engine(database_url)
    sessions = make_sessionmaker(engine)
    reports = []
    try:
        for path in paths:
            async with sessions() as session:
                reports.append(await import_file(session, path))
            print(format_report(reports[-1]), flush=True)
    finally:
        await engine.dispose()
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sims")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="import .docx/.xlsx rosters (files or directories)")
    imp.add_argument("paths", nargs="+", type=Path)
    imp.add_argument("--database-url", help="overrides SIMS_DATABASE_URL")
    args = parser.parse_args(argv)

    files = collect_files(args.paths)
    reports = asyncio.run(_import(files, args.database_url))
    total = sum(r.students_created for r in reports)
    errors = sum(r.errors for r in reports)
    print(f"\nфайлів {len(reports)}, нових студентів {total}, помилок {errors}")
    return 1 if errors or any(r.status != "done" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
