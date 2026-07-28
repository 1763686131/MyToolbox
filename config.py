import customtkinter as ctk
import os
import sys

# 软件外观配置
APP_TITLE = "千城工具箱"  #名字
WINDOW_SIZE = "1050x650" #屏幕尺寸
BG_COLOR = "#EDF5FC"  #背景颜色

# --- 兼容 PyInstaller 打包 ---
if getattr(sys, 'frozen', False):
    # 如果运行的是打包后的 .exe 文件，使用临时解压目录
    BASE_DIR = sys._MEIPASS
else:
    # 如果运行的是 .py 源码文件，使用当前文件所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))



def get_tool_path(exe_name):
    """
    全局公共方法：智能获取外部 .exe 工具的真实绝对路径
    """
    # 1. 智能获取运行目录（兼容纯代码运行和打包后运行）
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
        
    # 2. 拼接并返回最终的工具路径
    return os.path.join(base_dir, "tools", exe_name)



# 字体配置
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


# 字体函数
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
            {
                "id": "online_pdf",
                "name": "在线 PDF 转换",
                "desc": "无需下载，在浏览器中一键转换 PDF",
                "icon": "assets/icon/PDF.png",  # 你自己准备个图标就行
                
                # 🔥 重点：没有任何复杂的弹窗配置，只要填上网址！
                "url": "https://www.ilovepdf.com/zh-cn"
            },
            
        ],
    },
    {
        "id": "system",
        "name": "系统维护",
        "tools": [
           {
                "id": "driver_master",
                "name": "360驱动大师",
                "desc": "装机必备网卡驱动软件",
                "icon": "assets/icon/360.png",
                "dialog_module": "views.system.cloud_tool_dialog", 
                "dialog_class": "CloudToolDialog",
                # 直接在这里把参数传过去！
                "exe_name": "360驱动大师网卡版2.0.0.2040.exe" 
            },
        ],
    },
    {
        "id": "game",
        "name": "游戏",
        "tools": [],
    },
]

# 本地测试用 127.0.0.1，以后你只需要在这里把网址改成你的花生壳域名，全软件生效！
API_BASE_URL = "http://127.0.0.1:4566" 

def get_api_download_url(exe_name):
    """
    全局公共方法：智能生成云端下载完整链接
    """
    return f"{API_BASE_URL}/api/tools/{exe_name}/download"



# 个人中心（右侧固定项）
USER_CENTER_ITEM = {"id": "user_center", "name": "个人中心"}