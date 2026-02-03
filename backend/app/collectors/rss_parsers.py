import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from app.utils.timezone import SOURCE_TIMEZONES
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class RSSParser(ABC):
    def __init__(self, source_name: str = "unknown"):
        self.source_name = source_name

    @abstractmethod
    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        pass

    @abstractmethod
    def parse_title(self, item: ET.Element) -> Optional[str]:
        pass

    @abstractmethod
    def parse_link(self, item: ET.Element) -> Optional[str]:
        pass

    @abstractmethod
    def parse_content(self, item: ET.Element) -> Optional[str]:
        pass

    @abstractmethod
    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        pass


class RSS20Parser(RSSParser):
    def __init__(self, source_name: str = "unknown"):
        super().__init__(source_name=source_name)

    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        return root.findall(".//item")

    def parse_title(self, item: ET.Element) -> Optional[str]:
        elem = item.find("title")
        if elem is not None and elem.text:
            return self._clean_cdata(elem.text.strip())
        return None

    def parse_link(self, item: ET.Element) -> Optional[str]:
        elem = item.find("link")
        if elem is not None and elem.text:
            return self._clean_cdata(elem.text.strip())
        return None

    def parse_content(self, item: ET.Element) -> Optional[str]:
        for field in ["description", "content", "content:encoded"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                content = self._clean_cdata(elem.text.strip())
                content = re.sub(r"<[^>]+>", "", content)
                return content[:1000] if content else None
        return None

    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        candidates = [
            "pubDate",
            "{http://purl.org/dc/elements/1.1/}date",
        ]

        for tag in candidates:
            elem = item.find(tag)
            if elem is not None and elem.text:
                parsed = self._parse_datetime(elem.text.strip())
                if parsed is not None:
                    return parsed

        for child in list(item):
            if child.text is None:
                continue
            tag = child.tag
            local_name = tag.split("}", 1)[1] if "}" in tag else tag
            if local_name.lower() not in {"pubdate", "date", "published", "updated"}:
                continue
            parsed = self._parse_datetime(child.text.strip())
            if parsed is not None:
                return parsed

        return None

    @staticmethod
    def _clean_cdata(text: str) -> str:
        if text.startswith("<![CDATA[") and text.endswith("]]>"):
            return text[9:-3].strip()
        return text

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None

        cleaned = re.sub(r"\s+", " ", date_str.strip())
        default_tz = SOURCE_TIMEZONES.get(self.source_name, ZoneInfo("UTC"))
        if default_tz.key == "Asia/Shanghai":
            cleaned = re.sub(r"\bCST\b$", "+0800", cleaned)

        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(cleaned)
            if dt is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=default_tz)
                dt = dt.astimezone(timezone.utc)
                return self._validate_and_fix_datetime(dt, date_str)
        except (TypeError, ValueError):
            pass

        try:
            dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=default_tz)
            dt = dt.astimezone(timezone.utc)
            return self._validate_and_fix_datetime(dt, date_str)
        except ValueError:
            pass

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=default_tz)
                dt = dt.astimezone(timezone.utc)
                return self._validate_and_fix_datetime(dt, date_str)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def _validate_and_fix_datetime(
        dt: datetime, original_str: str
    ) -> Optional[datetime]:
        now = datetime.now(timezone.utc)
        diff = (dt - now).total_seconds()

        if diff > 86400:
            try:
                fixed_dt = dt.replace(year=dt.year - 1)
                new_diff = (fixed_dt - now).total_seconds()
                if -31536000 < new_diff <= 86400:
                    logger.warning(
                        f"Date '{original_str}' ({dt.isoformat()}) is in future. "
                        f"Corrected year from {dt.year} to {fixed_dt.year}"
                    )
                    return fixed_dt
            except ValueError:
                pass

            logger.warning(
                f"Date '{original_str}' ({dt.isoformat()}) is too far in future. "
                f"Treating it as invalid."
            )
            return None

        return dt


class AtomParser(RSSParser):
    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        return root.findall(f".//{self.ATOM_NS}entry")

    def parse_title(self, item: ET.Element) -> Optional[str]:
        elem = item.find(f"{self.ATOM_NS}title")
        if elem is not None and elem.text:
            return elem.text.strip()
        return None

    def parse_link(self, item: ET.Element) -> Optional[str]:
        elem = item.find(f"{self.ATOM_NS}link")
        if elem is not None:
            return elem.get("href")
        return None

    def parse_content(self, item: ET.Element) -> Optional[str]:
        for field in [f"{self.ATOM_NS}content", f"{self.ATOM_NS}summary"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                content = re.sub(r"<[^>]+>", "", elem.text.strip())
                return content[:1000] if content else None
        return None

    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        for field in [f"{self.ATOM_NS}published", f"{self.ATOM_NS}updated"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                try:
                    dt = datetime.fromisoformat(elem.text.strip().replace("Z", "+00:00"))
                    default_tz = SOURCE_TIMEZONES.get(self.source_name, ZoneInfo("UTC"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=default_tz)
                    return dt.astimezone(timezone.utc)
                except ValueError:
                    pass
        return None
