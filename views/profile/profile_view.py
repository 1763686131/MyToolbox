import os
import threading
import json
import time
import requests
import urllib.parse
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import config


class ProfileView(ctk.CTkFrame):
    """个人中心与管理员后台视图（已加入：单选框表单、必填项校验、精准错误捕获、支持 ZIP 压缩包上传）"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.current_user = None
        self.cloud_text = ""  
        self.cloud_data_dict = {} 
        
        self.upload_file_path = None
        self.upload_icon_path = None 

        self._build_ui()

    def _build_ui(self):
        self.current_user = getattr(config, "CURRENT_USER", None)

        for widget in self.winfo_children():
            widget.destroy()

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(
            header_frame, text="👤 个人中心",
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
        ctk.CTkLabel(card, text="您当前是游客身份，基本功能可用", font=config.get_font(size=14), text_color="gray").pack(pady=(25, 15))
        ctk.CTkButton(card, text="立即登录系统", font=config.get_font(size=14, weight="bold"), height=36, command=self._show_login_dialog).pack(pady=(0, 25))

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
        sync_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        sync_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(sync_card, text="☁️ 云端工具库目录同步", font=config.get_font(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        self.sync_status_frame = ctk.CTkFrame(sync_card, fg_color="transparent")
        self.sync_status_frame.pack(fill="x", padx=20, pady=(5, 15))

        is_latest = getattr(config, "SYNC_IS_LATEST", False)

        if is_latest:
            self.sync_status_label = ctk.CTkLabel(self.sync_status_frame, text="✅ 数据已经是最新了", font=config.get_font(size=13), text_color="#10B981")
            self.sync_status_label.pack(side="left")
        else:
            self.sync_status_label = ctk.CTkLabel(self.sync_status_frame, text="尚未检测，请点击比对云端数据", font=config.get_font(size=13), text_color="gray")
            self.sync_status_label.pack(side="left")

            self.btn_check_sync = ctk.CTkButton(self.sync_status_frame, text="🔄 检测更新", font=config.get_font(size=13, weight="bold"), height=32, command=self._start_check_sync)
            self.btn_check_sync.pack(side="right", padx=10)

            self.btn_do_sync = ctk.CTkButton(self.sync_status_frame, text="⬇️ 立即同步", font=config.get_font(size=13, weight="bold"), height=32, fg_color="#1677FF", command=self._execute_sync)

    def _build_admin_card(self):
        admin_card = ctk.CTkFrame(self, fg_color=("#FFFBEB", "#26231C"), corner_radius=12, border_width=1, border_color=("#FDE68A", "#544319"))
        admin_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(admin_card, text="⚙️ 管理员控制台：发布/更新软件", text_color=("#D97706", "#F59E0B"), font=config.get_font(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        form_grid = ctk.CTkFrame(admin_card, fg_color="transparent")
        form_grid.pack(fill="x", padx=20, pady=(0, 15))
        form_grid.columnconfigure(1, weight=1)

        # 💡 必填项红色星号标识
        ctk.CTkLabel(form_grid, text="* 软件名称:", text_color="red", font=config.get_font(size=12, weight="bold")).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_name = ctk.CTkEntry(form_grid, placeholder_text="必填：例如：驱动大师", font=config.get_font(size=12))
        self.entry_name.grid(row=0, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_grid, text="* 软件简介:", text_color="red", font=config.get_font(size=12, weight="bold")).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_desc = ctk.CTkEntry(form_grid, placeholder_text="必填：一句话描述功能亮点", font=config.get_font(size=12))
        self.entry_desc.grid(row=1, column=1, sticky="ew", pady=6)

        # 💡 创新点 1：将下拉框改为直观的单选按钮 (Radio Button)
        ctk.CTkLabel(form_grid, text="* 工具类型:", text_color="red", font=config.get_font(size=12, weight="bold")).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
        type_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        type_frame.grid(row=2, column=1, sticky="w", pady=6)
        
        self.var_type = ctk.StringVar(value="本地文件")
        # 🔥 修改提示文字，明确支持压缩包
        ctk.CTkRadioButton(type_frame, text="本地文件/压缩包 (.zip/.exe)", variable=self.var_type, value="本地文件", font=config.get_font(size=12), command=self._on_type_change).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(type_frame, text="网页链接 (HTML)", variable=self.var_type, value="网页链接 HTML", font=config.get_font(size=12), command=self._on_type_change).pack(side="left")

        # 💡 创新点 2：分类也改为单选按钮，并支持换行排列
        ctk.CTkLabel(form_grid, text="* 保存分类:", text_color="red", font=config.get_font(size=12, weight="bold")).grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
        self.category_map = {cat["name"]: cat["id"] for cat in getattr(config, "NAV_MENU", [])}
        cat_names_list = list(self.category_map.keys())
        self.var_category = ctk.StringVar(value=cat_names_list[0] if cat_names_list else "无分类")
        
        cat_frame = ctk.CTkFrame(form_grid, fg_color="transparent")
        cat_frame.grid(row=3, column=1, sticky="ew", pady=6)
        for i, cat_name in enumerate(cat_names_list):
            rb = ctk.CTkRadioButton(cat_frame, text=cat_name, variable=self.var_category, value=cat_name, font=config.get_font(size=12))
            rb.grid(row=i // 3, column=i % 3, padx=(0, 15), pady=(0, 8), sticky="w") # 每 3 个换一行

        ctk.CTkLabel(form_grid, text="版本编号:", font=config.get_font(size=12, weight="bold")).grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
        self.entry_version = ctk.CTkEntry(form_grid, placeholder_text="例如：v1.0.0", font=config.get_font(size=12))
        self.entry_version.grid(row=4, column=1, sticky="ew", pady=6)

        ctk.CTkLabel(form_grid, text="工具图标:", font=config.get_font(size=12, weight="bold")).grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)
        icon_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        icon_box.grid(row=5, column=1, sticky="ew", pady=6)
        
        self.icon_preview_lbl = ctk.CTkLabel(icon_box, text="🖼️", width=32, height=32, corner_radius=6, fg_color=("#F3F4F6", "#374151"))
        self.icon_preview_lbl.pack(side="left", padx=(0, 10))

        self.lbl_icon_path = ctk.CTkLabel(icon_box, text="未选择", text_color="gray", font=config.get_font(size=12))
        self.lbl_icon_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(icon_box, text="本地浏览", width=70, font=config.get_font(size=12), command=self._select_icon_file).pack(side="right")

        # ---------------- 动态切换区域 (网址 vs 文件) ----------------

        self.lbl_file_title = ctk.CTkLabel(form_grid, text="* 工具文件:", text_color="red", font=config.get_font(size=12, weight="bold"))
        self.file_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        # 🔥 修改提示文字，明确支持 .zip
        self.lbl_file_path = ctk.CTkLabel(self.file_box, text="必填：支持 .zip, .exe 或 .py", text_color="gray", font=config.get_font(size=12))
        self.lbl_file_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(self.file_box, text="📁 浏览文件", width=90, font=config.get_font(size=12), command=self._select_upload_file).pack(side="right")
        
        self.lbl_url_title = ctk.CTkLabel(form_grid, text="* 网页链接:", text_color="red", font=config.get_font(size=12, weight="bold"))
        self.url_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        self.entry_url = ctk.CTkEntry(self.url_box, placeholder_text="必填：例如: https://www.baidu.com", font=config.get_font(size=12))
        self.entry_url.pack(side="left", fill="x", expand=True)
        self.btn_fetch_icon = ctk.CTkButton(self.url_box, text="🔍 抓取图标", width=80, fg_color="#E6A23C", hover_color="#CF9236", font=config.get_font(size=12), command=self._start_fetch_favicon)
        self.btn_fetch_icon.pack(side="right", padx=(10, 0))

        # 初始布局：挂载文件区 (因为默认选项是本地文件)
        self.lbl_file_title.grid(row=6, column=0, sticky="e", padx=(0, 10), pady=6)
        self.file_box.grid(row=6, column=1, sticky="ew", pady=6)

        # -------------------------------------------------------------

        self.btn_upload = ctk.CTkButton(admin_card, text="🚀 立即上传并发布到云端", fg_color="#67C23A", hover_color="#529B2E", font=config.get_font(size=14, weight="bold"), height=40, command=self._start_upload_thread)
        self.btn_upload.pack(fill="x", padx=20, pady=(5, 20))


    # ------------------ 界面动态交互逻辑 ------------------

    def _on_type_change(self):
        """核心交互：监听单选框，智能切换必填组件区域"""
        selected_value = self.var_type.get()
        if selected_value == "网页链接 HTML":
            self.lbl_file_title.grid_remove()
            self.file_box.grid_remove()
            self.lbl_url_title.grid(row=6, column=0, sticky="e", padx=(0, 10), pady=6)
            self.url_box.grid(row=6, column=1, sticky="ew", pady=6)
        else:
            self.lbl_url_title.grid_remove()
            self.url_box.grid_remove()
            self.lbl_file_title.grid(row=6, column=0, sticky="e", padx=(0, 10), pady=6)
            self.file_box.grid(row=6, column=1, sticky="ew", pady=6)

    def _update_icon_preview(self, img_path):
        try:
            pil_image = Image.open(img_path)
            if pil_image.mode not in ("RGB", "RGBA"):
                pil_image = pil_image.convert("RGBA")
            ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(32, 32))
            self.icon_preview_lbl.configure(image=ctk_img, text="")
            
            short_name = os.path.basename(img_path)
            if len(short_name) > 15: short_name = short_name[:12] + "..."
            self.lbl_icon_path.configure(text=short_name, text_color="#1F2937")
        except Exception as e:
            print(f"预览加载失败: {e}")
            self.icon_preview_lbl.configure(image="", text="❌")

    def _start_fetch_favicon(self):
        url = self.entry_url.get().strip()
        if not url.startswith("http"):
            messagebox.showwarning("格式错误", "请填写以 http 或 https 开头的完整链接！")
            return
        
        self.btn_fetch_icon.configure(state="disabled", text="抓取中...")
        threading.Thread(target=self._task_fetch_favicon, args=(url,), daemon=True).start()

    def _task_fetch_favicon(self, url):
        try:
            domain = urllib.parse.urlparse(url).netloc
            icon_url = f"http://{domain}/favicon.ico"
            
            resp = requests.get(icon_url, timeout=5)
            if resp.status_code == 200 and len(resp.content) > 100:
                
                # 💡 核心修复：1. 改为存入 assets/icon 目录；2. 文件名加上时间戳防冲突
                timestamp = int(time.time() * 1000)  # 获取毫秒级时间戳
                temp_path = os.path.join(config.BASE_DIR, "assets", "icon", f"icon_{domain}_{timestamp}.ico")
                
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(resp.content)
                
                self.upload_icon_path = temp_path
                self.after(0, lambda: self._update_icon_preview(temp_path))
            else:
                self.after(0, lambda: messagebox.showinfo("未找到图标", "该网站根目录没有公开标准图标，请您手动截图上传。"))
        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror("网络错误", f"无法连接该网站抓取图标: {err}"))
        finally:
            self.after(0, lambda: self.btn_fetch_icon.configure(state="normal", text="🔍 抓取图标"))

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
        config.SYNC_IS_LATEST = True  
        self.sync_status_label.configure(text="✅ 数据已经是最新了", text_color="#10B981")
        if hasattr(self, 'btn_check_sync'): self.btn_check_sync.pack_forget()
        if hasattr(self, 'btn_do_sync'): self.btn_do_sync.pack_forget()

    def _execute_sync(self):
        self.btn_do_sync.configure(state="disabled", text="正在同步...")
        threading.Thread(target=self._task_execute_sync_and_icons, daemon=True).start()

    def _task_execute_sync_and_icons(self):
        try:
            base_dir = getattr(config, "BASE_DIR", os.getcwd())
            local_path = os.path.join(base_dir, "data", "appdata.json")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(self.cloud_text)
                
            for category in self.cloud_data_dict.get("categories", []):
                for tool in category.get("tools", []):
                    icon_path = tool.get("icon", "")
                    if icon_path and icon_path.endswith((".png", ".ico", ".jpg")):
                        local_icon_path = os.path.join(base_dir, icon_path)
                        if not os.path.exists(local_icon_path):
                            os.makedirs(os.path.dirname(local_icon_path), exist_ok=True)
                            try:
                                icon_resp = requests.get(f"{config.API_BASE_URL}/{icon_path}", timeout=10)
                                if icon_resp.status_code == 200:
                                    with open(local_icon_path, "wb") as f_icon:
                                        f_icon.write(icon_resp.content)
                            except Exception as icon_e:
                                print(f"拉取图标失败 {icon_path}: {icon_e}")
                
            self.after(0, self._show_synced)
            if hasattr(config, "reload_appdata"):
                self.after(0, config.reload_appdata)
            self.after(0, lambda: messagebox.showinfo("同步成功", "云端数据与图标已成功拉取覆盖！新工具已经就绪。"))
        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror("同步失败", f"发生错误: {err}"))
            self.after(0, lambda: self.btn_do_sync.configure(state="normal", text="⬇️ 立即同步"))

    # ------------------ 登录鉴权与上传逻辑 ------------------

    def _show_login_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("登录账户")
        
        win_w, win_h = 320, 300
        master = self.winfo_toplevel()
        master.update_idletasks() 
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (win_w // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (win_h // 2)
        dialog.geometry(f"{win_w}x{win_h}+{x}+{y}")
        dialog.resizable(False, False)
        dialog.transient(master)
        dialog.grab_set()

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
                    config.CURRENT_USER = resp.json().get("data")
                    dialog.destroy()
                    self._build_ui()  
                else:
                    messagebox.showerror("错误", resp.json().get("detail", "登录失败"), parent=dialog)
            except Exception as e:
                messagebox.showerror("网络异常", f"无法连接到 NAS 服务端: {e}", parent=dialog)

        ctk.CTkButton(dialog, text="立 即 登 录", height=38, font=config.get_font(size=14, weight="bold"), command=do_login).pack(fill="x", padx=40)

    def _logout(self):
        config.CURRENT_USER = None
        self._build_ui()

    def _select_icon_file(self):
        file_path = filedialog.askopenfilename(title="选择工具图标", filetypes=[("图片文件", "*.png;*.jpg;*.ico")])
        if file_path:
            self.upload_icon_path = file_path
            self._update_icon_preview(file_path)

    def _select_upload_file(self):
        # 🔥 核心修改：在这里增加了对 .zip 格式的支持，并将 .zip 放在默认可见项中
        file_path = filedialog.askopenfilename(
            title="选择要发布的软件包", 
            filetypes=[
                ("支持的工具类型", "*.zip;*.exe;*.py"), 
                ("文件夹压缩包 (含启动脚本)", "*.zip"),
                ("单文件程序", "*.exe"),
                ("Python 脚本", "*.py"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.upload_file_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_file_path.configure(text=filename, text_color=("#1F2937", "#F3F4F6"))
            if not self.entry_name.get():
                # 自动截取文件名（去掉 .zip 或 .exe 等后缀）作为软件名填入输入框
                self.entry_name.insert(0, os.path.splitext(filename)[0])

    def _start_upload_thread(self):
        # 💡 前端强拦截：表单必填项预校验
        if not self.entry_name.get() or not self.entry_desc.get():
            messagebox.showwarning("验证失败", "带 * 号的为必选项：请填写完整的名称和简介！")
            return
            
        if self.var_type.get() == "网页链接 HTML":
            if not self.entry_url.get():
                messagebox.showwarning("验证失败", "带 * 号的为必选项：请填写要收录的网址链接！")
                return
        else:
            if not getattr(self, "upload_file_path", None):
                # 🔥 验证提示同步修改
                messagebox.showwarning("验证失败", "带 * 号的为必选项：请先选择要上传的工具文件（.zip, .exe 或 .py）！")
                return

        self.btn_upload.configure(state="disabled", text="正在推送到云端，请稍候...")
        threading.Thread(target=self._upload_task, daemon=True).start()

    def _upload_task(self):
        selected_chinese_name = self.var_category.get()
        category_id = self.category_map.get(selected_chinese_name, "others")
        upload_url = f"{config.API_BASE_URL}/api/tools/{category_id}/upload"

        try:
            files = {}
            if self.upload_icon_path:
                files["icon"] = (os.path.basename(self.upload_icon_path), open(self.upload_icon_path, "rb"))

            data = {
                "name": self.entry_name.get(),
                "desc": self.entry_desc.get(),
                "tool_type": self.var_type.get(),
                "version": self.entry_version.get(),
            }

            if self.var_type.get() == "网页链接 HTML":
                data["url"] = self.entry_url.get().strip()
                dummy_path = os.path.join(config.BASE_DIR, "data", "url_dummy.txt")
                if not os.path.exists(dummy_path):
                    with open(dummy_path, "w") as f: f.write("link")
                files["file"] = ("url_dummy.txt", open(dummy_path, "rb"))
            else:
                files["file"] = (os.path.basename(self.upload_file_path), open(self.upload_file_path, "rb"))
            
            # 发起请求
            response = requests.post(upload_url, files=files, data=data, timeout=60)
            
            # 💡 详细错误解析拦截器：不管后端报什么错，全部解析出来展示给用户
            if response.status_code == 200:
                resp_json = response.json()
                if resp_json.get("status") == "success":
                    self.after(0, lambda: messagebox.showinfo("成功", "🎉 软件与图标已成功发布并写入云端数据库！"))
                    self.after(0, self._reset_upload_form)
                else:
                    error_msg = resp_json.get("message", "未知逻辑错误")
                    self.after(0, lambda e=error_msg: messagebox.showerror("上传被拒绝", f"服务端返回错误:\n{e}"))
            else:
                # 捕获 4xx (例如参数错误) 或 5xx (例如代码崩溃)
                error_msg = response.text
                try:
                    err_json = response.json()
                    error_msg = err_json.get("detail", err_json.get("message", response.text))
                except ValueError:
                    pass
                self.after(0, lambda code=response.status_code, msg=error_msg: messagebox.showerror("上传失败", f"HTTP {code} 服务器错误:\n{msg}"))

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: messagebox.showerror("网络错误", "无法连接到 NAS 服务端，请检查网络或确认服务端已启动！"))
        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror("意外错误", f"发生未知异常:\n{err}"))
        finally:
            self.after(0, lambda: self.btn_upload.configure(state="normal", text="🚀 立即上传并发布到云端"))

    def _reset_upload_form(self):
        self.entry_name.delete(0, 'end')
        self.entry_desc.delete(0, 'end')
        self.entry_version.delete(0, 'end')
        self.entry_url.delete(0, 'end')
        self.upload_file_path = None
        self.upload_icon_path = None
        # 🔥 上传成功后重置时的提示文字也改掉
        self.lbl_file_path.configure(text="必填：支持 .zip, .exe 或 .py", text_color="gray")
        self.lbl_icon_path.configure(text="未选择", text_color="gray")
        self.icon_preview_lbl.configure(image="", text="🖼️")