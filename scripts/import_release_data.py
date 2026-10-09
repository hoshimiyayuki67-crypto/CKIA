"""Reproducible import from MOE public XLS and user-provided Word extraction.

Operator dependencies: xlrd==2.0.2, pypinyin==0.55.0.
No API keys or personal chat data are involved.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import xlrd
from pypinyin import lazy_pinyin, Style

ROOT = Path(__file__).resolve().parents[1]
MOE = 'https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/t20260618_1441074.html'


def catalogue():
    sheet = xlrd.open_workbook(ROOT / 'artifacts/schools-2026.xls').sheet_by_index(0)
    overrides = {'内蒙古大学创业学院': ('imuchuangye', 'imuchuangye.cn'),
        '内蒙古大学': ('imu', 'imu.edu.cn'), '北京大学': ('pku', 'pku.edu.cn'),
        '清华大学': ('tsinghua', 'tsinghua.edu.cn')}
    website_file = ROOT / 'artifacts/school-websites.json'
    websites = json.loads(website_file.read_text(encoding='utf-8')) if website_file.exists() else {}
    schools, province = [], ''
    for row in range(3, sheet.nrows):
        values = sheet.row_values(row)
        if isinstance(values[0], str) and '所）' in values[0]:
            province = values[0].split('（')[0]
        if values[5] != '本科':
            continue
        name, code = values[1].strip(), str(int(values[2]))
        domain = urlsplit(websites.get(code, '')).hostname or ''
        domain = domain.lower().removeprefix('www.')
        if not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', domain):
            domain = ''
        school_id, domain = overrides.get(name, ('moe-' + code, domain))
        schools.append({'id': school_id, 'name': name, 'domain': domain,
            'province': province, 'city': str(values[4]), 'code': code,
            'pinyin': ''.join(lazy_pinyin(name)),
            'initials': ''.join(lazy_pinyin(name, style=Style.FIRST_LETTER)),
            'level': '本科'})
    assert len(schools) == 1412 and len({s['id'] for s in schools}) == 1412
    schools.sort(key=lambda s: (s['id'] != 'imuchuangye', s['code']))
    data = {'version': '2026-06-17', 'source': MOE, 'count': len(schools), 'schools': schools}
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    for output in ('backend/src/campus_assistant/data/schools.json', 'mobile/assets/schools.json'):
        path = ROOT / output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    def literal(value):
        return json.dumps(value, ensure_ascii=False).replace('$', r'\$')
    lines = ["// Generated from the MOE 2026 catalogue; regenerate with import_release_data.py.",
        "part of 'school.dart';", "const schoolCatalogue = <School>["]
    for school in schools:
        args = ', '.join(literal(school[key]) for key in ('id', 'name', 'domain'))
        fields = ', '.join(key + ': ' + literal(school[key]) for key in ('province', 'city', 'pinyin', 'initials', 'code'))
        lines.append(f'  School({args}, {fields}),')
    lines.append('];')
    (ROOT / 'mobile/lib/core/school_catalogue.g.dart').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('MOE undergraduate catalogue:', len(schools), 'website domains:', sum(bool(s['domain']) for s in schools))


def handbook():
    source = next((ROOT / 'knowledge/official').glob('*.doc'))
    raw = (ROOT / 'artifacts/handbook-2021.txt').read_text(encoding='utf-8')
    # Skip cover and contents. Preserve paragraphs and actual headings, no invented page numbers.
    start = raw.index('\f普通高等学校学生管理规定')
    headings = {re.sub(r'\t\d+\s*$', '', line).strip()
        for line in raw[:start].splitlines() if '\t' in line}
    headings.add('普通高等学校学生管理规定')
    text = raw[start:].replace('\x07', '\t')
    text = re.sub(r'[\ue000-\uf8ff]', '', text).replace('\v', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    paragraphs = [p.strip() for p in re.split(r'[\r\n\f]+', text) if p.strip()]
    def heading(value):
        return (value in headings or (len(value) < 90 and value.startswith('内蒙古大学创业学院')
            and not re.search(r'[。；：，]', value)
            and re.search(r'(办法|规定|流程|条例|章程|细则)([（(].*?[）)])?$', value)))
    merged, index = [], 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        if index + 1 < len(paragraphs) and paragraph.startswith('内蒙古大学创业学院') and len(paragraph) < 40:
            joined = paragraph + paragraphs[index + 1]
            if heading(joined):
                merged.append(joined)
                index += 2
                continue
        merged.append(paragraph)
        index += 1
    chunks, section, buffer = [], '普通高等学校学生管理规定', []
    def flush():
        if buffer:
            chunks.append((section, '\n'.join(buffer)))
            buffer.clear()
    for paragraph in merged:
        is_heading = heading(paragraph)
        if is_heading:
            flush()
            section = paragraph
        if sum(map(len, buffer)) + len(paragraph) > 1200:
            flush()
        buffer.append(paragraph)
    flush()
    entries = []
    for index, (heading, content) in enumerate(chunks, 1):
        entries.append({'school_id': 'imuchuangye', 'version': '2021-09',
            'reference_only': True, 'text': content,
            'source': {'doc_id': 'imuchuangye-handbook-2021', 'chunk_id': f'chunk-{index:03}',
                'title': '学生管理手册（2021年9月版） · ' + heading,
                'issuer': '内蒙古大学创业学院学生工作部（团委）', 'date': '2021-09-01',
                'date_precision': 'month', 'url': '/api/v1/documents/imuchuangye-handbook-2021'}})
    path = ROOT / 'knowledge/processed/documents/handbook-2021.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(json.dumps(e, ensure_ascii=False) for e in entries) + '\n', encoding='utf-8')
    manifest = {'doc_id': 'imuchuangye-handbook-2021', 'original_file': source.name,
        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'version': '2021-09',
        'chunks': len(entries), 'reference_only': True,
        'provenance': '用户提供原始DOC，封面注明2021年9月；未确认2026年仍有效，不能自动生成现行办事卡片。'}
    (ROOT / 'knowledge/official/handbook-2021.manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Historical handbook chunks:', len(entries))


if __name__ == '__main__':
    catalogue()
    handbook()
