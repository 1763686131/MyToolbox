import config
import customtkinter as ctk


class TopNavbar(ctk.CTkFrame):

  """一级：顶部导航栏组件 (还原图片样式)"""

  def __init__(self, master, on_category_change, **kwargs):
    super().__init__(
        master, fg_color="#FFFFFF", corner_radius=10, height=55, **kwargs
    )
    self.on_category_change = on_category_change
    self.buttons = {}
    self.active_id = None
    self.pack_propagate(False)

    for cat in config.NAV_MENU:
      cat_id = cat["id"]
      btn = ctk.CTkButton(
          self,
          text=cat["name"],
          width=90,
          height=36,
          corner_radius=6,
          # ✍️ 使用全局圆润字体
          font=config.get_font(size=14, weight="bold"),
          command=lambda cid=cat_id: self.select_tab(cid),
      )
      btn.pack(side="left", padx=(10, 5), pady=10)
      self.buttons[cat_id] = btn

    user_btn = ctk.CTkButton(
        self,
        text=config.USER_CENTER_ITEM["name"],
        width=90,
        height=36,
        fg_color="transparent",
        text_color="black",
        hover_color="#F0F0F0",
        # ✍️ 使用全局圆润字体
        font=config.get_font(size=14, weight="bold"),
        command=lambda: self.select_tab(config.USER_CENTER_ITEM["id"]),
    )
    user_btn.pack(side="right", padx=15, pady=10)
    self.buttons[config.USER_CENTER_ITEM["id"]] = user_btn
    
  def select_tab(self, cat_id):
    self.active_id = cat_id

    # 刷新样式：高亮项为浅蓝色底+深蓝字，非高亮项为无底色+黑字
    for cid, btn in self.buttons.items():
      if cid == cat_id:
        btn.configure(
            fg_color="#E6F4FF",  # 激活状态的浅蓝色
            text_color="#1677FF",  # 激活状态的蓝色字体
            hover_color="#BAE0FF",
        )
      else:
        btn.configure(
            fg_color="transparent",
            text_color="#000000",
            hover_color="#F5F5F5",
        )

    # 触发页面切换通知
    self.on_category_change(cat_id)