# 商品评论采集与口碑洞察平台

抓取多站点商品评论，解析归一评分与情感，去重建档后形成口碑趋势与报告的数据采集与口碑分析平台

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/WorkbenchView.vue|tsx  全部模块共享工作台
│   ├── src/data/modules.ts              18个业务模块配置
│   ├── src/api/              统一请求封装
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/resource.py  通用查询/导出/登记/动作接口
│   ├── app/services/<key>.py    每个模块独立领域逻辑
│   ├── app/services/base.py     共享服务骨架
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 评论站点目录 | `review_site` | 站点配置 | 站点名称、站点类型、覆盖类目 |
| 关键词种子池 | `seed_keyword` | 关键词 | 关键词名称、所属类目、搜索意图 |
| 评论抓取任务 | `review_crawl` | 抓取任务 | 任务编号、站点标识、关键词标识 |
| 页面快文摘取 | `page_digest` | 页面摘录 | 摘录编号、任务编号、页面指纹 |
| 评论解析器 | `review_parse` | 解析规则 | 规则名称、站点标识、字段映射 |
| 评分归一 | `rating_norm` | 归一记录 | 记录编号、原始评分、评分制式 |
| 情感标注 | `sentiment_label` | 情感记录 | 记录编号、评论文本、情感极性 |
| 评论去重 | `review_dedup` | 去重记录 | 记录编号、评论指纹、相似簇号 |
| 作者画像 | `author_profile` | 作者档案 | 作者指纹、站点集合、活跃度等级 |
| 口碑情感库 | `review_sentiment_store` | 情感样本 | 样本编号、情感极性、强度分值 |
| 方面词抽取 | `aspect_extract` | 方面词 | 方面词名称、关联类目、出现频次 |
| 投诉聚类 | `complaint_cluster` | 投诉簇 | 簇编号、簇主题、簇内条数 |
| 趋势统计 | `trend_stat` | 趋势点 | 统计编号、统计周期、情感占比 |
| 抓取配额 | `crawl_quota` | 配额记录 | 配额编号、站点标识、日配额上限 |
| 验证码闸口 | `captcha_gate` | 闸口记录 | 闸口编号、站点标识、触发频率 |
| 失败重试队列 | `crawl_retry` | 重试项 | 队列编号、失败原因、重试次数 |
| 口碑导出中心 | `review_export` | 导出任务 | 导出编号、数据范围、字段清单 |
| 口碑报告 | `opinion_report` | 报告文档 | 报告编号、覆盖周期、正面要点 |
| 标注复核台 | `sentiment_review` | 复核事项 | 事项编号、争议样本、原标注 |
| 采集度量总览 | `platform_metrics` | 度量项 | 度量名称、统计窗口、当前值 |

## 约定

- 全部模块共享`frontend/src/views/WorkbenchView.vue|tsx`和一套资源路由。
- 每个模块仍保留独立`backend/app/services/<模块>.py`；纯前端保留
  `frontend/src/domain/<模块>.ts`，用于承载真实业务差异并维持36题位容量。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。

领域：数据工程
子方向：数据采集、爬虫与RPA
