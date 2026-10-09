import asyncio
import json

import httpx

from campus_assistant.intelligence.deepseek import DeepSeek


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
