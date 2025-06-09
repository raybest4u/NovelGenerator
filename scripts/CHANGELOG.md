
# CHANGELOG.md
# 更新日志

## [1.0.0] - 2024-12-19

### 新增功能
- ✨ 完整的MCP架构实现
- ✨ 世界观构建系统（世界生成、魔法体系、地理环境）
- ✨ 角色管理系统（角色创建、关系管理、发展规划）
- ✨ 情节规划引擎（故事大纲、冲突生成、弧线管理）
- ✨ 智能写作系统（章节写作、场景生成、对话写作、描述写作）
- ✨ 辅助工具集（名称生成、时间线管理、一致性检查）
- ✨ RESTful
API接口
- ✨ 命令行工具
- ✨ Docker容器化支持
- ✨ 完整的测试套件
- ✨ 监控和日志系统
- ✨ 性能优化功能
- ✨ 安全防护机制

### 技术特性
- 🔧 模块化架构设计
- 🔧 异步编程支持
- 🔧 数据库持久化
- 🔧 Redis缓存支持
- 🔧 多种LLM后端兼容
- 🔧 自动化CI / CD流程
- 🔧 代码质量检查
- 🔧 性能监控和指标收集

### 文档和示例
- 📚 完整的README文档
- 📚 API使用文档
- 📚 部署指南
- 📚 开发指南
- 📚 使用示例代码
- 📚 最佳实践指导

## [未来计划]

### v1.1.0
- 🚀 增强的世界观编辑器
- 🚀 可视化故事规划界面
- 🚀 多语言支持
- 🚀 导出格式扩展（EPUB、PDF等）

### v1.2.0
- 🚀 插件系统
- 🚀 模板市场
- 🚀 协作写作功能
- 🚀 AI写作助手

### v2.0.0
- 🚀 Web界面重构
- 🚀 移动端支持
- 🚀 云端服务版本
- 🚀 企业级功能

---

# LICENSE
MIT
License

Copyright(c)
2024
Fantasy
Novel
MCP

Permission is hereby
granted, free
of
charge, to
any
person
obtaining
a
copy
of
this
software and associated
documentation
files(the
"Software"), to
deal
in the
Software
without
restriction, including
without
limitation
the
rights
to
use, copy, modify, merge, publish, distribute, sublicense, and / or sell
copies
of
the
Software, and to
permit
persons
to
whom
the
Software is
furnished
to
do
so, subject
to
the
following
conditions:

The
above
copyright
notice and this
permission
notice
shall
be
included in all
copies or substantial
portions
of
the
Software.

THE
SOFTWARE
IS
PROVIDED
"AS IS", WITHOUT
WARRANTY
OF
ANY
KIND, EXPRESS
OR
IMPLIED, INCLUDING
BUT
NOT
LIMITED
TO
THE
WARRANTIES
OF
MERCHANTABILITY,
FITNESS
FOR
A
PARTICULAR
PURPOSE
AND
NONINFRINGEMENT.IN
NO
EVENT
SHALL
THE
AUTHORS
OR
COPYRIGHT
HOLDERS
BE
LIABLE
FOR
ANY
CLAIM, DAMAGES
OR
OTHER
LIABILITY, WHETHER
IN
AN
ACTION
OF
CONTRACT, TORT
OR
OTHERWISE, ARISING
FROM,
OUT
OF
OR
IN
CONNECTION
WITH
THE
SOFTWARE
OR
THE
USE
OR
OTHER
DEALINGS
IN
THE
SOFTWARE.

---

# CONTRIBUTING.md
# 贡献指南

感谢您对
Fantasy
Novel
MCP
项目的兴趣！我们欢迎各种形式的贡献。

## 贡献方式

### 报告问题
- 使用[GitHub
Issues](https: // github.com / your-repo / fantasy-novel-mcp / issues)
报告bug
- 提供详细的重现步骤
- 包含环境信息和错误日志

### 功能建议
- 在
Issues
中提出新功能建议
- 详细描述功能的用途和价值
- 提供使用场景和示例

### 代码贡献

#### 开发环境设置
```bash
# 1. Fork并克隆项目
git
clone
https: // github.com / your - username / fantasy - novel - mcp.git
cd
fantasy - novel - mcp

# 2. 设置开发环境
./ scripts / dev - setup.sh

# 3. 创建功能分支
git
checkout - b
feature / your - feature - name
```

#### 代码规范
- 遵循
PEP
8
代码风格
- 使用
black
进行代码格式化
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

#### 提交流程
```bash
# 1. 运行测试
make
test

# 2. 代码格式化
make
format

# 3. 代码检查
make
lint

# 4. 提交代码
git
add.
git
commit - m
"feat: 添加新功能描述"

# 5. 推送并创建PR
git
push
origin
feature / your - feature - name
```

### 文档贡献
- 改进现有文档
- 添加使用示例
- 翻译文档到其他语言
- 编写教程和指南

## 开发指南

### 项目结构
```
fantasy_novel_mcp /
├── config /  # 配置管理
├── core /  # 核心组件
├── modules /  # 功能模块
├── data /  # 数据层
├── tests /  # 测试代码
├── scripts /  # 工具脚本
├── examples /  # 使用示例
└── docs /  # 文档
```

### 添加新模块
1.在`modules / ` 下创建新目录
2.实现模块功能和工具
3.添加单元测试
4.更新文档
5.注册工具到主程序

### 测试要求
- 单元测试覆盖率 > 80 %
- 集成测试通过
- 性能测试无回归

## 社区准则

### 行为准则
- 尊重他人，友善交流
- 建设性地提出意见
- 帮助新贡献者
- 维护包容的社区环境

### 沟通渠道
- GitHub
Issues: 问题报告和功能讨论
- GitHub
Discussions: 一般讨论和问答
- Email: 私人或敏感问题

## 认可贡献者

我们感谢所有贡献者的付出：
- 代码贡献者将被列入
CONTRIBUTORS.md
- 重要贡献会在发布说明中特别感谢
- 长期贡献者可能被邀请成为维护者

## 获取帮助

如果您需要帮助：
1.查看现有文档和示例
2.搜索已有的 Issues
3.创建新的 Issue 或 Discussion
4.联系维护者

再次感谢您的贡献！🎉