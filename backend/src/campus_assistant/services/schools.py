import ipaddress
import re
from dataclasses import dataclass

from campus_assistant.schemas.chat import ChatRequest


@dataclass(frozen=True)
class School:
    id: str
    name: str
    domain: str


SCHOOLS = (
    School("imuchuangye", "内蒙古大学创业学院", "imuchuangye.cn"),
    School("imu", "内蒙古大学", "imu.edu.cn"),
    School("pku", "北京大学", "pku.edu.cn"),
    School("tsinghua", "清华大学", "tsinghua.edu.cn"),
)


def resolve_school(request: ChatRequest) -> School:
    for school in SCHOOLS:
        if request.school_id == school.id:
            return school  # Server registry wins over client-provided names/domains.
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
