import os
import time
import threading
import requests
import zipfile
import glob
import subprocess
from tkinter import messagebox
import customtkinter as ctk
import config


class CloudToolDialog(ctk.CTkToplevel):

    """万能三级弹窗：支持单文件(.exe)和文件夹(.zip)的智能下载、解压、与静默启动引擎"""

    def __init__(self, master, display_name, exe_name, sub_dir="others", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.display_name = display_name
        self.tool_name = exe_name 
        self.sub_dir = sub_dir    
        
        self.title(f"🚀 启动 {self.display_name}")
        
        # 🌟 让下载弹窗相对于主窗口绝对居中
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
        
        # 💡 新增引擎核心：判断是否是 zip 压缩包 (文件夹工具)
        self.is_zip = self.tool_name.lower().endswith(".zip")
        if self.is_zip:
            # 自动计算解压后的文件夹路径 (例如: 360.zip -> 360)
            self.extracted_folder_path = os.path.join(local_folder, self.tool_name[:-4])
        else:
            self.extracted_folder_path = None

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
        """智能检测本地文件或文件夹是否存在"""
        if self.is_zip:
            # 如果是 zip，必须检测解压后的文件夹是否存在
            file_exists = os.path.exists(self.extracted_folder_path) and os.path.isdir(self.extracted_folder_path)
        else:
            # 单文件正常检测
            file_exists = os.path.exists(self.exe_path)

        if file_exists:
            self.status_label.configure(text="状态: 找到内置程序，可随时启动", text_color="green")
            self.btn_action.configure(text="⚡ 立即运行软件", fg_color="#1677FF", state="normal")
            self.progress_frame.pack_forget() 
        else:
            self.status_label.configure(text="状态: 未在本地找到该软件", text_color="#E6A23C")
            self.btn_action.configure(text="⬇️ 从云端下载并运行", fg_color="#67C23A", state="normal")
            self.progress_frame.pack_forget() 

    def _on_button_click(self):
        if self.is_downloading: return
        
        # 智能拦截启动还是下载
        if self.is_zip and os.path.exists(self.extracted_folder_path):
            self._launch_exe()
        elif not self.is_zip and os.path.exists(self.exe_path):
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
        download_url = config.get_api_download_url(self.tool_name, self.sub_dir)
        os.makedirs(os.path.dirname(self.exe_path), exist_ok=True)
        
        try:
            response = requests.get(download_url, stream=True, timeout=10)
            response.raise_for_status() 
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            last_update_time = 0
            
            # 1. 下载阶段
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
            
            # 🚀 2. 智能解压阶段 (如果下载的是 ZIP 压缩包)
            if self.is_zip:
                self.after(0, lambda: self.status_label.configure(text="状态: 下载完成，正在解压部署...", text_color="#E6A23C"))
                self.after(0, lambda: self.btn_action.configure(text="部署中..."))
                
                try:
                    with zipfile.ZipFile(self.exe_path, 'r') as zip_ref:
                        zip_ref.extractall(self.extracted_folder_path)
                    
                    # 💡 3. 解压成功后，立即无痕删除原安装包，释放用户磁盘空间！
                    os.remove(self.exe_path)
                except Exception as e:
                    self.after(0, self._on_download_error, f"解压失败，文件可能已损坏: {e}")
                    return
                
            # 4. 全部完成，呼叫主线程恢复UI并启动
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
        messagebox.showerror("下载失败", f"无法从服务器获取文件或处理失败！\n错误信息: {error_msg}")

    def _launch_exe(self):
        """智能启动引擎：兼容单文件与文件夹脚本架构"""
        try:
            if self.is_zip:
                # ------------------- 文件夹模式启动 (.bat) -------------------
                if not os.path.exists(self.extracted_folder_path):
                    messagebox.showerror("错误", "未找到软件文件夹，可能被误删，请重新下载！")
                    return
                
                # 递归深入寻找所有的 .bat 文件（防止压缩包里套娃）
                bat_files = glob.glob(os.path.join(self.extracted_folder_path, "**", "*.bat"), recursive=True)
                
                if not bat_files:
                    messagebox.showerror("错误", "该工具文件夹内缺失 .bat 启动脚本，请联系管理员核对！")
                    return
                    
                target_bat = None
                # 优先级探测：寻找 start.bat 或 run.bat
                for bat in bat_files:
                    name_lower = os.path.basename(bat).lower()
                    if name_lower in ["start.bat", "run.bat"]:
                        target_bat = bat
                        break
                
                # 如果没有标准命名的，抓取找到的第一个 bat
                if not target_bat:
                    target_bat = bat_files[0]
                    
                # 🚀 隐蔽执行魔法 (无黑框启动)
                # 使用 subprocess.CREATE_NO_WINDOW 隐藏烦人的控制台
                creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                
                subprocess.Popen(
                    target_bat,
                    cwd=os.path.dirname(target_bat), # 确保运行环境在该脚本所在的深层文件夹内
                    creationflags=creation_flags
                )
                self.destroy()
                
            else:
                # ------------------- 传统单文件模式启动 (.exe) -------------------
                os.startfile(self.exe_path)
                self.destroy()
                
        except Exception as e:
            messagebox.showerror("启动失败", f"无法运行此程序: {e}")