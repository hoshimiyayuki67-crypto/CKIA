import asyncio
import json

import httpx

from campus_assistant.intelligence.deepseek import DeepSeek, supported_quote


def test_one_invalid_summary_section_does_not_discard_supported_sections():
    result = {'points': [
        {'heading': '办理步骤', 'text': '在校生可自助打印成绩单。',
         'support': [{'reference': 'web-1', 'quote': '在校生自助打印'}]},
        {'heading': '错误段落', 'text': '没有依据的规定',
         'support': [{'reference': 'web-1', 'quote': '伪造引文'}]},
        {'heading': 'x' * 40, 'text': '超长标题也不能影响有效段落',
         'support': [{'reference': 'web-1', 'quote': '在校生自助打印'}]}]}

    def handle(request):
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps(result)}}]})
    model = DeepSeek('key', transport=httpx.MockTransport(handle))
    points = asyncio.run(model.summarize('成绩单', '学校', {'web-1': '在校生自助打印成绩单'}))
    assert len(points) == 1 and points[0].heading == '办理步骤'


def test_quote_formatting_uses_original_source_and_rejects_changed_facts():
    source = '在校生可在**自助打印机**\n\n办理成绩单，每份10元。'
    quote = supported_quote(source, '在校生可在自助打印机 办理成绩单，每份10元。')
    assert quote is not None and quote in source
    assert supported_quote(source, '在校生可在自助打印机办理成绩单，每份5元。') is None
    assert supported_quote(source, '在校生……每份10元。') is None
    source = '学生／校友—学生服务中心，每份10元。'
    assert supported_quote(source, '学生/校友–学生服务中心，每份10元。') in source
