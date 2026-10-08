const messages = document.querySelector('#messages');
const form = document.querySelector('#chat-form');
const question = document.querySelector('#question');
const send = document.querySelector('#send');
const notice = document.querySelector('#notice');

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function message(text, role) {
  const article = element('article', undefined, `message ${role}`);
  article.append(element('p', text));
  messages.append(article);
  return article;
}

function renderCard(article, card) {
  article.append(element('h2', card.matter_name));
  article.append(element('p', `适用对象：${card.target_users.join('、')}`));
  article.append(element('h3', '材料清单'));
  for (const material of card.materials) {
    const label = element('label', undefined, 'check');
    const checkbox = element('input');
    checkbox.type = 'checkbox';
    label.append(checkbox, element('span', `${material.item}${material.required ? '（必需）' : '（按需）'}${material.note ? ` · ${material.note}` : ''}`));
    article.append(label);
  }
  const details = element('dl');
  for (const [label, value] of [['办理地点', card.location], ['办公时间', card.office_hours], ['截止日期', card.deadline || '未查到明确期限'], ['办理方式', card.channel], ['咨询渠道', card.contact]]) {
    details.append(element('dt', label), element('dd', value));
  }
  article.append(details);
  for (const note of card.notes) article.append(element('p', note));
  for (const source of card.sources) {
    const line = element('p', `${source.issuer} · ${source.date} · `, 'source');
    let url;
    try { url = new URL(source.url); } catch { url = null; }
    if (url && ['http:', 'https:'].includes(url.protocol)) {
      const link = element('a', source.title);
      link.href = url.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      line.append(link);
    } else line.append(element('span', source.title));
    article.append(line);
  }
  article.append(element('p', '勾选仅记录本次页面准备进度，刷新后清空。'));
}

fetch('/health').then(response => {
  if (!response.ok) throw new Error('health');
  return response.json();
}).then(data => {
  notice.textContent = data.demo_mode
    ? '演示模式：仅含虚构测试数据，不是学校规定。可提问“测试馆借阅需要什么材料？”'
    : data.knowledge_status === 'loaded'
      ? '已加载资料；只回答已审核且未失效的事项。'
      : '校内资料尚未入库，当前会明确拒答。';
}).catch(() => { notice.textContent = '无法连接服务，请确认后端已启动。'; });

form.addEventListener('submit', async event => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value || send.disabled) return;
  message(value, 'user');
  send.disabled = true;
  send.textContent = '查询中…';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const category = document.querySelector('#category').value;
    const response = await fetch('/api/v1/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: value, ...(category ? { category } : {}) }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error('request');
    const data = await response.json();
    const article = message(`${data.demo_mode ? '【虚构演示】' : ''}${data.message}`, 'assistant');
    if (data.status === 'card' && data.card) renderCard(article, data.card);
    question.value = '';
    article.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch {
    message('暂时无法完成查询，请稍后重试；当前没有获得可核实的答案。', 'assistant');
  } finally {
    clearTimeout(timeout);
    send.disabled = false;
    send.textContent = '发送';
    question.focus();
  }
});
