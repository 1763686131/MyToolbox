import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pypdf import PdfReader, PdfWriter
import config

class PDFCropDialog(ctk.CTkToplevel):

  """三级：PDF 工具独立弹窗窗口（已修复按钮显示问题）"""

  def __init__(self, master, *args, **kwargs):
    super().__init__(master, *args, **kwargs)

    self.title("📄 PDF 上半部分批量截取合并工具")
    self.geometry("560x520")  # 💡 稍微调大高度，给控件充足空间
    self.resizable(False, False)

    # 确保窗口置顶与获得焦点
    self.lift()
    self.focus_force()
    self.grab_set()

    self._build_ui()

  def _build_ui(self):
    # 1. 选择输入文件夹
    f1 = ctk.CTkFrame(self, fg_color="transparent")
    f1.pack(side="top", fill="x", padx=20, pady=(15, 5))

    ctk.CTkLabel(
        f1,
        text="1. 选择 PDF 输入文件夹:",
        font = config.get_font(size=13, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))

    self.folder_path = ctk.StringVar()
    ctk.CTkEntry(
        f1,
        textvariable=self.folder_path,
        placeholder_text="点击右侧按钮选择文件夹...",
    ).pack(side="left", fill="x", expand=True, padx=(0, 10))
    ctk.CTkButton(
        f1, text="浏览...", width=80, command=self._select_folder
    ).pack(side="right")

    # 2. 选择指定输出文件路径
    f2 = ctk.CTkFrame(self, fg_color="transparent")
    f2.pack(side="top", fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        f2,
        text="2. 指定合并后的输出文件:",
        font = config.get_font(size=13, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))

    self.output_path = ctk.StringVar()
    ctk.CTkEntry(
        f2,
        textvariable=self.output_path,
        placeholder_text="默认保存在输入目录下，也可点击右侧另存为...",
    ).pack(side="left", fill="x", expand=True, padx=(0, 10))
    ctk.CTkButton(
        f2, text="另存为...", width=80, command=self._select_output_file
    ).pack(side="right")

    # 3. 比例设置
    f3 = ctk.CTkFrame(self, fg_color="transparent")
    f3.pack(side="top", fill="x", padx=20, pady=5)

    ctk.CTkLabel(
        f3,
        text="3. 截取比例 (默认 0.5 即保留上半部分):",
        font = config.get_font(size=13, weight="bold"),
    ).pack(anchor="w", pady=(0, 5))

    self.ratio_var = ctk.StringVar(value="0.5")
    ctk.CTkEntry(f3, textvariable=self.ratio_var, width=100).pack(
        side="left", padx=(0, 10)
    )
    ctk.CTkLabel(f3, text="范围 0.1~0.9", text_color="gray").pack(side="left")

    # 💡 【关键修复】：先把执行按钮固定锁定在最底部 (side="bottom")
    self.btn_run = ctk.CTkButton(
        self,
        text="🚀 开始处理并合并",
        height=40,
        font = config.get_font(size=14, weight="bold"),
        command=self._start_thread,
    )
    self.btn_run.pack(side="bottom", fill="x", padx=20, pady=(10, 20))

    # 4. 日志面板（最后 pack，它会自动挤在输入框和底端按钮之间）
    f4 = ctk.CTkFrame(self, fg_color="transparent")
    f4.pack(side="top", fill="both", expand=True, padx=20, pady=5)

    ctk.CTkLabel(
        f4, text="4. 处理进度与日志:", font = config.get_font(size=13, weight="bold")
    ).pack(anchor="w", pady=(0, 5))

    self.log_text = ctk.CTkTextbox(f4)
    self.log_text.pack(fill="both", expand=True)

  def _select_folder(self):
    """选择输入目录，并智能生成默认输出文件路径"""
    path = filedialog.askdirectory()
    if path:
      self.folder_path.set(path)
      if not self.output_path.get():
        default_out = os.path.join(path, "合并完成_仅上半部分.pdf")
        self.output_path.set(default_out)

  def _select_output_file(self):
    """弹出保存文件选择框，让用户自由选择路径和文件名"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF 文件", "*.pdf")],
        title="选择合并后文件的保存位置",
    )
    if file_path:
      self.output_path.set(file_path)

  def log(self, msg):
    self.log_text.insert("end", msg + "\n")
    self.log_text.see("end")

  def _start_thread(self):
    threading.Thread(target=self._process_pdfs, daemon=True).start()

  def _process_pdfs(self):
    folder = self.folder_path.get()
    out_file = self.output_path.get()

    if not folder or not os.path.exists(folder):
      messagebox.showwarning("提示", "请先选择有效的 PDF 输入文件夹！")
      return

    if not out_file:
      messagebox.showwarning("提示", "请指定合并后 PDF 的保存路径！")
      return

    try:
      split_ratio = float(self.ratio_var.get())
    except ValueError:
      messagebox.showerror("错误", "截取比例必须为数字！")
      return

    self.btn_run.configure(state="disabled")
    self.log("🚀 开始扫描 PDF 文件...")

    pdf_files = sorted(
        [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    )
    if not pdf_files:
      self.log("⚠️ 目录内未找到任何 PDF 文件！")
      self.btn_run.configure(state="normal")
      return

    writer = PdfWriter()
    total_pages = 0

    for file_name in pdf_files:
      file_path = os.path.join(folder, file_name)
      try:
        reader = PdfReader(file_path)
        for page in reader.pages:
          ll_x = float(page.mediabox.lower_left[0])
          ll_y = float(page.mediabox.lower_left[1])
          ur_x = float(page.mediabox.upper_right[0])
          ur_y = float(page.mediabox.upper_right[1])

          mid_y = ll_y + (ur_y - ll_y) * (1 - split_ratio)
          page.mediabox.lower_left = (ll_x, mid_y)
          page.cropbox.lower_left = (ll_x, mid_y)

          writer.add_page(page)
          total_pages += 1
        self.log(f"  ✓ 已完成: {file_name}")
      except Exception as e:
        self.log(f"  ✗ 出错 [{file_name}]: {e}")

    try:
      out_dir = os.path.dirname(out_file)
      if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

      with open(out_file, "wb") as f_out:
        writer.write(f_out)
      self.log(f"\n🎉 处理完毕！共合并 {total_pages} 页。")
      self.log(f"👉 保存文件至: {out_file}")
      messagebox.showinfo("成功", f"处理完成！已保存至:\n{out_file}")
    except Exception as e:
      self.log(f"❌ 保存合并文件失败: {e}")

    self.btn_run.configure(state="normal")