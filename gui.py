#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import re
import csv
import time
from datetime import datetime

import location


class PhoneQueryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("手机号归属地批量查询工具 v1.0")
        self.root.geometry("800x600")

        # 查询状态
        self.is_querying = False
        self.current_index = 0
        self.phone_list = []
        self.results = []

        self.setup_ui()

    def setup_ui(self):
        """设置界面布局"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入区域", padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(input_frame, text="手机号列表（每行一个）:").grid(row=0, column=0, sticky=tk.W)

        self.phone_text = scrolledtext.ScrolledText(input_frame, width=60, height=8)
        self.phone_text.grid(row=1, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))

        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5)

        ttk.Button(button_frame, text="导入手机号", command=self.import_phones).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清空列表", command=self.clear_phones).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="开始查询", command=self.start_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="停止查询", command=self.stop_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="导出结果", command=self.export_results).pack(side=tk.LEFT, padx=2)

        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="查询进度", padding="5")
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status_var = tk.StringVar(value="准备就绪，请输入手机号")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky=tk.W)

        # 结果区域
        result_frame = ttk.LabelFrame(main_frame, text="查询结果", padding="5")
        result_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 创建结果表格
        columns = ("手机号", "归属地", "运营商", "区号", "邮编", "状态")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)

        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        input_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

    def import_phones(self):
        """导入手机号文件"""
        filename = filedialog.askopenfilename(
            title="选择手机号文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.phone_text.delete(1.0, tk.END)
                    self.phone_text.insert(1.0, content)
                messagebox.showinfo("成功", f"已导入文件: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导入文件失败: {str(e)}")

    def clear_phones(self):
        """清空手机号列表"""
        self.phone_text.delete(1.0, tk.END)

    def validate_phones(self):
        """验证手机号格式"""
        content = self.phone_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "请输入手机号")
            return False

        phones = [p.strip() for p in content.split('\n') if p.strip()]
        valid_phones = []

        for phone in phones:
            if re.match(r'^1[3-9]\d{9}$', phone):
                valid_phones.append(phone)
            else:
                print(f"无效手机号: {phone}")

        if not valid_phones:
            messagebox.showerror("错误", "未找到有效的手机号")
            return False

        self.phone_list = valid_phones
        return True

    def start_query(self):
        """开始查询"""
        if not self.validate_phones():
            return

        if self.is_querying:
            messagebox.showwarning("警告", "查询正在进行中")
            return

        # 清空之前的结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        self.results = []
        self.is_querying = True
        self.current_index = 0

        # 在新线程中执行查询
        thread = threading.Thread(target=self.batch_query)
        thread.daemon = True
        thread.start()

    def stop_query(self):
        """停止查询"""
        self.is_querying = False
        self.status_var.set("查询已停止")

    def batch_query(self):
        """批量查询主逻辑"""
        total = len(self.phone_list)

        for i, phone in enumerate(self.phone_list):
            if not self.is_querying:
                break

            self.current_index = i

            # 更新进度
            progress = (i / total) * 100
            self.progress_var.set(progress)
            self.status_var.set(f"正在查询 ({i + 1}/{total}): {phone}")

            # 执行查询
            result = location.query_single_phone(phone)
            self.results.append(result)

            # 在GUI线程中更新结果
            self.root.after(0, self.update_result_tree, result)

            # 延迟，避免请求过快
            time.sleep(1)

        # 查询完成
        self.is_querying = False
        self.progress_var.set(100)
        self.status_var.set(f"查询完成! 成功: {len([r for r in self.results if r['success']])}/{total}")

    def update_result_tree(self, result):
        """更新结果表格"""
        if result['success']:
            data = result['data']
            values = (
                result['phone'],
                data.get('location', ''),
                data.get('operator', ''),
                data.get('area_code', ''),
                data.get('zip_code', ''),
                '成功'
            )
            self.result_tree.insert('', tk.END, values=values)
        else:
            values = (
                result['phone'],
                '', '', '', '',
                f"失败: {result.get('error', '')}"
            )
            self.result_tree.insert('', tk.END, values=values)

    def export_results(self):
        """导出结果到文件"""
        if not self.results:
            messagebox.showwarning("警告", "没有可导出的结果")
            return

        filename = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    self.export_to_csv(filename)
                elif filename.endswith('.xlsx'):
                    self.export_to_excel(filename)
                else:
                    self.export_to_csv(filename + '.csv')

                messagebox.showinfo("成功", f"结果已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_to_csv(self, filename):
        """导出到CSV"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['手机号', '归属地', '运营商', '区号', '邮编', '状态', '查询时间'])

            for result in self.results:
                if result['success']:
                    data = result['data']
                    writer.writerow([
                        result['phone'],
                        data.get('location', ''),
                        data.get('operator', ''),
                        data.get('area_code', ''),
                        data.get('zip_code', ''),
                        '成功',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ])
                else:
                    writer.writerow([
                        result['phone'],
                        '', '', '', '',
                        f"失败: {result.get('error', '')}",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ])

    def export_to_excel(self, filename):
        """导出到Excel（需要安装openpyxl）"""
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "手机号查询结果"

            # 写入表头
            headers = ['手机号', '归属地', '运营商', '区号', '邮编', '状态', '查询时间']
            ws.append(headers)

            # 写入数据
            for result in self.results:
                if result['success']:
                    data = result['data']
                    row = [
                        result['phone'],
                        data.get('location', ''),
                        data.get('operator', ''),
                        data.get('area_code', ''),
                        data.get('zip_code', ''),
                        '成功',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                else:
                    row = [
                        result['phone'],
                        '', '', '', '',
                        f"失败: {result.get('error', '')}",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                ws.append(row)

            wb.save(filename)
        except ImportError:
            messagebox.showerror("错误", "请安装openpyxl库: pip install openpyxl")


def main():
    root = tk.Tk()
    app = PhoneQueryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
