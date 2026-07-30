import os
import threading
import json
import requests
from tkinter import filedialog, messagebox
import customtkinter as ctk
import config


class ProfileView(ctk.CTkFrame):
    """个人中心与管理员后台视图（支持游客鉴权、全局状态锁定与图标静默同步）"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_user = None
        self.cloud_text = ""  
        self.cloud_data_dict = {} # 用于存放解析后的云端字典，方便提取图标路径
        
        self.upload_file_path = None
        self.upload_icon_path = None # 新增：存放准备上传的图标路径

        self._build_ui()

    def _build_ui(self):
        self.current_user = getattr(config, "CURRENT_USER", None)

        for widget in self.winfo_children():
            widget.destroy()
            
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(
            header_frame, text="👤 个人中心 & 管理后台",
            font=config.get_font(size=20, weight="bold"), text_color=("#1F2937", "#F3F4F6")
        ).pack(anchor="w")

        if self.current_user is None:
            self._build_guest_card()
        else:
            self._build_user_card()

        self._build_sync_card()

        if self.current_user and self.current_user.get("role") == "admin":
            self._build_admin_card()

    def _build_guest_card(self):
        card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        card.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(card, text="您当前是游客身份，部分高级功能已隐藏", font=config.get_font(size=14), text_color="gray").pack(pady=(25, 15))
        ctk.CTkButton(card, text="🔑 立即登录系统", font=config.get_font(size=14, weight="bold"), height=36, command=self._show_login_dialog).pack(pady=(0, 25))

    def _build_user_card(self):
        info_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        info_card.pack(fill="x", padx=20, pady=10)
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=15)
        
        avatar = self.current_user.get("profile", {}).get("avatar", "🧑‍💻")
        ctk.CTkLabel(info_inner, text=avatar, font=ctk.CTkFont(size=42)).pack(side="left", padx=(0, 15))

        user_text_box = ctk.CTkFrame(info_inner, fg_color="transparent")
        user_text_box.pack(side="left", fill="both", expand=True)

        user_name = self.current_user.get('name', '未知用户')
        user_id = self.current_user.get('id', '未知ID')
        ctk.CTkLabel(user_text_box, text=f"欢迎回来，{user_name} (ID: {user_id})", font=config.get_font(size=16, weight="bold")).pack(anchor="w")

        role_badge_text = "✨ 超级管理员账号" if self.current_user.get("role") == "admin" else "👤 普通用户账号"
        role_color = "#1677FF" if self.current_user.get("role") == "admin" else "gray"
        ctk.CTkLabel(user_text_box, text=role_badge_text, text_color=role_color, font=config.get_font(size=12)).pack(anchor="w", pady=(3, 0))
        
        ctk.CTkButton(info_inner, text="退出登录", width=70, fg_color="#F56C6C", hover_color="#E6A23C", font=config.get_font(size=12), command=self._logout).pack(side="right")

    def _build_sync_card(self):
        """云端数据同步模块（引入全局状态锁，防止来回切换重置）"""
        sync_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        sync_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(sync_card, text="☁️ 云端工具库目录同步", font=config.get_font(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        self.sync_status_frame = ctk.CTkFrame(sync_card, fg_color="transparent")
        self.sync_status_frame.pack(fill="x", padx=20, pady=(5, 15))

        # 读取全局变量，判断是否在当前运行周期内已经同步/检查过了
        is_latest = getattr(config, "SYNC_IS_LATEST", False)

        if is_latest:
            # 锁定状态：如果已经是最新的，直接展示绿色，不生成检测按钮
            self.sync_status_label = ctk.CTkLabel(self.sync_status_frame, text="✅ 数据已经是最新了", font=config.get_font(size=13), text_color="#10B981")
            self.sync_status_label.pack(side="left")
        else:
            # 初始状态：未检查
            self.sync_status_label = ctk.CTkLabel(self.sync_status_frame, text="尚未检测，请点击比对云端数据", font=config.get_font(size=13), text_color="gray")
            self.sync_status_label.pack(side="left")

            self.btn_check_sync = ctk.CTkButton(self.sync_status_frame, text="🔄 检测更新", font=config.get_font(size=13, weight="bold"), height=32, command=self._start_check_sync)
            self.btn_check_sync.pack(side="right", padx=10)

            self.btn_do_sync = ctk.CTkButton(self.sync_status_frame, text="⬇️ 立即同步", font=config.get_font(size=13, weight="bold"), height=32, fg_color="#1677FF", command=self._execute_sync)

    def _build_admin_card(self):
        """管理员上传面板（新增图标上传入口）"""
        admin_card = ctk.CTkFrame(self, fg_color=("#FFFBEB", "#26231C"), corner_radius=12, border_width=1, border_color=("#FDE68A", "#544319"))
        admin_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(admin_card, text="⚙️ 管理员控制台：发布/更新软件", text_color=("#D97706", "#F59E0B"), font=config.get_font(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        form_grid = ctk.CTkFrame(admin_card, fg_color="transparent")
        form_grid.pack(fill="x", padx=20, pady=(0, 15))
        form_grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_grid, text="软件名称:", font=config.get_font(size=12, weight="bold")).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_name = ctk.CTkEntry(form_grid, placeholder_text="例如：驱动大师", font=config.get_font(size=12))
        self.entry_name.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_grid, text="软件简介:", font=config.get_font(size=12, weight="bold")).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_desc = ctk.CTkEntry(form_grid, placeholder_text="一句话描述功能亮点", font=config.get_font(size=12))
        self.entry_desc.grid(row=1, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_grid, text="工具类型:", font=config.get_font(size=12, weight="bold")).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
        self.var_type = ctk.StringVar(value=".exe文件")
        ctk.CTkOptionMenu(form_grid, values=[".exe文件", "网页链接 HTML"], variable=self.var_type, font=config.get_font(size=12)).grid(row=2, column=1, sticky="w", pady=6)

        ctk.CTkLabel(form_grid, text="保存分类:", font=config.get_font(size=12, weight="bold")).grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
        self.category_map = {cat["name"]: cat["id"] for cat in getattr(config, "NAV_MENU", [])}
        cat_names_list = list(self.category_map.keys())
        self.var_category = ctk.StringVar(value=cat_names_list[0] if cat_names_list else "无分类")
        ctk.CTkOptionMenu(form_grid, values=cat_names_list, variable=self.var_category, font=config.get_font(size=12)).grid(row=3, column=1, sticky="w", pady=6)

        ctk.CTkLabel(form_grid, text="版本编号:", font=config.get_font(size=12, weight="bold")).grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_version = ctk.CTkEntry(form_grid, placeholder_text="例如：v1.0.0", font=config.get_font(size=12))
        self.entry_version.grid(row=4, column=1, sticky="ew", pady=6)

        # 💡 新增：图标选择区
        ctk.CTkLabel(form_grid, text="工具图标:", font=config.get_font(size=12, weight="bold")).grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)
        icon_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        icon_box.grid(row=5, column=1, sticky="ew", pady=6)
        self.lbl_icon_path = ctk.CTkLabel(icon_box, text="未选择(默认文本图标)", text_color="gray", font=config.get_font(size=12))
        self.lbl_icon_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(icon_box, text="🖼️ 浏览图标", width=90, font=config.get_font(size=12), command=self._select_icon_file).pack(side="right")

        ctk.CTkLabel(form_grid, text="工具文件:", font=config.get_font(size=12, weight="bold")).grid(row=6, column=0, sticky="e", padx=(0, 10), pady=6)
        file_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        file_box.grid(row=6, column=1, sticky="ew", pady=6)
        self.lbl_file_path = ctk.CTkLabel(file_box, text="未选择任何文件", text_color="gray", font=config.get_font(size=12))
        self.lbl_file_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(file_box, text="📁 浏览文件", width=90, font=config.get_font(size=12), command=self._select_upload_file).pack(side="right")

        self.btn_upload = ctk.CTkButton(admin_card, text="🚀 立即上传并发布到云端", fg_color="#67C23A", hover_color="#529B2E", font=config.get_font(size=14, weight="bold"), height=40, command=self._start_upload_thread)
        self.btn_upload.pack(fill="x", padx=20, pady=(5, 20))


    # ------------------ 同步比对核心业务逻辑 ------------------

    def _start_check_sync(self):
        self.sync_status_label.configure(text="正在与云端比对....", text_color=("#1F2937", "#F3F4F6"))
        self.btn_check_sync.pack_forget() 
        self.btn_do_sync.pack_forget()    
        threading.Thread(target=self._task_check_sync, daemon=True).start()

    def _task_check_sync(self):
        try:
            base_dir = getattr(config, "BASE_DIR", os.getcwd())
            local_path = os.path.join(base_dir, "data", "appdata.json")
            
            local_data = {}
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    try:
                        local_data = json.load(f)
                    except json.JSONDecodeError:
                        local_data = {} 

            resp = requests.get(f"{config.API_BASE_URL}/api/appdata", timeout=5)
            resp.raise_for_status()
            
            self.cloud_text = resp.text  
            try:
                self.cloud_data_dict = resp.json() 
            except ValueError:
                self.cloud_data_dict = {}

            if local_data != self.cloud_data_dict:
                self.after(0, self._show_sync_needed)
            else:
                self.after(0, self._show_synced)
                
        except Exception as e:
            self.after(0, lambda: self.sync_status_label.configure(text=f"❌ 无法连接云端: {e}", text_color="red"))
            self.after(0, lambda: self.btn_check_sync.pack(side="right", padx=10))

    def _show_sync_needed(self):
        self.sync_status_label.configure(text="⚠️ 云端数据有新内容", text_color="#D97706")
        self.btn_do_sync.pack(side="right", padx=10) 

    def _show_synced(self):
        """同步完毕后，打上全局标记，隐藏按钮"""
        config.SYNC_IS_LATEST = True  # 💡 标记全局状态
        self.sync_status_label.configure(text="✅ 数据已经是最新了", text_color="#10B981")
        if hasattr(self, 'btn_check_sync'): self.btn_check_sync.pack_forget()
        if hasattr(self, 'btn_do_sync'): self.btn_do_sync.pack_forget()

    def _execute_sync(self):
        self.btn_do_sync.configure(state="disabled", text="正在同步...")
        threading.Thread(target=self._task_execute_sync_and_icons, daemon=True).start()

    def _task_execute_sync_and_icons(self):
        """后台写入 JSON，并静默拉取所有缺失的图标"""
        try:
            base_dir = getattr(config, "BASE_DIR", os.getcwd())
            local_path = os.path.join(base_dir, "data", "appdata.json")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(self.cloud_text)
                
            # 💡 核心新增：遍历云端 JSON，静默比对并下载缺失图标
            for category in self.cloud_data_dict.get("categories", []):
                for tool in category.get("tools", []):
                    icon_path = tool.get("icon", "")
                    if icon_path and icon_path.endswith((".png", ".ico", ".jpg")):
                        local_icon_path = os.path.join(base_dir, icon_path)
                        # 如果本地没有这个图标，直接从服务端下载
                        if not os.path.exists(local_icon_path):
                            os.makedirs(os.path.dirname(local_icon_path), exist_ok=True)
                            try:
                                icon_resp = requests.get(f"{config.API_BASE_URL}/{icon_path}", timeout=10)
                                if icon_resp.status_code == 200:
                                    with open(local_icon_path, "wb") as f_icon:
                                        f_icon.write(icon_resp.content)
                            except Exception as icon_e:
                                print(f"拉取图标失败 {icon_path}: {icon_e}")
                
            # 同步完成后刷新前端状态
            self.after(0, self._show_synced)
            if hasattr(config, "reload_appdata"):
                self.after(0, config.reload_appdata)
            self.after(0, lambda: messagebox.showinfo("同步成功", "云端数据与图标已成功拉取覆盖！新工具已经就绪。"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("同步失败", f"发生错误: {e}"))
            self.after(0, lambda: self.btn_do_sync.configure(state="normal", text="⬇️ 立即同步"))

    # ------------------ 登录鉴权与上传逻辑 ------------------

    def _show_login_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("登录账户")
        win_w, win_h = 320, 300
        master = self.winfo_toplevel()
        master.update_idletasks() # 确保获取到最新的窗口尺寸
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (win_w // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (win_h // 2)
        dialog.geometry(f"{win_w}x{win_h}+{x}+{y}")
        
        dialog.resizable(False, False)
        dialog.transient(master)
        dialog.grab_set()

        # ... 这里保留你原本生成的账号密码输入框 UI 代码 ...
        ctk.CTkLabel(dialog, text="🔑 验证身份", font=config.get_font(size=20, weight="bold")).pack(pady=(20, 10))
        
        ctk.CTkLabel(dialog, text="账号 ID:", font=config.get_font(size=12)).pack(anchor="w", padx=40)
        entry_id = ctk.CTkEntry(dialog, placeholder_text="如: 1001", font=config.get_font(size=13))
        entry_id.pack(fill="x", padx=40, pady=(5, 10))

        ctk.CTkLabel(dialog, text="密码:", font=config.get_font(size=12)).pack(anchor="w", padx=40)
        entry_pwd = ctk.CTkEntry(dialog, placeholder_text="请输入密码", show="*", font=config.get_font(size=13))
        entry_pwd.pack(fill="x", padx=40, pady=(5, 20))

        def do_login():
            uid, pwd = entry_id.get().strip(), entry_pwd.get().strip()
            if not uid or not pwd:
                messagebox.showwarning("提示", "账号和密码不能为空！", parent=dialog)
                return
            
            try:
                resp = requests.post(f"{config.API_BASE_URL}/api/login", json={"user_id": uid, "password": pwd}, timeout=5)
                if resp.status_code == 200 and resp.json().get("status") == "success":
                    # 🌟 修复 1：将登录信息写入全局状态
                    config.CURRENT_USER = resp.json().get("data")
                    dialog.destroy()
                    self._build_ui()  
                else:
                    messagebox.showerror("错误", resp.json().get("detail", "登录失败"), parent=dialog)
            except Exception as e:
                messagebox.showerror("网络异常", f"无法连接到 NAS 服务端: {e}", parent=dialog)

        ctk.CTkButton(dialog, text="立 即 登 录", height=38, font=config.get_font(size=14, weight="bold"), command=do_login).pack(fill="x", padx=40)

    def _logout(self):
        # 🌟 修复 1：清理全局状态
        config.CURRENT_USER = None
        self._build_ui()

    def _select_icon_file(self):
        """选择图片图标"""
        file_path = filedialog.askopenfilename(title="选择工具图标", filetypes=[("图片文件", "*.png;*.jpg;*.ico")])
        if file_path:
            self.upload_icon_path = file_path
            self.lbl_icon_path.configure(text=os.path.basename(file_path), text_color=("#1F2937", "#F3F4F6"))

    def _select_upload_file(self):
        file_path = filedialog.askopenfilename(title="选择要发布的软件包或 HTML")
        if file_path:
            self.upload_file_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_file_path.configure(text=filename, text_color=("#1F2937", "#F3F4F6"))
            if not self.entry_name.get():
                self.entry_name.insert(0, os.path.splitext(filename)[0])

    def _start_upload_thread(self):
        if not self.upload_file_path:
            messagebox.showwarning("提示", "请先选择要上传的工具文件！")
            return
        if not self.entry_name.get() or not self.entry_desc.get():
            messagebox.showwarning("提示", "请填写完整的名称和简介！")
            return

        self.btn_upload.configure(state="disabled", text="正在推送到 NAS，请稍候...")
        threading.Thread(target=self._upload_task, daemon=True).start()

    def _upload_task(self):
        selected_chinese_name = self.var_category.get()
        category_id = self.category_map.get(selected_chinese_name, "others")
        upload_url = f"{config.API_BASE_URL}/api/tools/{category_id}/upload"

        try:
            # 💡 核心新增：组装双文件上传负载
            files = {
                "file": (os.path.basename(self.upload_file_path), open(self.upload_file_path, "rb"))
            }
            if self.upload_icon_path:
                files["icon"] = (os.path.basename(self.upload_icon_path), open(self.upload_icon_path, "rb"))

            data = {
                "name": self.entry_name.get(),
                "desc": self.entry_desc.get(),
                "tool_type": self.var_type.get(),
                "version": self.entry_version.get(),
            }
            
            response = requests.post(upload_url, files=files, data=data, timeout=60)
            response.raise_for_status()

            self.after(0, lambda: messagebox.showinfo("成功", "🎉 软件与图标已成功发布并写入云端数据库！"))
            self.after(0, self._reset_upload_form)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("上传失败", f"发生错误:\n{e}"))
        finally:
            self.after(0, lambda: self.btn_upload.configure(state="normal", text="🚀 立即上传并发布到云端"))

    def _reset_upload_form(self):
        """重置上传表单"""
        self.entry_name.delete(0, 'end')
        self.entry_desc.delete(0, 'end')
        self.entry_version.delete(0, 'end')
        self.upload_file_path = None
        self.upload_icon_path = None
        self.lbl_file_path.configure(text="未选择任何文件", text_color="gray")
        self.lbl_icon_path.configure(text="未选择(默认文本图标)", text_color="gray")