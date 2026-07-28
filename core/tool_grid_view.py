import importlib
import os
import config
import customtkinter as ctk
from PIL import Image  # 确保你本地已经 pip install Pillow


class ToolGridView(ctk.CTkScrollableFrame):

    """二级：工具网格容器 (展示工具卡片)"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.dialogs = {}
        
    def render_category(self, cat_id):
        # 清空现有子控件
        for widget in self.winfo_children():
            widget.destroy()

        # 个人中心单独展示
        if cat_id == "user_center":
            lbl = ctk.CTkLabel(
                self,
                text="👤 个人中心页面",
                font=config.get_font(size=20, weight="bold"),
            )
            lbl.pack(pady=50)
            return

        # 查找对应分类
        target_cat = next((c for c in config.NAV_MENU if c["id"] == cat_id), None)
        if not target_cat or not target_cat["tools"]:
            empty_lbl = ctk.CTkLabel(
                self,
                text="📁该分类下暂无工具",
                font=config.get_font(size=16),
                text_color="gray",
            )
            empty_lbl.pack(pady=100)
            return

        # 渲染该分类下的工具卡片网格
        for tool in target_cat["tools"]:
            self._create_tool_card(tool)

    def _create_tool_card(self, tool_info):
        """创建漂亮的独立工具卡片"""
        card = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=12,
            width=300,
            height=160,
        )
        card.pack(side="left", padx=15, pady=15)
        card.pack_propagate(False)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))

        # ----------------------------------------------------
        # 🎯 图标加载逻辑
        # ----------------------------------------------------
        raw_icon = tool_info.get("icon", "")
        # 修正路径：替换掉错误的斜杠
        clean_icon = raw_icon.replace("\\", "/").strip("/")
        # 拼接绝对路径
        icon_path = os.path.join(config.BASE_DIR, clean_icon)

        # 检查文件是否存在
        if os.path.exists(icon_path):
            try:
                # 使用 PIL 打开图片，并传入 CTkImage
                pil_image = Image.open(icon_path)
                ctk_img = ctk.CTkImage(
                    light_image=pil_image, 
                    dark_image=pil_image, 
                    size=(28, 28)
                )
                icon_lbl = ctk.CTkLabel(top_frame, image=ctk_img, text="")
            except Exception as e:
                print(f"⚠️ 图片加载异常: {e}")
                icon_lbl = ctk.CTkLabel(top_frame, text="📄", font=config.get_font(22))
        else:
            print(f"⚠️ 找不到图片: {icon_path}")
            icon_lbl = ctk.CTkLabel(top_frame, text="📄", font=config.get_font(22))

        icon_lbl.pack(side="left", padx=(0, 8))

        # ----------------------------------------------------
        # 标题、描述、按钮逻辑
        # ----------------------------------------------------
        title_lbl = ctk.CTkLabel(
            top_frame,
            text=tool_info["name"],
            font=config.get_font(14, "bold"),
            text_color="#1F2937",
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        desc_lbl = ctk.CTkLabel(
            card,
            text=tool_info["desc"],
            font=config.get_font(12),
            text_color="#6B7280",
            wraplength=260,
            justify="left",
        )
        desc_lbl.pack(anchor="w", padx=15, pady=5)

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
        tool_id = tool_info["id"]
        try:
            module = importlib.import_module(tool_info["dialog_module"])
            dialog_cls = getattr(module, tool_info["dialog_class"])
            
            # 🔥 如果它在 config 里配置了 exe_name，我们就把参数传进去！
            if "exe_name" in tool_info:
                dialog = dialog_cls(self, display_name=tool_info["name"], exe_name=tool_info["exe_name"])
            else:
                dialog = dialog_cls(self)
                
            self.dialogs[tool_id] = dialog
        except Exception as e:
            print(f"❌ 启动工具弹窗失败: {e}")