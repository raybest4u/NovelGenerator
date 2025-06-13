

# 项目目录结构
```
fantasy_novel_mcp/
├── config/
│   ├── __init__.py
│   ├── settings.py           # 配置管理
│   └── prompts/             # 提示词模板
│       ├── worldbuilding.yaml
│       ├── character.yaml
│       ├── plot.yaml
│       └── writing.yaml
├── core/
│   ├── __init__.py
│   ├── llm_client.py        # LLM客户端封装
│   ├── mcp_server.py        # MCP服务器
│   └── base_tools.py        # 基础工具类
├── modules/
│   ├── __init__.py
│   ├── worldbuilding/       # 世界观构建模块
│   │   ├── __init__.py
│   │   ├── world_generator.py
│   │   ├── magic_system.py
│   │   └── geography.py
│   ├── character/           # 角色管理模块
│   │   ├── __init__.py
│   │   ├── character_creator.py
│   │   ├── relationship.py
│   │   └── development.py
│   ├── plot/                # 情节规划模块
│   │   ├── __init__.py
│   │   ├── story_planner.py
│   │   ├── conflict_generator.py
│   │   └── arc_manager.py
│   ├── writing/             # 写作模块
│   │   ├── __init__.py
│   │   ├── chapter_writer.py
│   │   ├── scene_generator.py
│   │   ├── dialogue_writer.py
│   │   └── description_writer.py
│   └── tools/               # 工具集合
│       ├── __init__.py
│       ├── name_generator.py
│       ├── timeline_manager.py
│       └── consistency_checker.py
├── data/
│   ├── templates/           # 模板数据
│   ├── references/          # 参考资料
│   └── generated/           # 生成的小说
├── tests/
│   ├── __init__.py
│   ├── test_worldbuilding.py
│   ├── test_character.py
│   ├── test_plot.py
│   └── test_writing.py
├── requirements.txt
├── setup.py
├── README.md
└── main.py                  # 主入口
```



## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。


