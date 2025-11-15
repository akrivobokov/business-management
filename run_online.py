#!/usr/bin/env python
"""Helper to expose the calculator online without memorising Django commands."""
from __future__ import annotations

import argparse
import os
import sys


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Стартует Django-сервер калькулятора так, чтобы он был доступен онлайн "
            "(например, на 0.0.0.0:8000 на VPS или в контейнере)."
        )
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Хост (addr) для runserver. По умолчанию 0.0.0.0, чтобы сервер был доступен снаружи.",
    )
    parser.add_argument(
        "--port",
        default="8000",
        help="Порт HTTP. По умолчанию 8000.",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Отключить autoreload (полезно в проде/контейнере).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "business_management.settings")

    from django.core.management import call_command

    addr = f"{args.host}:{args.port}"
    runserver_args = [addr]
    runserver_kwargs = {"use_reloader": not args.no_reload}
    call_command("runserver", *runserver_args, **runserver_kwargs)


if __name__ == "__main__":
    main()
