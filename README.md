# 文档说明

``` Plaintext

MyToolbox/
│
├── config.py                  # ⚙️ 配置文件 (定义颜色 #EDF5FC 及三级菜单路由)
├── main.py                    # 🚀 主程序入口
│
├── core/                      # 🧠 核心 UI 组件
│   ├── top_navbar.py          # 顶部导航栏 (一级菜单)
│   └── tool_grid_view.py      # 工具网格展示卡片区 (二级页面)
│
└── views/                     # 📦 业务工具弹窗 (三级弹窗)
    └── office/
        └── pdf_crop_dialog.py # 📄 PDF截取合并工具 (独立弹窗 CTkToplevel)

```

## 新环境安装配置

```bash

py -m pip install -r requirements.txt
```


## 打包代码

``` bash

py -m PyInstaller -F -w --add-data "assets;assets" main.py


py -m PyInstaller -n "千城工具箱" -i "assets/app.ico" -F -w --add-data "assets;assets" main.py
```