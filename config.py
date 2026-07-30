import json
import os
import sys
import customtkinter as ctk

# ==========================================
# 1. 基础外观与环境配置
# ==========================================
APP_TITLE = "千城工具箱"  #名字
WINDOW_SIZE = "1050x650" #屏幕尺寸
BG_COLOR = "#EDF5FC" #背景颜色

# 用户登录状态
CURRENT_USER = None

# API 接口地址 (根据你的真实 NAS IP / Docker 端口修改)
API_BASE_URL = "http://127.0.0.1:4566"

# --- 智能获取项目根目录 (兼容 PyInstaller 打包) ---
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==========================================
# 2. 动态读取 appdata.json 数据库引擎
# ==========================================
def load_appdata():
    """从本地 appdata.json 读取菜单与工具数据（带精确定位日志）"""
    # 💡 核心修改：在路径拼接中加入 "data" 文件夹
    json_path = os.path.join(BASE_DIR, "data", "appdata.json")

    # 兼容检查
    if not os.path.exists(json_path):
        json_path = os.path.join(os.getcwd(), "data", "appdata.json")

    print(f"🔍 正在尝试读取数据库路径: {json_path}")

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            formatted_menu = []
            for cat in data.get("categories", []):
                cat_item = {
                    "id": cat.get("category_id") or cat.get("id"),
                    "name": cat.get("category_name") or cat.get("name"),
                    "tools": [],
                }

                for t in cat.get("tools", []):
                    tool_item = dict(t)
                    if "id" not in tool_item and "tool_id" in tool_item:
                        tool_item["id"] = tool_item["tool_id"]

                    if "sub_dir" not in tool_item and "path" in tool_item:
                        parts = tool_item["path"].replace("\\", "/").split("/")
                        if len(parts) >= 3:
                            tool_item["sub_dir"] = parts[1]
                        else:
                            tool_item["sub_dir"] = "others"

                    cat_item["tools"].append(tool_item)

                formatted_menu.append(cat_item)

            print("✅ 成功加载本地 appdata.json 数据库数据！")
            return formatted_menu
        except Exception as e:
            # 💡 关键：把具体的语法错误打印出来！
            print(f"❌ 读取 appdata.json 失败，具体语法/解析错误为: {e}")
    else:
        print(f"❌ 文件未找到，请确认 {json_path} 是否真实存在！")

    print("⚠️ 启动空菜单备用机制。")
    return []

# 初始化全局菜单数据
NAV_MENU = load_appdata()


def reload_appdata():
    """热刷新函数：当从 NAS 同步并覆盖了本地 appdata.json 后调用，无需重启应用"""
    global NAV_MENU
    NAV_MENU = load_appdata()
    return NAV_MENU


# ==========================================
# 3. 公共实用辅助函数
# ==========================================
def get_tool_path(exe_name, sub_dir="others"):
    """智能拼接外部 .exe 工具在本地 tools 文件夹下的绝对路径"""
    return os.path.join(BASE_DIR, "tools", sub_dir, exe_name)


def get_api_download_url(exe_name, sub_dir="others"):
    """获取 NAS 云端下发文件的 API 链接"""
    return f"{API_BASE_URL}/api/tools/{sub_dir}/{exe_name}/download"


# ==========================================
# 4. 字体与 UI 统一配置
# ==========================================
FONT_FILE_NAME = "AlimamaFangYuanTiVF-Thin-2.ttf"
FONT_FAMILY = "AlimamaFangYuanTi VF SemiBold"
FONT_PATH = os.path.join(BASE_DIR, "assets", "font", FONT_FILE_NAME)


def get_font(size=12, weight="normal"):
    """获取自定义字体的统一入口"""
    try:
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
    except Exception:
        return ("Microsoft YaHei", size, weight)


USER_CENTER_ITEM = {"id": "user_center", "name": "个人中心"}