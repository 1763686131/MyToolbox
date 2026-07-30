import importlib
import os
import time
import json
import requests
import urllib.parse
import webbrowser
import config
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image  # 确保你本地已经 pip install Pillow

class ToolGridView(ctk.CTkScrollableFrame):
    """二级：工具网格容器 (展示工具卡片)"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.dialogs = {}

    def _is_admin(self) -> bool:
        """判断当前登录的用户是否为管理员"""
        user_info = getattr(config, "CURRENT_USER", None) or getattr(config, "USER_INFO", None)
        if not user_info or not isinstance(user_info, dict):
            return False
        role = str(user_info.get("role", "")).lower()
        is_admin_flag = user_info.get("is_admin", False)
        username = str(user_info.get("username", "")).lower()
        return role == "admin" or is_admin_flag is True or username == "admin"

    def render_category(self, cat_id):
        # 清空现有子控件
        for widget in self.winfo_children():
            widget.destroy()

        # 🔥 个人中心单独展示
        if cat_id == "user_center":
            try:
                from views.profile.profile_view import ProfileView
                profile_page = ProfileView(self)
                profile_page.pack(fill="both", expand=True)
            except Exception as e:
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
        if not target_cat or not target_cat.get("tools"):
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
            # 💡 核心：软删除拦截，状态为 0 的直接隐身
            if tool.get("status", 1) == 0:
                continue
            self._create_tool_card(tool, cat_id)

    def _create_tool_card(self, tool_info, category_id=None):
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

        # 💡 管理员专属：右上角删除按钮
        if self._is_admin():
            btn_delete = ctk.CTkButton(
                card,
                text="×",
                width=22,
                height=22,
                corner_radius=11,
                fg_color="transparent",
                hover_color="#FF4D4F",  # 鼠标悬停变红
                text_color="#888888",
                font=config.get_font(14, "bold"),
                command=lambda t=tool_info, c=category_id: self._on_delete_tool_click(t, c)
            )
            btn_delete.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))

        # ----------------------------------------------------
        # 🎯 图标加载逻辑
        # ----------------------------------------------------
        raw_icon = tool_info.get("icon", "")
        clean_icon = raw_icon.replace("\\", "/").strip("/")
        icon_path = os.path.join(config.BASE_DIR, clean_icon)

        if os.path.exists(icon_path):
            try:
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
            icon_lbl = ctk.CTkLabel(top_frame, text="📄", font=config.get_font(22))

        icon_lbl.pack(side="left", padx=(0, 8))

        # ----------------------------------------------------
        # 标题、描述、按钮逻辑
        # ----------------------------------------------------
        title_lbl = ctk.CTkLabel(
            top_frame,
            text=tool_info.get("name", "未知应用"),
            font=config.get_font(14, "bold"),
            text_color="#1F2937",
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

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

    def _launch_tool_dialog(self, tool_info):
        """处理点击打开工具的逻辑"""
        # 防抖锁
        if getattr(self, "_is_opening_lock", False):
            return
        self._is_opening_lock = True
        self.after(400, lambda: setattr(self, "_is_opening_lock", False))

        tool_type = str(tool_info.get("type", "")) + str(tool_info.get("tool_type", ""))
        
        # 网页判断
        if "网页" in tool_type or "html" in tool_type.lower() or "url" in tool_info:
            target_url = tool_info.get("url") or tool_info.get("path") or tool_info.get("exe_name")
            if target_url and target_url.startswith("http"):
                webbrowser.open(target_url)
            else:
                messagebox.showerror("打开失败", "该工具被标记为网页链接，但在数据库中未找到有效的 http 网址！\\n请检查服务端数据。")
            return

        # 本地工具弹窗流程
        tool_id = str(tool_info.get("id") or tool_info.get("tool_id") or tool_info.get("name"))
        
        # 防止重复弹窗
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

    # ==========================================
    # 🚀 删除操作（下架 / 彻底删除）底层逻辑
    # ==========================================
    def _on_delete_tool_click(self, tool_info, category_id):
        """点击删除按钮，弹出二次确认窗"""
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
        """执行具体的删除逻辑（网络优先，绝不报 404）"""
        dialog.destroy()  

        # 1. 动态获取 API 根地址
        api_base = getattr(config, "SERVER_URL", None) or getattr(config, "API_URL", None) or getattr(config, "HOST", "http://127.0.0.1:4566")
        api_base = str(api_base).rstrip("/")
        
        # 2. 安全的 URL 编码，防止空格和斜杠把路由搞崩
        safe_tool_id = urllib.parse.quote(str(tool_id), safe="")
        safe_cat_id = urllib.parse.quote(str(category_id), safe="")

        api_url = ""
        try:
            # 3. 先向服务端发起删除请求！
            if delete_mode == "soft":
                api_url = f"{api_base}/api/tools/{safe_cat_id}/{safe_tool_id}/delete"
            else:
                api_url = f"{api_base}/api/tools/{safe_cat_id}/{safe_tool_id}/hard_delete"
                
            resp = requests.post(api_url, timeout=8)
            
            # 如果不是 200，说明服务端出了问题，绝对不能继续！
            if resp.status_code != 200:
                messagebox.showerror("服务器拒绝", f"服务端未能处理该请求，本地取消删除！\n\n状态码: {resp.status_code}\n报错信息: {resp.text}")
                return

            # 4. 服务端删成功了，现在修改客户端本地数据库
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

            # 5. 弹窗提示并刷新界面
            action_name = "软删除下架" if delete_mode == "soft" else "强制彻底删除"
            messagebox.showinfo("操作成功", f"工具【{tool_name}】已成功{action_name}！")
            
            # 刷新网格，卡片会立刻消失
            self.render_category(category_id)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("网络连接失败", f"无法连通服务器，请检查服务端是否运行！\n\n请求的地址: {api_url}\n错误: {e}")
        except Exception as e:
            messagebox.showerror("本地异常", f"执行过程发生错误: {str(e)}")