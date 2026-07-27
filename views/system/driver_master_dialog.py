import os
import subprocess
from tkinter import messagebox
import customtkinter as ctk
import config

class DriverMasterDialog(ctk.CTkToplevel):

  """三级：第三方软件（驱动大师）快捷启动器"""

  def __init__(self, master, *args, **kwargs):
    super().__init__(master, *args, **kwargs)

    self.title("🚀 启动驱动大师")
    self.geometry("380x200")
    self.resizable(False, False)

    self.lift()
    self.focus_force()
    self.grab_set()

    # 1. 相对路径指向 tools 目录下的 exe
    # 获取项目根目录路径
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    self.exe_path = os.path.join(base_dir, "tools", "360驱动大师网卡版2.0.0.2040.exe")

    self._build_ui()

  def _build_ui(self):
    ctk.CTkLabel(
        self, text="360驱动大师网卡版", font=config.get_font(size=13, weight="bold")
    ).pack(pady=(20, 5))

    # 显示路径检测状态
    if os.path.exists(self.exe_path):
      status_text = "状态: 找到内置程序，可随时启动"
      status_color = "green"
    else:
      status_text = f"状态: 未找到文件 ({self.exe_path})"
      status_color = "red"

    ctk.CTkLabel(
        self, text=status_text, text_color=status_color, font=config.get_font(size=12)
    ).pack(pady=5)

    # 启动按钮
    btn_launch = ctk.CTkButton(
        self,
        text="⚡ 立即运行软件",
        height=38,
        font=config.get_font(size=14, weight="bold"),
        fg_color="#1677FF",
        command=self._launch_exe,
    )
    btn_launch.pack(fill="x", padx=30, pady=20)

  def _launch_exe(self):
    """启动外部 EXE"""
    if not os.path.exists(self.exe_path):
      messagebox.showerror(
          "找不到文件", f"未在以下位置找到目标软件：\n{self.exe_path}"
      )
      return

    try:
      # 在 Windows 上最优雅地打开软文件/程序（不会弹出黑框）
      os.startfile(self.exe_path)
      # 也可以使用：subprocess.Popen([self.exe_path])

      # 启动后，把这个 Python 提示小弹窗自动关掉
      self.destroy()
    except Exception as e:
      messagebox.showerror("启动失败", f"无法运行此程序: {e}")