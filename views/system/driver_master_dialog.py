import os
import threading
import requests
from tkinter import messagebox
import customtkinter as ctk
import config


class DriverMasterDialog(ctk.CTkToplevel):

    """三级：第三方软件快捷启动/下载器"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.title("🚀 启动驱动大师")
        # 窗口稍微加高一点，给进度条留出空间
        self.geometry("380x240")
        self.resizable(False, False)

        self.lift()
        self.focus_force()
        self.grab_set()

        # 核心变量配置
        self.tool_name = "360驱动大师网卡版2.0.0.2040.exe"
        self.exe_path = config.get_tool_path(self.tool_name)
        
        # 你的 NAS API 基础地址（本地测试用 127.0.0.1，以后改成花生壳域名即可）
        self.api_base_url = "http://127.0.0.1:4566"
        
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. 标题
        ctk.CTkLabel(
            self, text="360驱动大师网卡版", font=config.get_font(size=14, weight="bold")
        ).pack(pady=(20, 5))

        # 2. 状态文字
        self.status_label = ctk.CTkLabel(
            self, text="正在检测环境...", font=config.get_font(size=12)
        )
        self.status_label.pack(pady=5)

        # 3. 隐藏的进度条组件 (默认不显示，下载时才出来)
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=280)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(5, 2))
        
        self.percent_label = ctk.CTkLabel(
            self.progress_frame, text="0.00 MB / 0.00 MB (0%)", font=config.get_font(size=11), text_color="gray"
        )
        self.percent_label.pack()

        # 4. 操作按钮
        self.btn_action = ctk.CTkButton(
            self,
            text="检测中...",
            height=38,
            font=config.get_font(size=14, weight="bold"),
            command=self._on_button_click,
        )
        self.btn_action.pack(fill="x", padx=40, pady=15)

        # 5. 初始化状态检查
        self._check_local_file()

    def _check_local_file(self):
        """检测本地文件，并根据情况改变 UI 状态"""
        if os.path.exists(self.exe_path):
            self.status_label.configure(text="状态: 找到内置程序，可随时启动", text_color="green")
            self.btn_action.configure(text="⚡ 立即运行软件", fg_color="#1677FF", state="normal")
            self.progress_frame.pack_forget() # 隐藏进度条
        else:
            self.status_label.configure(text="状态: 未在本地找到该软件", text_color="#E6A23C")
            self.btn_action.configure(text="⬇️ 从云端下载并运行", fg_color="#67C23A", state="normal")
            self.progress_frame.pack_forget() # 隐藏进度条

    def _on_button_click(self):
        """按钮点击事件路由"""
        if self.is_downloading:
            return

        if os.path.exists(self.exe_path):
            self._launch_exe()
        else:
            self._start_download()

    def _start_download(self):
        """准备下载并启动子线程"""
        self.is_downloading = True
        self.btn_action.configure(text="正在下载中，请稍候...", state="disabled", fg_color="gray")
        self.status_label.configure(text="状态: 正在从服务器拉取文件...", text_color="#1677FF")
        
        # 显示进度条
        self.progress_frame.pack(after=self.status_label, fill="x", pady=5)
        self.progress_bar.set(0)
        
        # 启动后台下载线程 (避免卡死主界面)
        threading.Thread(target=self._download_task, daemon=True).start()

    def _download_task(self):
        """在后台线程执行真实的网络下载 (流式下载)"""
        download_url = f"{self.api_base_url}/api/tools/{self.tool_name}/download"
        
        # 确保本地 tools 文件夹存在
        os.makedirs(os.path.dirname(self.exe_path), exist_ok=True)
        
        try:
            # stream=True 意味着边下边存，防止大文件撑爆内存
            response = requests.get(download_url, stream=True, timeout=10)
            response.raise_for_status() # 检查是否 404
            
            # 获取文件总大小 (通过 API 的 Headers)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.exe_path, "wb") as file:
                # 每次读取 8KB 数据
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 计算进度并通过 self.after 安全地通知前端刷新 UI
                        if total_size > 0:
                            percent = downloaded_size / total_size
                            self.after(0, self._update_progress_ui, percent, downloaded_size, total_size)
                            
            # 下载完成，自动触发运行逻辑
            self.after(0, self._on_download_complete)
            
        except requests.exceptions.RequestException as e:
            # 下载报错处理
            self.after(0, self._on_download_error, str(e))
            # 如果下了一半断网了，把残缺的文件删掉防错
            if os.path.exists(self.exe_path):
                os.remove(self.exe_path)

    def _update_progress_ui(self, percent, downloaded_size, total_size):
        """实时更新进度条 UI (必须通过 self.after 调用)"""
        self.progress_bar.set(percent)
        dl_mb = downloaded_size / (1024 * 1024)
        tot_mb = total_size / (1024 * 1024)
        self.percent_label.configure(
            text=f"{dl_mb:.1f} MB / {tot_mb:.1f} MB ({int(percent * 100)}%)"
        )

    def _on_download_complete(self):
        """下载完成后的收尾工作"""
        self.is_downloading = False
        self._check_local_file() # 重新检测并变绿
        
        # 立即启动！
        self._launch_exe()

    def _on_download_error(self, error_msg):
        """下载出错时的 UI 恢复"""
        self.is_downloading = False
        self._check_local_file()
        messagebox.showerror("下载失败", f"无法从服务器获取文件，请检查网络！\n错误信息: {error_msg}")

    def _launch_exe(self):
        """启动外部 EXE"""
        try:
            os.startfile(self.exe_path)
            self.destroy()
        except Exception as e:
            messagebox.showerror("启动失败", f"无法运行此程序: {e}")