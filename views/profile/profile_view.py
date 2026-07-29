import os
import threading
import requests
from tkinter import filedialog, messagebox
import customtkinter as ctk
import config


class ProfileView(ctk.CTkFrame):
    """个人中心与管理员后台视图（已优化布局与美化）"""

    def __init__(self, master, **kwargs):
        # 💡 核心修复：继承普通 CTkFrame，避免与外层 ToolGridView 的滚动条冲突
        super().__init__(master, fg_color="transparent", **kwargs)

        # 1. 模拟用户数据（真实开发中可从全局状态或 API 获取）
        self.user_data = {
            "id": "001",
            "name": "小乐",
            "role": "admin",  # 'admin' 超级管理员 | 'user' 普通用户
            "cloud_items": [
                {"name": "驱动大师.exe", "category": "system_files"},
                {"name": "连点器.exe", "category": "games"},
            ],
        }

        self.upload_file_path = None
        self._build_ui()
        self._check_local_sync_status()

    def _build_ui(self):
        """构建整体界面布局"""
        # 顶部标题栏
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header_frame,
            text="👤 个人中心 & 管理后台",
            font=config.get_font(size=20, weight="bold"),
            text_color=("#1F2937", "#F3F4F6"),
        ).pack(anchor="w")

        # ================== 1. 用户信息卡片 ==================
        info_card = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2B2B2B"),
            corner_radius=12,
            border_width=1,
            border_color=("#E5E7EB", "#374151"),
        )
        info_card.pack(fill="x", padx=20, pady=10)

        # 头像与基本信息（水平排布）
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(info_inner, text="🧑‍💻", font=ctk.CTkFont(size=42)).pack(
            side="left", padx=(0, 15)
        )

        user_text_box = ctk.CTkFrame(info_inner, fg_color="transparent")
        user_text_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            user_text_box,
            text=f"你好，{self.user_data['name']} (ID: {self.user_data['id']})",
            font=config.get_font(size=16, weight="bold"),
        ).pack(anchor="w")

        role_badge_text = (
            "✨ 超级管理员账号"
            if self.user_data["role"] == "admin"
            else "👤 普通用户账号"
        )
        ctk.CTkLabel(
            user_text_box,
            text=role_badge_text,
            text_color="#1677FF" if self.user_data["role"] == "admin" else "gray",
            font=config.get_font(size=12),
        ).pack(anchor="w", pady=(3, 0))

        # ================== 2. 云端工具同步中心 ==================
        sync_card = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2B2B2B"),
            corner_radius=12,
            border_width=1,
            border_color=("#E5E7EB", "#374151"),
        )
        sync_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            sync_card,
            text="☁️ 云端工具库同步状态",
            font=config.get_font(size=15, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(15, 5))

        self.sync_status_label = ctk.CTkLabel(
            sync_card, text="正在扫描本地环境...", font=config.get_font(size=12)
        )
        self.sync_status_label.pack(anchor="w", padx=20, pady=5)

        self.btn_sync = ctk.CTkButton(
            sync_card,
            text="🔄 一键同步缺失工具",
            font=config.get_font(size=13, weight="bold"),
            height=34,
            corner_radius=6,
            state="disabled",
            command=self._start_sync_tools,
        )
        self.btn_sync.pack(anchor="w", padx=20, pady=(5, 15))

        # ================== 3. 管理员专属：发版上传控制台 ==================
        if self.user_data["role"] == "admin":
            admin_card = ctk.CTkFrame(
                self,
                fg_color=("#FFFBEB", "#26231C"),
                corner_radius=12,
                border_width=1,
                border_color=("#FDE68A", "#544319"),
            )
            admin_card.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(
                admin_card,
                text="⚙️ 管理员控制台：发布/更新软件",
                text_color=("#D97706", "#F59E0B"),
                font=config.get_font(size=15, weight="bold"),
            ).pack(anchor="w", padx=20, pady=(15, 10))

            # 网格化表单（解决拉伸和不齐问题）
            form_grid = ctk.CTkFrame(admin_card, fg_color="transparent")
            form_grid.pack(fill="x", padx=20, pady=(0, 15))
            form_grid.columnconfigure(1, weight=1)  # 让输入框自动拉伸

            # 表单项 1: 名称
            ctk.CTkLabel(
                form_grid,
                text="软件名称:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
            self.entry_name = ctk.CTkEntry(
                form_grid,
                placeholder_text="例如：驱动大师",
                font=config.get_font(size=12),
            )
            self.entry_name.grid(row=0, column=1, sticky="ew", pady=6)

            # 表单项 2: 简介
            ctk.CTkLabel(
                form_grid,
                text="软件简介:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
            self.entry_desc = ctk.CTkEntry(
                form_grid,
                placeholder_text="一句话描述功能亮点",
                font=config.get_font(size=12),
            )
            self.entry_desc.grid(row=1, column=1, sticky="ew", pady=6)

            # 表单项 3: 类型
            ctk.CTkLabel(
                form_grid,
                text="工具类型:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
            self.var_type = ctk.StringVar(value=".exe文件")
            opt_type = ctk.CTkOptionMenu(
                form_grid,
                values=[".exe文件", "网页链接 HTML"],
                variable=self.var_type,
                font=config.get_font(size=12),
            )
            opt_type.grid(row=2, column=1, sticky="w", pady=6)

            # 表单项 4: 栏目子目录 (动态读取 appdata.json)
            ctk.CTkLabel(
                form_grid,
                text="保存分类:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
            
            # 💡 核心：遍历 config.NAV_MENU，提取出中文名字和英文 ID 的映射
            self.category_map = {cat["name"]: cat["id"] for cat in config.NAV_MENU}
            cat_names_list = list(self.category_map.keys()) # 得到类似 ["系统维护", "游戏辅助"]
            
            self.var_category = ctk.StringVar(value=cat_names_list[0] if cat_names_list else "无分类")
            opt_cat = ctk.CTkOptionMenu(
                form_grid,
                values=cat_names_list, # 下拉框直接显示友好的中文名！
                variable=self.var_category,
                font=config.get_font(size=12),
            )
            opt_cat.grid(row=3, column=1, sticky="w", pady=6)

            # 表单项 5: 版本号
            ctk.CTkLabel(
                form_grid,
                text="版本编号:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=4, column=0, sticky="e", padx=(0, 10), pady=6)
            self.entry_version = ctk.CTkEntry(
                form_grid,
                placeholder_text="例如：v1.0.0",
                font=config.get_font(size=12),
            )
            self.entry_version.grid(row=4, column=1, sticky="ew", pady=6)

            # 表单项 6: 软件包文件选择
            ctk.CTkLabel(
                form_grid,
                text="选择文件:",
                font=config.get_font(size=12, weight="bold"),
            ).grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)

            file_selector_box = ctk.CTkFrame(form_grid, fg_color="transparent")
            file_selector_box.grid(row=5, column=1, sticky="ew", pady=6)

            self.lbl_file_path = ctk.CTkLabel(
                file_selector_box,
                text="未选择任何本地文件",
                text_color="gray",
                font=config.get_font(size=12),
                anchor="w",
            )
            self.lbl_file_path.pack(side="left", fill="x", expand=True)

            ctk.CTkButton(
                file_selector_box,
                text="📁 浏览文件",
                width=90,
                height=30,
                font=config.get_font(size=12),
                command=self._select_upload_file,
            ).pack(side="right")

            # 提交上传按钮
            self.btn_upload = ctk.CTkButton(
                admin_card,
                text="🚀 立即上传并发布到 NAS 云端",
                fg_color="#67C23A",
                hover_color="#529B2E",
                font=config.get_font(size=14, weight="bold"),
                height=40,
                corner_radius=8,
                command=self._start_upload_thread,
            )
            self.btn_upload.pack(fill="x", padx=20, pady=(5, 20))

    # ================== 业务逻辑区 ==================

    def _check_local_sync_status(self):
        """对比云端清单与本地是否存在文件"""
        base_dir = getattr(config, "BASE_DIR", os.getcwd())
        missing_tools = []

        for tool in self.user_data["cloud_items"]:
            local_path = os.path.join(
                base_dir, "tools", tool["category"], tool["name"]
            )
            if not os.path.exists(local_path):
                missing_tools.append(tool["name"])

        if missing_tools:
            self.sync_status_label.configure(
                text=f"⚠️ 检测到 {len(missing_tools)} 个云端工具未同步至本地 (例如: {missing_tools[0]})",
                text_color="#D97706",
            )
            self.btn_sync.configure(state="normal", fg_color="#1677FF")
        else:
            self.sync_status_label.configure(
                text="✅ 所有云端工具已同步至本地，环境完美运行。",
                text_color="#10B981",
            )
            self.btn_sync.configure(state="disabled", fg_color="gray")

    def _start_sync_tools(self):
        self.btn_sync.configure(state="disabled", text="正在后台同步中...")
        messagebox.showinfo(
            "同步提示",
            "已开始拉取云端应用，缺失的文件将自动存入对应的 tools 目录！",
        )
        self.after(2000, self._mock_sync_complete)

    def _mock_sync_complete(self):
        self._check_local_sync_status()
        self.btn_sync.configure(text="🔄 一键同步缺失工具")

    def _select_upload_file(self):
        file_path = filedialog.askopenfilename(
            title="选择要发布的软件包或 HTML"
        )
        if file_path:
            self.upload_file_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_file_path.configure(
                text=filename, text_color=("#1F2937", "#F3F4F6")
            )

            if not self.entry_name.get():
                self.entry_name.insert(0, os.path.splitext(filename)[0])

    def _start_upload_thread(self):
        if not self.upload_file_path:
            messagebox.showwarning("提示", "请先选择要上传的文件！")
            return
        if not self.entry_name.get() or not self.entry_desc.get():
            messagebox.showwarning("提示", "请填写完整的名称和简介！")
            return

        self.btn_upload.configure(
            state="disabled", text="正在推送到 NAS，请稍候..."
        )
        threading.Thread(target=self._upload_task, daemon=True).start()

    def _upload_task(self):
        # 💡 核心：把下拉框选中的中文（如“系统维护”），反向查出英文ID（如“system”）
        selected_chinese_name = self.var_category.get()
        category_id = self.category_map.get(selected_chinese_name, "others")
        
        # 请根据实际情况填入你的 NAS 局域网/公网接口地址
        upload_url = f"http://127.0.0.1:4566/api/tools/{category_id}/upload"

        try:
            with open(self.upload_file_path, "rb") as f:
                files = {"file": (os.path.basename(self.upload_file_path), f)}
                data = {
                    "name": self.entry_name.get(),
                    "desc": self.entry_desc.get(),
                    "tool_type": self.var_type.get(),
                    "version": self.entry_version.get(),
                }
                response = requests.post(
                    upload_url, files=files, data=data, timeout=60
                )
                response.raise_for_status()

            self.after(
                0, lambda: messagebox.showinfo("成功", "🎉 软件已成功发布到 NAS！")
            )
        except Exception as e:
            self.after(
                0,
                lambda: messagebox.showerror(
                    "上传失败", f"无法连接到 NAS 服务端:\n{e}"
                ),
            )
        finally:
            self.after(
                0,
                lambda: self.btn_upload.configure(
                    state="normal", text="🚀 立即上传并发布到 NAS 云端"
                ),
            )