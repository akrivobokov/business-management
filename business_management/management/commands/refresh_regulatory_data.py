import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from business_management.regulations import (
    DEFAULT_REGULATORY_DATA,
    get_regulatory_cache_path,
)


class Command(BaseCommand):
    help = (
        "Подтягивает справочники организационно-правовых форм и систем налогообложения "
        "из официальных источников ФНС России и обновляет локальный кэш."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Не выводить диагностические сообщения, только ошибки",
        )

    def handle(self, *args, **options):
        sources = getattr(settings, "REGULATORY_SOURCES", {})
        if not sources:
            self.stdout.write(self.style.WARNING("REGULATORY_SOURCES не настроены"))
            return

        opf_data = self._fetch_json(sources.get("opf"))
        tax_data = self._fetch_json(sources.get("tax_systems"))

        snapshot = {
            "checked_at": timezone.now().isoformat(),
            "sources": sources,
            "opf": self._extract_opf(opf_data),
            "tax_systems": self._extract_tax_systems(tax_data),
        }

        cache_path = get_regulatory_cache_path()
        cache_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

        if not options.get("quiet"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Кэш обновлён ({len(snapshot['opf'])} ОПФ, {len(snapshot['tax_systems'])} налоговых режимов)"
                )
            )

    def _fetch_json(self, url: str):
        if not url:
            return None
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError:
            return None

    def _extract_opf(self, payload):
        if not payload:
            return DEFAULT_REGULATORY_DATA["opf"]

        if isinstance(payload, dict):
            candidates = payload.get("data") or payload.get("result") or payload.get("records") or payload.get("items")
            if candidates is None and all(key.isdigit() for key in payload.keys()):
                candidates = payload.values()
        else:
            candidates = payload

        opf_items = []
        for item in candidates or []:
            code = (
                item.get("OPF")
                or item.get("OPF_CODE")
                or item.get("code")
                or item.get("id")
                or item.get("kod")
            )
            title = (
                item.get("FULLNAME")
                or item.get("OPF_NAME")
                or item.get("NAME")
                or item.get("name")
                or item.get("full_name")
            )
            if not code or not title:
                continue
            defaults = next((opf for opf in DEFAULT_REGULATORY_DATA["opf"] if opf["code"] == code), None)
            opf_items.append(
                {
                    "code": code,
                    "title": title,
                    "source_url": (item.get("source") or (defaults or {}).get("source_url")),
                    "tax_systems": (item.get("tax_systems") or (defaults or {}).get("tax_systems") or []),
                }
            )

        return opf_items or DEFAULT_REGULATORY_DATA["opf"]

    def _extract_tax_systems(self, payload):
        if not payload:
            return DEFAULT_REGULATORY_DATA["tax_systems"]

        if isinstance(payload, dict):
            candidates = payload.get("data") or payload.get("result") or payload.get("records") or payload.get("items")
            if candidates is None and all(key.isdigit() for key in payload.keys()):
                candidates = payload.values()
        else:
            candidates = payload

        systems = {}
        for item in candidates or []:
            code = (
                item.get("code")
                or item.get("tax_code")
                or item.get("id")
                or item.get("system")
                or item.get("regime")
            )
            if not code:
                continue
            defaults = DEFAULT_REGULATORY_DATA["tax_systems"].get(code, {})
            rate = item.get("rate") or item.get("tax_rate") or item.get("effective_rate")
            systems[code] = {
                "code": code,
                "title": item.get("title") or item.get("name") or defaults.get("title", code),
                "effective_rate": str(rate or defaults.get("effective_rate", "0")),
                "law_reference": item.get("law_reference") or defaults.get("law_reference"),
                "basis": item.get("basis") or defaults.get("basis", "revenue"),
                "source_url": item.get("source_url") or defaults.get("source_url"),
                "note": item.get("note") or defaults.get("note"),
            }

        return systems or DEFAULT_REGULATORY_DATA["tax_systems"]
