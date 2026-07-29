import os
import threading
import json
import requests
from tkinter import filedialog, messagebox
import customtkinter as ctk
import config


class ProfileView(ctk.CTkFrame):
    """个人中心与管理员后台视图（支持游客鉴权与手动云端数据比对）"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # 核心鉴权状态：None 表示游客，登录后存储用户字典数据
        self.current_user = None
        self.cloud_text = ""  # 用于存放从云端拉取下来的新版 appdata.json 字符
        self.upload_file_path = None

        self._build_ui()

    def _build_ui(self):
        """动态构建整体界面（登录前后会重新调用渲染）"""
        for widget in self.winfo_children():
            widget.destroy()

        # 顶部标题栏
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(
            header_frame, text="👤 个人中心 & 管理后台",
            font=config.get_font(size=20, weight="bold"), text_color=("#1F2937", "#F3F4F6")
        ).pack(anchor="w")

        # ================== 模块 1：用户身份区 ==================
        if self.current_user is None:
            self._build_guest_card()
        else:
            self._build_user_card()

        # ================== 模块 2：云端数据同步区 (所有人开放) ==================
        self._build_sync_card()

        # ================== 模块 3：后台上传区 (仅限管理员可见) ==================
        if self.current_user and self.current_user.get("role") == "admin":
            self._build_admin_card()

    # ------------------ UI 绘制子方法 ------------------

    def _build_guest_card(self):
        """游客展示卡片：只有登录按钮"""
        card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(card, text="您当前是游客身份，部分高级功能已隐藏", font=config.get_font(size=14), text_color="gray").pack(pady=(25, 15))
        ctk.CTkButton(
            card, text="🔑 立即登录系统", font=config.get_font(size=14, weight="bold"), height=36,
            command=self._show_login_dialog
        ).pack(pady=(0, 25))

    def _build_user_card(self):
        """用户展示卡片：登录后显示资料"""
        info_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        info_card.pack(fill="x", padx=20, pady=10)

        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=15)
        
        # 头像
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
        
        # 退出登录按钮
        ctk.CTkButton(
            info_inner, text="退出登录", width=70, fg_color="#F56C6C", hover_color="#E6A23C", 
            font=config.get_font(size=12), command=self._logout
        ).pack(side="right")

    def _build_sync_card(self):
        """云端数据同步模块：两步走（手动检测 -> 发现不同 -> 同步更新）"""
        sync_card = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2B2B2B"), corner_radius=12, border_width=1, border_color=("#E5E7EB", "#374151"))
        sync_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(sync_card, text="☁️ 云端工具库目录同步", font=config.get_font(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        # 状态行框架
        self.sync_status_frame = ctk.CTkFrame(sync_card, fg_color="transparent")
        self.sync_status_frame.pack(fill="x", padx=20, pady=(5, 15))

        # 初始标签
        self.sync_status_label = ctk.CTkLabel(self.sync_status_frame, text="尚未检测，请点击比对云端数据", font=config.get_font(size=13), text_color="gray")
        self.sync_status_label.pack(side="left")

        # 初始显示的检测按钮
        self.btn_check_sync = ctk.CTkButton(
            self.sync_status_frame, text="🔄 检测更新", font=config.get_font(size=13, weight="bold"), height=32,
            command=self._start_check_sync
        )
        self.btn_check_sync.pack(side="right", padx=10)

        # 发现不同后才显示的【立即同步】按钮 (默认先创建但不 pack 渲染)
        self.btn_do_sync = ctk.CTkButton(
            self.sync_status_frame, text="⬇️ 立即同步", font=config.get_font(size=13, weight="bold"), height=32,
            fg_color="#1677FF", command=self._execute_sync
        )

    def _build_admin_card(self):
        """管理员上传面板（动态读取 JSON 下拉框）"""
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

        ctk.CTkLabel(form_grid, text="选择文件:", font=config.get_font(size=12, weight="bold")).grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)
        file_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        file_box.grid(row=5, column=1, sticky="ew", pady=6)
        self.lbl_file_path = ctk.CTkLabel(file_box, text="未选择任何文件", text_color="gray", font=config.get_font(size=12))
        self.lbl_file_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(file_box, text="📁 浏览文件", width=90, font=config.get_font(size=12), command=self._select_upload_file).pack(side="right")

        self.btn_upload = ctk.CTkButton(admin_card, text="🚀 立即上传并发布到云端", fg_color="#67C23A", hover_color="#529B2E", font=config.get_font(size=14, weight="bold"), height=40, command=self._start_upload_thread)
        self.btn_upload.pack(fill="x", padx=20, pady=(5, 20))


    # ------------------ 同步比对核心业务逻辑 ------------------

    def _start_check_sync(self):
        """第一步：点击检测更新按钮"""
        # 变成正在比对的文字
        self.sync_status_label.configure(text="正在与云端比对....", text_color=("#1F2937", "#F3F4F6"))
        
        # 隐藏检测按钮
        self.btn_check_sync.pack_forget() 
        self.btn_do_sync.pack_forget()    
        
        # 启动多线程进行网络请求，防止主界面卡住
        threading.Thread(target=self._task_check_sync, daemon=True).start()

    def _task_check_sync(self):
        """后台拉取云端 appdata.json 并与本地进行【结构化】对比"""
        try:
            # 1. 读取本地 JSON 数据为 Python 字典
            base_dir = getattr(config, "BASE_DIR", os.getcwd())
            local_path = os.path.join(base_dir, "data", "appdata.json")
            
            local_data = {}
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    try:
                        local_data = json.load(f)
                    except json.JSONDecodeError:
                        local_data = {}  # 如果本地文件损坏，当做空数据处理

            # 2. 从 NAS 请求最新 JSON 数据
            sync_url = f"{config.API_BASE_URL}/api/appdata"
            resp = requests.get(sync_url, timeout=5)
            resp.raise_for_status()
            
            # 保存云端的原始纯文本，留给用户点击“立即同步”时写入本地用
            self.cloud_text = resp.text  
            
            try:
                cloud_data = resp.json() # 将云端下发的数据也转为 Python 字典
            except ValueError:
                cloud_data = {}

            # 3. 💡 核心修复：直接比对字典内容，彻底无视空格和换行符的干扰！
            if local_data != cloud_data:
                self.after(0, self._show_sync_needed) # 内容真的不一样
            else:
                self.after(0, self._show_synced)      # 内容一模一样
                
        except Exception as e:
            self.after(0, lambda: self.sync_status_label.configure(text=f"❌ 无法连接云端: {e}", text_color="red"))
            self.after(0, lambda: self.btn_check_sync.pack(side="right", padx=10)) # 如果出错，把检测按钮重新显示出来
    def _show_sync_needed(self):
        """发现不一样：显示提示，并在右边出现【立即同步】按钮"""
        self.sync_status_label.configure(text="⚠️ 云端数据有新内容", text_color="#D97706")
        self.btn_do_sync.pack(side="right", padx=10) 

    def _show_synced(self):
        """发现一模一样：显示绿色提示，隐藏所有按钮"""
        self.sync_status_label.configure(text="✅ 数据已经是最新了", text_color="#10B981")
        self.btn_check_sync.pack_forget()
        self.btn_do_sync.pack_forget()

    def _execute_sync(self):
        """第二步：点击立即同步，覆盖本地文件"""
        try:
            base_dir = getattr(config, "BASE_DIR", os.getcwd())
            local_path = os.path.join(base_dir, "data", "appdata.json")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 将刚才拉取的 self.cloud_text 直接覆写本地
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(self.cloud_text)
                
            # 调用热更新刷新左侧导航栏
            if hasattr(config, "reload_appdata"):
                config.reload_appdata()
                
            # 同步完成后，变为绿色最新状态
            self._show_synced()
            messagebox.showinfo("同步成功", "本地数据已成功更新覆盖！新上的工具已经就绪。")
        except Exception as e:
            messagebox.showerror("写入失败", f"无法更新本地数据文件: {e}")


    # ------------------ 登录鉴权与上传逻辑 ------------------

    def _show_login_dialog(self):
        """弹出登录模态框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("登录账户")
        dialog.geometry("320x300")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
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
                    self.current_user = resp.json().get("data")
                    dialog.destroy()
                    self._build_ui()  
                else:
                    messagebox.showerror("错误", resp.json().get("detail", "登录失败"), parent=dialog)
            except Exception as e:
                messagebox.showerror("网络异常", f"无法连接到 NAS 服务端: {e}", parent=dialog)

        ctk.CTkButton(dialog, text="立 即 登 录", height=38, font=config.get_font(size=14, weight="bold"), command=do_login).pack(fill="x", padx=40)

    def _logout(self):
        self.current_user = None
        self._build_ui()

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
            messagebox.showwarning("提示", "请先选择要上传的文件！")
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
            with open(self.upload_file_path, "rb") as f:
                files = {"file": (os.path.basename(self.upload_file_path), f)}
                data = {
                    "name": self.entry_name.get(),
                    "desc": self.entry_desc.get(),
                    "tool_type": self.var_type.get(),
                    "version": self.entry_version.get(),
                }
                response = requests.post(upload_url, files=files, data=data, timeout=60)
                response.raise_for_status()

            self.after(0, lambda: messagebox.showinfo("成功", "🎉 软件已成功发布到 NAS！"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("上传失败", f"无法连接到 NAS 服务端:\n{e}"))
        finally:
            self.after(0, lambda: self.btn_upload.configure(state="normal", text="🚀 立即上传并发布到云端"))