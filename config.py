import customtkinter as ctk

# 软件外观配置
APP_TITLE = "千城工具箱"
WINDOW_SIZE = "1050x650"
BG_COLOR = "#EDF5FC"  # 🎯 你的指定背景色
FONT_FAMILY = "Microsoft JhengHei"

def get_font(size=12, weight="normal"):
  """统一字体获取函数

  💡 修复说明：像“幼圆”这种字体在 Windows 中没有独立的粗体(Bold)文件。
  如果强制传 weight="bold"，Tkinter 会加载失败并退回默认字体。
  因此这里拦截“幼圆”字体，统一使用 "normal" 字重。
  """
  target_weight = weight

  # 如果使用的是幼圆体，强制使用 normal 防崩
  if FONT_FAMILY in ["幼圆", "YouYuan"]:
    target_weight = "normal"

  return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=target_weight)


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
                "icon": "📄",
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