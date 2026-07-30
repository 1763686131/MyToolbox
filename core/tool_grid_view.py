import importlib
import os
import webbrowser
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

        # 🔥 个人中心单独展示（核心修改区）
        if cat_id == "user_center":
            try:
                # 动态引入我们写好的高级个人中心组件
                from views.profile.profile_view import ProfileView
                
                # 实例化并让它铺满整个网格区域
                profile_page = ProfileView(self)
                profile_page.pack(fill="both", expand=True)
            except Exception as e:
                # 如果找不到文件或代码有错，给个友好的报错提示
                error_lbl = ctk.CTkLabel(
                    self,
                    text=f"❌ 加载个人中心失败:\n{e}",
                    text_color="red",
                    font=config.get_font(size=14)
                )
                error_lbl.pack(pady=50)
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
        # 🚀 核心修复：防抖锁（加入 getattr 完美容错，没上户口也不会报错了！）
        if getattr(self, "_is_opening_lock", False):
            return
        self._is_opening_lock = True
        self.after(400, lambda: setattr(self, "_is_opening_lock", False))

        # ==========================================
        # 🌟 创新点：前端通过 Type 精准拦截分类
        # ==========================================
        # 兼容读取后端传过来的 type 或 tool_type 字段
        tool_type = str(tool_info.get("type", "")) + str(tool_info.get("tool_type", ""))
        
        # 1. 只要类型里包含“网页”或“html”，或者存在“url”字段，绝对判定为网页工具！
        if "网页" in tool_type or "html" in tool_type.lower() or "url" in tool_info:
            # 智能提取网址 (兼容后端可能存错字段的情况)
            target_url = tool_info.get("url") or tool_info.get("path") or tool_info.get("exe_name")
            
            if target_url and target_url.startswith("http"):
                webbrowser.open(target_url)  # 👉 直接跳转浏览器
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("打开失败", "该工具被标记为网页链接，但在数据库中未找到有效的 http 网址！\n请检查服务端数据。")
            return

        # ==========================================
        # 2. 如果不是网页，走常规的 EXE/PY 本地弹窗流程
        # ==========================================
        tool_id = tool_info.get("id") or tool_info.get("tool_id") or tool_info.get("name")
        
        # 已存在窗口判断
        if tool_id in self.dialogs and self.dialogs[tool_id].winfo_exists():
            self.dialogs[tool_id].lift()
            self.dialogs[tool_id].focus_force()
            return

        try:
            # 兼容新老数据的万能兜底
            module_name = tool_info.get("dialog_module", "views.system.cloud_tool_dialog")
            class_name = tool_info.get("dialog_class", "CloudToolDialog")
            
            module = importlib.import_module(module_name)
            dialog_cls = getattr(module, class_name)
            
            # 安全判断，确保有 exe_name 才传参数
            if "exe_name" in tool_info and tool_info["exe_name"]:
                dialog = dialog_cls(
                    self.winfo_toplevel(), 
                    display_name=tool_info["name"], 
                    exe_name=tool_info["exe_name"],
                    sub_dir=tool_info.get("sub_dir", "others")
                )
            else:
                dialog = dialog_cls(self.winfo_toplevel())
                
            self.dialogs[tool_id] = dialog
        except Exception as e:
            print(f"❌ 启动工具弹窗失败: {e}")
        if "url" in tool_info:
            webbrowser.open(tool_info["url"])
            return
            
        tool_id = tool_info.get("id") or tool_info.get("tool_id")
        
        # 🌟 修复 4：防止双击或多次点击导致弹出多个窗口
        if tool_id in self.dialogs and self.dialogs[tool_id].winfo_exists():
            self.dialogs[tool_id].lift()
            self.dialogs[tool_id].focus_force()
            return

        try:
            # 🌟 修复 4：新上传的工具如果没有配置弹窗模块，自动给它分配万能云端弹窗，防止崩溃！
            module_name = tool_info.get("dialog_module", "views.system.cloud_tool_dialog")
            class_name = tool_info.get("dialog_class", "CloudToolDialog")
            
            module = importlib.import_module(module_name)
            dialog_cls = getattr(module, class_name)
            
            # 🌟 修复 3：将 self 换成 self.winfo_toplevel()，传主窗口对象给弹窗以便它居中计算
            if "exe_name" in tool_info:
                dialog = dialog_cls(
                    self.winfo_toplevel(), 
                    display_name=tool_info["name"], 
                    exe_name=tool_info["exe_name"],
                    sub_dir=tool_info.get("sub_dir", "others")
                )
            else:
                dialog = dialog_cls(self.winfo_toplevel())
                
            self.dialogs[tool_id] = dialog
        except Exception as e:
            print(f"❌ 启动工具弹窗失败: {e}")
        if "url" in tool_info:
            webbrowser.open(tool_info["url"])    #如果是链接，直接调动浏览器
            return
            
        tool_id = tool_info["id"]
        try:
            module = importlib.import_module(tool_info["dialog_module"])
            dialog_cls = getattr(module, tool_info["dialog_class"])
            
            # 🔥 如果它在 config 里配置了 exe_name，我们就把参数传进去！
            if "exe_name" in tool_info:
                dialog = dialog_cls(
                    self, 
                    display_name=tool_info["name"], 
                    exe_name=tool_info["exe_name"],
                    sub_dir=tool_info.get("sub_dir", "others")  # 👉 核心修复：精准传递文件夹分类名！
                )
            else:
                dialog = dialog_cls(self)
                
            self.dialogs[tool_id] = dialog
        except Exception as e:
            print(f"❌ 启动工具弹窗失败: {e}")