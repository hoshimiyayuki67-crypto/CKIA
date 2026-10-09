# 本科院校目录

schools.json 以教育部2026-06-17全国普通高等学校名单筛选本科层次，1412条，包含职业本科，不含港澳台和专科学校。
来源：https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/202606/t20260618_1441074.html
官网域名以现有四所院校配置优先，其余按名称精确匹配公开参考数据：
https://github.com/FitchCode/AllShoolData/blob/master/全国高校信息(json数据格式).json
参考数据可能存在旧域名；未匹配时保留空值，禁止臆造域名。
联网时仅接受匹配学校全称的.edu.cn首页发现，再限定该域名搜索。
未确认官网时给出明确提示，用户可指定官网；不降级为其他学校的结果。
脚本scripts/import_release_data.py生成服务端JSON、客户端JSON和编译内置目录，断网也可选择、搜索院校。
