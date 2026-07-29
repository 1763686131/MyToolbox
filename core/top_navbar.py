import config
import customtkinter as ctk


class TopNavbar(ctk.CTkFrame):

    """一级：顶部导航栏组件 (已支持 appdata.json 动态渲染与热刷新)"""

    def __init__(self, master, on_category_change, **kwargs):
        super().__init__(
            master, fg_color="#FFFFFF", corner_radius=10, height=55, **kwargs
        )
        self.on_category_change = on_category_change
        self.buttons = {}
        self.active_id = None
        self.pack_propagate(False)

        self._build_buttons()

    def _build_buttons(self):
        """渲染顶部所有分类按钮"""
        # 重新生成前清空已有按钮（防止热刷新时按钮重复叠加）
        for btn in self.buttons.values():
            btn.destroy()
        self.buttons.clear()

        # 1. 渲染 appdata.json 读取出来的动态分类
        for cat in config.NAV_MENU:
            cat_id = cat["id"]
            btn = ctk.CTkButton(
                self,
                text=cat["name"],
                width=90,
                height=36,
                corner_radius=6,
                font=config.get_font(size=14, weight="bold"),
                command=lambda cid=cat_id: self.select_tab(cid),
            )
            btn.pack(side="left", padx=(10, 5), pady=10)
            self.buttons[cat_id] = btn

        # 2. 右侧固定挂载“个人中心”按钮（安全容错处理）
        user_center_info = getattr(
            config,
            "USER_CENTER_ITEM",
            {"id": "user_center", "name": "👤 个人中心"},
        )

        user_btn = ctk.CTkButton(
            self,
            text=user_center_info["name"],
            width=90,
            height=36,
            fg_color="transparent",
            text_color="black",
            hover_color="#F0F0F0",
            font=config.get_font(size=14, weight="bold"),
            command=lambda: self.select_tab(user_center_info["id"]),
        )
        user_btn.pack(side="right", padx=15, pady=10)
        self.buttons[user_center_info["id"]] = user_btn

    def select_tab(self, cat_id):
        """高亮选中的选项卡，并触发回调"""
        self.active_id = cat_id
        user_center_id = getattr(
            config, "USER_CENTER_ITEM", {"id": "user_center"}
        )["id"]

        for cid, btn in self.buttons.items():
            if cid == cat_id:
                btn.configure(fg_color="#1677FF", text_color="#FFFFFF")
            else:
                if cid == user_center_id:
                    btn.configure(fg_color="transparent", text_color="black")
                else:
                    btn.configure(fg_color="transparent", text_color="#1F2937")

        if self.on_category_change:
            self.on_category_change(cat_id)

    def reload_navbar(self):
        """热刷新函数：当从 NAS 同步覆盖了 appdata.json 后调用，更新顶部按钮列表"""
        self._build_buttons()
        if self.active_id and self.active_id in self.buttons:
            self.select_tab(self.active_id)
        elif config.NAV_MENU:
            self.select_tab(config.NAV_MENU[0]["id"])