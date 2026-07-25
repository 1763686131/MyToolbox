import importlib
import config
import customtkinter as ctk


class ToolGridView(ctk.CTkScrollableFrame):

  """二级：工具网格容器 (展示工具卡片)"""

  def __init__(self, master, **kwargs):
    super().__init__(
        master, fg_color="transparent", **kwargs
    )  # 透明背景呈现 #EDF5FC
    self.current_dialog = None

  def render_category(self, cat_id):
    # 清空现有子控件
    for widget in self.winfo_children():
      widget.destroy()

    # 个人中心单独展示
    if cat_id == "user_center":
      lbl = ctk.CTkLabel(
          self,
          text="👤 个人中心页面",
          font=ctk.CTkFont(size=20, weight="bold"),
      )
      lbl.pack(pady=50)
      return

    # 查找对应分类
    target_cat = next((c for c in config.NAV_MENU if c["id"] == cat_id), None)
    if not target_cat or not target_cat["tools"]:
      empty_lbl = ctk.CTkLabel(
          self,
          text="📁 该分类下暂无工具",
          font=ctk.CTkFont(size=16),
          text_color="gray",
      )
      empty_lbl.pack(pady=100)
      return

    # 渲染该分类下的工具卡片网格
    for tool in target_cat["tools"]:
      self._create_tool_card(tool)

  def _create_tool_card(self, tool_info):
    """创建漂亮的白色独立工具卡片"""
    card = ctk.CTkFrame(
        self,
        fg_color="#FFFFFF",
        corner_radius=12,
        width=300,
        height=160,
    )
    card.pack(side="left", padx=15, pady=15)
    card.pack_propagate(False)

    # 顶部图标与名称
    top_frame = ctk.CTkFrame(card, fg_color="transparent")
    top_frame.pack(fill="x", padx=15, pady=(15, 5))

    icon_lbl = ctk.CTkLabel(
        top_frame, text=tool_info["icon"], font=config.get_font(22)
      )
    icon_lbl.pack(side="left", padx=(0, 8))

      # 💡 标题：添加 anchor="w" 和 expand=True，防止文字重影
    title_lbl = ctk.CTkLabel(
          top_frame,
          text=tool_info["name"],
          font=config.get_font(14, "bold"),
          text_color="#1F2937",
          anchor="w",
      )
    title_lbl.pack(side="left", fill="x", expand=True)

      # 描述文本
    desc_lbl = ctk.CTkLabel(
      card,
      text=tool_info["desc"],
      font=config.get_font(12),
      text_color="#6B7280",
      wraplength=260,
      justify="left",
    )
    desc_lbl.pack(anchor="w", padx=15, pady=5)

    # 底部打开按钮
    btn_open = ctk.CTkButton(
        card,
        text="打开工具",
        height=32,
        corner_radius=6,
        fg_color="#1677FF",
        hover_color="#0958D9",
        font=config.get_font(13, "bold"),
        command=lambda t=tool_info: self._launch_tool_dialog(t),
    )
    btn_open.pack(anchor="e", padx=15, pady=(5, 10))

  def _launch_tool_dialog(self, tool_info):
    """动态加载并弹出三级窗口 (按需引入)"""
    try:
      # 动态导入模块与类 (类似 Vue 动态路由)
      module = importlib.import_module(tool_info["dialog_module"])
      dialog_cls = getattr(module, tool_info["dialog_class"])

      # 实例化并打开弹窗
      if (
          self.current_dialog is None
          or not self.current_dialog.winfo_exists()
      ):
        self.current_dialog = dialog_cls(self)
      else:
        self.current_dialog.focus()  # 若已打开则置顶
    except Exception as e:
      print(f"❌ 启动工具弹窗失败: {e}")