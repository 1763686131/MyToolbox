import importlib
import os
import sys
import json
import requests
import urllib.parse
import webbrowser
import config
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

class ToolGridView(ctk.CTkScrollableFrame):
    """二级：工具网格容器 (展示工具卡片 - 响应式 + 防遮挡完美版)"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.dialogs = {}
        
        # 隐藏自带的物理滚动条
        if getattr(config, "HIDE_GLOBAL_SCROLLBARS", False):
            self._scrollbar.grid_forget()
            
        # 响应式布局：保存当前卡片对象，监听窗口尺寸变化
        self.current_cards = []
        self.current_max_cols = 0
        self._resize_after_id = None
        
        self.bind("<Configure>", self._on_resize)

    # ==========================================
    # 🌟 滚轮事件强穿透引擎
    # ==========================================
    def _force_scroll_binding(self, widget):
        """递归遍历所有子控件，强制绑定鼠标滚轮事件到主 Canvas，并自动刷新画布大小"""
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")  
        widget.bind("<Button-5>", self._on_mousewheel, add="+")  

        # 💡 核心修复 2：监听任何内部组件的大小变化，一旦变大立刻更新滚动范围！
        # 这样登录后底下显示的新内容，瞬间就能被滚动条感知到！
        widget.bind("<Configure>", lambda e: self._update_scroll_region(), add="+")
        
        for child in widget.winfo_children():
            self._force_scroll_binding(child)


    def _update_scroll_region(self):
        """强制更新底层 Canvas 的滚动边界，防止出现滑不动的情况"""
        if getattr(self, "_parent_canvas", None) and self._parent_canvas.winfo_exists():
            # 获取内部包裹的 Frame 的实际大小
            bbox = self._parent_canvas.bbox("all")
            if bbox:
                # 强制重新设置画布的滚动范围
                self._parent_canvas.configure(scrollregion=bbox)

    def _on_mousewheel(self, event):
        """跨平台鼠标滚轮处理器，增加滑动速度"""
        if getattr(self, "_parent_canvas", None) is None or not self._parent_canvas.winfo_exists():
            return

        # 💡 核心修复 1：滚动加速器 (修改倍率，让滑动更顺畅)
        scroll_speed = 3  # 你可以修改这个数字，数字越大滑动越快

        if sys.platform.startswith("win"):
            # Windows: event.delta 通常是 120 或 -120
            direction = int(-1 * (event.delta / 120))
            self._parent_canvas.yview_scroll(direction * scroll_speed, "units")
        elif sys.platform == "darwin":
            # macOS: event.delta 就是滑动的像素
            self._parent_canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            # Linux X11
            if event.num == 4:
                self._parent_canvas.yview_scroll(-1 * scroll_speed, "units")
            elif event.num == 5:
                self._parent_canvas.yview_scroll(1 * scroll_speed, "units")

                
    def _is_admin(self) -> bool:
        user_info = getattr(config, "CURRENT_USER", None) or getattr(config, "USER_INFO", None)
        if not user_info or not isinstance(user_info, dict):
            return False
        role = str(user_info.get("role", "")).lower()
        is_admin_flag = user_info.get("is_admin", False)
        username = str(user_info.get("username", "")).lower()
        return role == "admin" or is_admin_flag is True or username == "admin"

    def _on_resize(self, event):
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(100, self._layout_cards)

    def _layout_cards(self):
        if not self.current_cards:
            return

        available_width = self.winfo_width()
        if available_width < 100:
            available_width = 1000

        max_cols = max(1, (available_width - 20) // 330)

        if getattr(self, "current_max_cols", 0) == max_cols:
            return
        
        self.current_max_cols = max_cols

        for index, card in enumerate(self.current_cards):
            row = index // max_cols
            col = index % max_cols
            card.grid(row=row, column=col, padx=15, pady=15)

    def render_category(self, cat_id):
        for widget in self.winfo_children():
            widget.destroy()

        self.current_cards = []
        self.current_max_cols = 0 

        # 🔥 个人中心单独展示
        if cat_id == "user_center":
            try:
                from views.profile.profile_view import ProfileView
                profile_page = ProfileView(self)
                # 🚀 修复点 1：去掉 expand=True，允许个人中心根据实际内容撑开高度！
                profile_page.pack(fill="x", padx=10, pady=10)
                
                # 为个人中心注入滚轮穿透事件
                self._force_scroll_binding(profile_page)
            except Exception as e:
                error_lbl = ctk.CTkLabel(
                    self, text=f"❌ 加载个人中心失败:\n{e}", text_color="red", font=config.get_font(size=14)
                )
                error_lbl.pack(pady=50)
            return

        target_cat = next((c for c in config.NAV_MENU if c["id"] == cat_id), None)
        if not target_cat or not target_cat.get("tools"):
            empty_lbl = ctk.CTkLabel(
                self, text="📁该分类下暂无工具", font=config.get_font(size=16), text_color="gray"
            )
            empty_lbl.pack(pady=100)
            return

        self.grid_container = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, padx=10, pady=10)

        visible_tools = [t for t in target_cat["tools"] if t.get("status", 1) != 0]
        
        for tool in visible_tools:
            card = self._create_tool_card(self.grid_container, tool, cat_id)
            self.current_cards.append(card)

        self._layout_cards()
        self._force_scroll_binding(self.grid_container)

    def _create_tool_card(self, parent_container, tool_info, category_id=None):
        card = ctk.CTkFrame(
            parent_container,
            fg_color="#FFFFFF",
            corner_radius=12,
            width=300,
            height=160,
        )
        card.grid_propagate(False)
        card.pack_propagate(False)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))

        # 🎯 图标加载 (靠左)
        raw_icon = tool_info.get("icon", "")
        clean_icon = raw_icon.replace("\\", "/").strip("/")
        icon_path = os.path.join(config.BASE_DIR, clean_icon)

        if os.path.exists(icon_path):
            try:
                pil_image = Image.open(icon_path)
                ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(28, 28))
                icon_lbl = ctk.CTkLabel(top_frame, image=ctk_img, text="")
            except Exception as e:
                icon_lbl = ctk.CTkLabel(top_frame, text="📄", font=config.get_font(22))
        else:
            icon_lbl = ctk.CTkLabel(top_frame, text="📄", font=config.get_font(22))
            
        icon_lbl.pack(side="left", padx=(0, 8))

        # 🎯 标题加载 (居中偏左)
        title_lbl = ctk.CTkLabel(
            top_frame,
            text=tool_info.get("name", "未知应用"),
            font=config.get_font(14, "bold"),
            text_color="#1F2937",
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # 🚀 修复点 2：将删除按钮直接加入布局队列，强制靠右，绝不重叠！
        if self._is_admin():
            btn_delete = ctk.CTkButton(
                top_frame,
                text="×",
                width=24,
                height=24,
                corner_radius=12,
                fg_color="#FFEEEE",    
                hover_color="#FF4D4F", 
                text_color="#FF4D4F",  
                font=config.get_font(16, "bold"),
                command=lambda t=tool_info, c=category_id: self._on_delete_tool_click(t, c)
            )
            # pack(side="right") 会让它安全地躲在标题栏的最右侧
            btn_delete.pack(side="right", padx=(5, 0))

        # 描述与打开按钮
        desc_lbl = ctk.CTkLabel(
            card,
            text=tool_info.get("desc", ""),
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

        return card

    # ==========================================
    # 行为交互逻辑 (打开与删除)
    # ==========================================
    def _launch_tool_dialog(self, tool_info):
        if getattr(self, "_is_opening_lock", False):
            return
        self._is_opening_lock = True
        self.after(400, lambda: setattr(self, "_is_opening_lock", False))

        tool_type = str(tool_info.get("type", "")) + str(tool_info.get("tool_type", ""))
        
        if "网页" in tool_type or "html" in tool_type.lower() or "url" in tool_info:
            target_url = tool_info.get("url") or tool_info.get("path") or tool_info.get("exe_name")
            if target_url and target_url.startswith("http"):
                webbrowser.open(target_url)
            else:
                messagebox.showerror("打开失败", "该工具被标记为网页链接，但在数据库中未找到有效的 http 网址！")
            return

        tool_id = str(tool_info.get("id") or tool_info.get("tool_id") or tool_info.get("name"))
        
        if tool_id in self.dialogs and self.dialogs[tool_id].winfo_exists():
            self.dialogs[tool_id].lift()
            self.dialogs[tool_id].focus_force()
            return

        try:
            module_name = tool_info.get("dialog_module", "views.system.cloud_tool_dialog")
            class_name = tool_info.get("dialog_class", "CloudToolDialog")
            
            module = importlib.import_module(module_name)
            dialog_cls = getattr(module, class_name)
            
            if "exe_name" in tool_info and tool_info["exe_name"]:
                dialog = dialog_cls(
                    self.winfo_toplevel(), 
                    display_name=tool_info.get("name", ""), 
                    exe_name=tool_info.get("exe_name", ""),
                    sub_dir=tool_info.get("sub_dir", "others")
                )
            else:
                dialog = dialog_cls(self.winfo_toplevel())
                
            self.dialogs[tool_id] = dialog
        except Exception as e:
            print(f"❌ 启动工具弹窗失败: {e}")

    def _on_delete_tool_click(self, tool_info, category_id):
        tool_name = tool_info.get("name", "未命名软件")
        tool_id = tool_info.get("tool_id") or tool_info.get("id")

        dialog = ctk.CTkToplevel(self)
        dialog.title("确认删除操作")
        dialog.geometry("460x240")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.update_idletasks()
        if self.winfo_toplevel():
            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - 460) // 2
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - 240) // 2
            dialog.geometry(f"+{x}+{y}")

        lbl = ctk.CTkLabel(
            dialog, 
            text=f"请选择对【{tool_name}】的删除方式：\n\n🟡 【软删除/下架】：仅隐藏，服务器仍保留数据。\n🔴 【强制彻底删除】：抹除数据库记录，并销毁物理文件！", 
            font=config.get_font(14),
            justify="left"
        )
        lbl.pack(pady=(25, 20), padx=20)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        btn_soft = ctk.CTkButton(
            btn_frame, text="软删除 (下架)", 
            fg_color="#F39C12", hover_color="#D68910", font=config.get_font(14, "bold"),
            command=lambda: self._execute_delete_action(dialog, tool_id, category_id, tool_name, "soft")
        )
        btn_soft.pack(side="left", padx=10, expand=True)

        btn_hard = ctk.CTkButton(
            btn_frame, text="强制彻底删除", 
            fg_color="#E74C3C", hover_color="#C0392B", font=config.get_font(14, "bold"),
            command=lambda: self._execute_delete_action(dialog, tool_id, category_id, tool_name, "hard")
        )
        btn_hard.pack(side="right", padx=10, expand=True)

    def _execute_delete_action(self, dialog, tool_id, category_id, tool_name, delete_mode):
        dialog.destroy()  

        api_base = getattr(config, "SERVER_URL", None) or getattr(config, "API_URL", None) or getattr(config, "HOST", "http://127.0.0.1:4566")
        api_base = str(api_base).rstrip("/")
        
        safe_tool_id = urllib.parse.quote(str(tool_id), safe="")
        safe_cat_id = urllib.parse.quote(str(category_id), safe="")

        api_url = ""
        try:
            if delete_mode == "soft":
                api_url = f"{api_base}/api/tools/{safe_cat_id}/{safe_tool_id}/delete"
            else:
                api_url = f"{api_base}/api/tools/{safe_cat_id}/{safe_tool_id}/hard_delete"
                
            resp = requests.post(api_url, timeout=8)
            
            if resp.status_code != 200:
                messagebox.showerror("服务器拒绝", f"服务端未能处理该请求，本地取消删除！\n\n状态码: {resp.status_code}\n报错信息: {resp.text}")
                return

            local_db_path = os.path.join(config.BASE_DIR, "data", "appdata.json")
            if os.path.exists(local_db_path):
                with open(local_db_path, "r", encoding="utf-8") as f:
                    db_data = json.load(f)

                for cat in db_data.get("categories", []):
                    if cat.get("category_id") == category_id or cat.get("id") == category_id:
                        if delete_mode == "soft":
                            for t in cat.get("tools", []):
                                if t.get("tool_id") == tool_id or t.get("id") == tool_id:
                                    t["status"] = 0
                                    break
                        elif delete_mode == "hard":
                            cat["tools"] = [
                                t for t in cat.get("tools", []) 
                                if t.get("tool_id") != tool_id and t.get("id") != tool_id
                            ]
                        break

                with open(local_db_path, "w", encoding="utf-8") as f:
                    json.dump(db_data, f, ensure_ascii=False, indent=2)

            action_name = "软删除下架" if delete_mode == "soft" else "强制彻底删除"
            messagebox.showinfo("操作成功", f"工具【{tool_name}】已成功{action_name}！")
            
            self.render_category(category_id)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("网络连接失败", f"无法连通服务器，请检查服务端是否运行！\n\n错误: {e}")
        except Exception as e:
            messagebox.showerror("本地异常", f"执行过程发生错误: {str(e)}")