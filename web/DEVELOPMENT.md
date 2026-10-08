# H5 开发

当前是无构建依赖的原生 HTML/CSS/JS 预览，包含单页对话、类别筛选、卡片与材料勾选。由 FastAPI 同源服务：启动后访问 http://127.0.0.1:8000/。不能通过双击 index.html 调用接口。演示启动方式见 backend/DEVELOPMENT.md。

对话数据使用 textContent 渲染，来源链接限制 HTTP(S)，请求有超时与错误反馈。当前消息和勾选状态刷新后清空，尚未接入持久化、截图、语音、推送和 Flutter WebView。

后续通过 Flutter WebView 集成，仅开放受信任来源。桥接契约需要版本号、request_id、允许的 action、参数校验、结果和错误字段。相机、分享、缓存操作经 Flutter 执行；H5 不接触模型密钥。禁止任意 URL 调用原生桥接。
