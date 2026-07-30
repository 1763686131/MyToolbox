import os
import time
import threading
import requests
from tkinter import messagebox
import customtkinter as ctk
import config


class CloudToolDialog(ctk.CTkToplevel):

    """万能三级弹窗：只要传入文件名，自动处理所有本地/云端逻辑（已接入子目录分类）"""

    def __init__(self, master, display_name, exe_name, sub_dir="others", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.display_name = display_name
        self.tool_name = exe_name 
        self.sub_dir = sub_dir    
        
        self.title(f"🚀 启动 {self.display_name}")
        
        # 🌟 修复 3：让下载弹窗相对于主窗口绝对居中
        win_w, win_h = 380, 240
        master.update_idletasks() # 确保获取到最新的主窗口数据
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (win_w // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (win_h // 2)
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        
        self.resizable(False, False)
        self.lift()
        self.focus_force()
        self.grab_set()

        try:
            base_dir = config.BASE_DIR
        except AttributeError:
            base_dir = os.getcwd()
            
        local_folder = os.path.join(base_dir, "tools", self.sub_dir)
        os.makedirs(local_folder, exist_ok=True) 
        
        self.exe_path = os.path.join(local_folder, self.tool_name)
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 界面标题也会根据传入的名字动态改变
        ctk.CTkLabel(
            self, text=self.display_name, font=config.get_font(size=14, weight="bold")
        ).pack(pady=(20, 5))

        self.status_label = ctk.CTkLabel(self, text="正在检测环境...", font=config.get_font(size=12))
        self.status_label.pack(pady=5)

        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=280)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(5, 2))
        
        self.percent_label = ctk.CTkLabel(
            self.progress_frame, text="0.00 MB / 0.00 MB (0%)", font=config.get_font(size=11), text_color="gray"
        )
        self.percent_label.pack()

        self.btn_action = ctk.CTkButton(
            self, text="检测中...", height=38, font=config.get_font(size=14, weight="bold"),
            command=self._on_button_click,
        )
        self.btn_action.pack(fill="x", padx=40, pady=15)

        self._check_local_file()

    def _check_local_file(self):
        if os.path.exists(self.exe_path):
            self.status_label.configure(text="状态: 找到内置程序，可随时启动", text_color="green")
            self.btn_action.configure(text="⚡ 立即运行软件", fg_color="#1677FF", state="normal")
            self.progress_frame.pack_forget() 
        else:
            self.status_label.configure(text="状态: 未在本地找到该软件", text_color="#E6A23C")
            self.btn_action.configure(text="⬇️ 从云端下载并运行", fg_color="#67C23A", state="normal")
            self.progress_frame.pack_forget() 

    def _on_button_click(self):
        if self.is_downloading: return
        if os.path.exists(self.exe_path):
            self._launch_exe()
        else:
            self._start_download()

    def _start_download(self):
        self.is_downloading = True
        self.btn_action.configure(text="正在下载中，请稍候...", state="disabled", fg_color="gray")
        self.status_label.configure(text="状态: 正在从服务器拉取文件...", text_color="#1677FF")
        
        self.progress_frame.pack(after=self.status_label, fill="x", pady=5)
        self.progress_bar.set(0)
        
        threading.Thread(target=self._download_task, daemon=True).start()

    def _download_task(self):
        # 🌟 修复 4：直接把 sub_dir 传给生成函数，彻底干掉错误的 replace 字符串替换逻辑
        download_url = config.get_api_download_url(self.tool_name, self.sub_dir)
        
        os.makedirs(os.path.dirname(self.exe_path), exist_ok=True)
        try:
            response = requests.get(download_url, stream=True, timeout=10)
            response.raise_for_status() 
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            last_update_time = 0
            
            with open(self.exe_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        current_time = time.time()
                        if current_time - last_update_time > 0.1 and total_size > 0:
                            percent = downloaded_size / total_size
                            self.after(0, self._update_progress_ui, percent, downloaded_size, total_size)
                            last_update_time = current_time
                            
            if total_size > 0:
                self.after(0, self._update_progress_ui, 1.0, total_size, total_size)
                
            self.after(0, self._on_download_complete)
            
        except requests.exceptions.RequestException as e:
            self.after(0, self._on_download_error, str(e))
            if os.path.exists(self.exe_path):
                os.remove(self.exe_path)

    def _update_progress_ui(self, percent, downloaded_size, total_size):
        self.progress_bar.set(percent)
        dl_mb = downloaded_size / (1024 * 1024)
        tot_mb = total_size / (1024 * 1024)
        self.percent_label.configure(text=f"{dl_mb:.1f} MB / {tot_mb:.1f} MB ({int(percent * 100)}%)")

    def _on_download_complete(self):
        self.is_downloading = False
        self._check_local_file() 
        self._launch_exe()

    def _on_download_error(self, error_msg):
        self.is_downloading = False
        self._check_local_file()
        messagebox.showerror("下载失败", f"无法从服务器获取文件，请检查网络！\n错误信息: {error_msg}")

    def _launch_exe(self):
        try:
            os.startfile(self.exe_path)
            self.destroy()
        except Exception as e:
            messagebox.showerror("启动失败", f"无法运行此程序: {e}")