# Backend Testing Guide

## 快速开始

```bash
cd backend

# 安装测试依赖（首次运行）
pip install -e ".[dev]"

# 运行全部测试
pytest

# 详细输出（显示每个测试用例名称）
pytest -v

# 只显示失败的测试
pytest --tb=short

# 运行单个测试文件
pytest tests/test_companies.py

# 运行单个测试类
pytest tests/test_validation.py::TestCompanyCreate -v

# 运行单个测试函数
pytest tests/test_companies.py::test_health_check -v

# 带覆盖率报告（需额外安装）
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

## 测试架构

```
tests/
├── conftest.py           # 全局 fixtures
├── test_companies.py     # API 端到端测试（12 个用例）
└── test_validation.py    # Pydantic 模型验证测试（15 个用例）
```

### conftest.py — 测试基础设施

| 组件 | 说明 |
|------|------|
| **内存数据库** | `sqlite:///:memory:`，不读写真实 `.db` 文件 |
| **client fixture** | 每个测试自动创建隔离的 `TestClient` |
| **自动清理** | 测试结束后自动 `drop_all` 清理数据 |
| **API Key** | 硬编码 `test-key`，无需真实 OpenRouter key |

### 测试覆盖范围

#### API 层 (`test_companies.py`)
- `test_health_check` — 健康检查端点
- `test_list_companies_empty` — 空列表返回
- `test_create_company` — 正常创建
- `test_create_company_invalid_status` — 非法 status → 422
- `test_create_company_missing_required_fields` — 缺少必填 → 422
- `test_create_company_name_too_long` — 超长字段 → 422
- `test_get_company` — 获取详情（含 interviews 关联）
- `test_get_company_not_found` — 不存在 → 404
- `test_update_company` — 部分更新
- `test_delete_company` — 删除后验证 404
- `test_list_companies_pagination` — skip/limit 分页
- `test_list_companies_invalid_pagination` — 负数 skip → 422
- `test_get_interview_chain_empty` — 空面试链

#### 模型验证 (`test_validation.py`)
- `CompanyCreate` — 7 个用例（空名、超长、非法 status、JD/notes 长度）
- `CompanyUpdate` — 3 个用例（部分更新、空名、非法 status）
- `MatchRequest` — 4 个用例（空 JD、超长文本）
- `ReviewRequest` — 5 个用例（空笔记、超长、轮次边界 1~50）
- `PrepRequest` — 3 个用例（天数边界 1~30）

## 注意事项

1. **测试不调用真实 LLM** — 只测 API 路由和 Pydantic 验证，AI 服务调用不在范围内
2. **不影响真实数据库** — 使用内存 SQLite，你的 `coachspark.db` 完全安全
3. **每次测试隔离** — fixture 自动建表/删表，测试之间无状态污染
4. **AI 端点未覆盖** — match/review/prep 的 AI 调用需要 mock LangGraph，当前未测试

## 新增测试

在对应文件添加函数即可，pytest 自动发现 `test_` 开头的函数：

```python
def test_your_new_feature(client):
    response = client.get("/api/v1/your-endpoint/")
    assert response.status_code == 200
```
