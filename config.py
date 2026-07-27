import customtkinter as ctk
import os

# 软件外观配置
APP_TITLE = "千城工具箱"
WINDOW_SIZE = "1050x650"
BG_COLOR = "#EDF5FC"  # 🎯 你的指定背景色

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_FILE_NAME = "AlimamaFangYuanTiVF-Thin-2.ttf"
FONT_FAMILY = "阿里妈妈方圆体 VF SemiBold"
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", FONT_FILE_NAME)


# 自动注册并加载字体包
if os.path.exists(FONT_PATH):
  try:
    ctk.FontManager.load_font(FONT_PATH)
    print(f"✅ 成功加载字体: {FONT_FILE_NAME}")
  except Exception as e:
    print(f"⚠️ 字体加载失败: {e}")
else:
  print(f"⚠️ 未找到字体文件，请检查路径: {FONT_PATH}")



def get_font(size=12, weight="normal"):
  """全局统一字体获取函数"""
  return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


# 三级架构配置
# Level 1: 顶部导航分类 -> Level 2: 页面工具列表 -> Level 3: 点击弹出工具窗口类
NAV_MENU = [
    {
        "id": "office",
        "name": "办公工具",
        "tools": [
            {
                "id": "pdf_crop",
                "name": "PDF分割合并工具",
                "desc": "批量将PDF页面截取上半部分并整合为一个文档",
                "icon": "assets/icon/PDF.png",
                "dialog_module": "views.office.pdf_crop_dialog",
                "dialog_class": "PDFCropDialog",  # 三级弹窗类
            },
            # 💡 以后有新的办公工具，直接在此追加卡片字典即可
        ],
    },
    {
        "id": "system",
        "name": "系统维护",
        "tools": [],
    },
    {
        "id": "game",
        "name": "游戏",
        "tools": [],
    },
]

# 个人中心（右侧固定项）
USER_CENTER_ITEM = {"id": "user_center", "name": "个人中心"}