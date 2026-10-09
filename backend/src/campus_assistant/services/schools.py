import ipaddress
import json
import re
from dataclasses import dataclass
from pathlib import Path

from campus_assistant.schemas.chat import ChatRequest


@dataclass(frozen=True)
class School:
    id: str
    name: str
    domain: str
    province: str = ''
    city: str = ''
    code: str = ''
    pinyin: str = ''
    initials: str = ''
    level: str = '本科'


CATALOGUE = json.loads((Path(__file__).resolve().parents[1] / 'data/schools.json').read_text(encoding='utf-8'))
SCHOOLS = tuple(School(**school) for school in CATALOGUE['schools'])
SCHOOL_BY_ID = {school.id: school for school in SCHOOLS}


def resolve_school(request: ChatRequest) -> School:
    if request.school_id in SCHOOL_BY_ID:
        return SCHOOL_BY_ID[request.school_id]  # Server registry wins over client values.
    name = (request.school_name or "").strip()
    domain = (request.school_domain or "").strip().lower().removeprefix("www.")
    try:
        domain = domain.encode("idna").decode("ascii")
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("院校域名不能是 IP 地址")
    if (not request.school_id.startswith("custom-") or not name or len(name) < 2
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", domain)
            or "." not in domain or ".." in domain
            or domain.endswith((".localhost", ".local", ".internal"))):
        raise ValueError("请提供有效院校名称和官网域名，例如 example.edu.cn")
    return School(request.school_id, name, domain)
