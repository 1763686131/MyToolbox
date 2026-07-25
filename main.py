import config
import customtkinter as ctk
from core.tool_grid_view import ToolGridView
from core.top_navbar import TopNavbar


class MainApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    # 基本设置
    self.title(config.APP_TITLE)
    self.geometry(config.WINDOW_SIZE)

    # 🎯 设置主窗口整体背景色为指定值 #EDF5FC
    self.configure(fg_color=config.BG_COLOR)

    # 1. 挂载顶部导航栏 (一级)
    self.navbar = TopNavbar(self, on_category_change=self.on_category_change)
    self.navbar.pack(fill="x", padx=20, pady=(15, 10))

    # 2. 挂载二级工具卡片网格容器
    self.grid_view = ToolGridView(self)
    self.grid_view.pack(fill="both", expand=True, padx=10, pady=10)

    # 3. 默认选中第一个分类（办公工具）
    self.navbar.select_tab("office")

  def on_category_change(self, cat_id):
    """一级菜单切换触发二级网格刷新"""
    self.grid_view.render_category(cat_id)


if __name__ == "__main__":
  app = MainApp()
  app.mainloop()