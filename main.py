import config
import customtkinter as ctk
from core.tool_grid_view import ToolGridView
from core.top_navbar import TopNavbar

# 让打包软件 PyInstaller 识别并包含视图模块（不要删除）
import views.office.pdf_crop_dialog
import views.system.cloud_tool_dialog


class MainApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # 基本设置
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)

        # 🎯 设置主窗口整体背景色
        self.configure(fg_color=config.BG_COLOR)

        # 1. 挂载顶部导航栏 (一级)
        self.navbar = TopNavbar(self, on_category_change=self.on_category_change)
        self.navbar.pack(fill="x", padx=20, pady=(15, 10))

        # 2. 挂载二级工具卡片网格容器
        self.grid_view = ToolGridView(self)
        self.grid_view.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. 💡 核心修复：动态默认选中 appdata.json 里的第一个分类（不再写死 "office"）
        if config.NAV_MENU:
            first_category_id = config.NAV_MENU[0]["id"]
            self.navbar.select_tab(first_category_id)
        else:
            # 如果 appdata.json 是空的，默认切换到个人中心
            self.navbar.select_tab("user_center")

    def on_category_change(self, cat_id):
        """一级菜单切换触发"""
        self.grid_view.render_category(cat_id)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()