# 步骤记录器

> Android 自动化操作 App（Flet 子集版）

## 开发

```bash
# 安装依赖
uv sync

# 启动（开发模式，浏览器预览）
python main.py

# 跑测试
pytest

# 构建 APK（在TRAE云沙箱执行）
flet build apk --name step_recorder --version 0.1.0
```

## 目录结构

```
step_recorder/
├── main.py                # 入口
├── pyproject.toml         # 依赖配置
├── config/
│   └── settings.py        # 配置
├── views/
│   ├── home_view.py
│   ├── settings_view.py
│   └── components/
├── services/
│   └── storage.py
├── models/
│   ├── user.py
│   └── exceptions.py
├── controllers/
├── routes.py
├── i18n/
│   ├── zh.json
│   └── en.json
└── tests/
```

## 版本

- 0.1.0：初始版本
