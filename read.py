import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests
import re
import warnings
import os
import platform
 
warnings.filterwarnings("ignore")
current_files = []
current_file_index = -1
IS_ANDROID = platform.system() == "Linux" and "aarch64" in platform.machine()
 
def set_syntax_highlight(text_widget):
    text_widget.tag_config("tag_html", foreground="#4ec9b0")
    text_widget.tag_config("tag_attr", foreground="#9cdcfe")
    text_widget.tag_config("tag_str", foreground="#ce9178")
    text_widget.tag_config("tag_keyword", foreground="#569cd6")
    text_widget.tag_config("tag_func", foreground="#dcdcaa")
    text_widget.tag_config("tag_comment", foreground="#6a9955")
    text_widget.tag_config("tag_type", foreground="#4ec9b0")
    content = text_widget.get(1.0, tk.END)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, content)
    text_widget.tag_remove("all", 1.0, tk.END)
    lines = content.splitlines()
    pos = 1.0
    for line in lines:
        if "//" in line:
            idx = line.find("//")
            text_widget.tag_add("tag_comment", f"{pos}+{idx}c", f"{pos} lineend")
        if "/*" in line and "*/" in line:
            s = line.find("/*")
            e = line.find("*/", s) + 2
            text_widget.tag_add("tag_comment", f"{pos}+{s}c", f"{pos}+{e}c")
        if "#" in line and not line.strip().startswith("#"):
            idx = line.find("#")
            text_widget.tag_add("tag_comment", f"{pos}+{idx}c", f"{pos} lineend")
        keywords = ["if","else","for","while","def","class","import","from","return","public","private","static","void","int","String","fun","val","var","let","const","include","main","package","extends","implements","new"]
        for kw in keywords:
            for match in re.finditer(rf"\b{kw}\b", line):
                text_widget.tag_add("tag_keyword", f"{pos}+{match.start()}c", f"{pos}+{match.end()}c")
        types = ["int","float","double","char","bool","String","Long","Byte","Unit","object","boolean","short","long"]
        for tp in types:
            for match in re.finditer(rf"\b{tp}\b", line):
                text_widget.tag_add("tag_type", f"{pos}+{match.start()}c", f"{pos}+{match.end()}c")
        if '"' in line or "'" in line:
            quote = None
            for i,c in enumerate(line):
                if c in "\"'" and quote is None:
                    quote = c
                    q_start = i
                elif c == quote:
                    text_widget.tag_add("tag_str", f"{pos}+{q_start}c", f"{pos}+{i+1}c")
                    quote = None
        if "<" in line:
            for tag in ["html","head","body","meta","title","button","script","div","link","style","img"]:
                for s in [f"<{tag}",f"</{tag}>"]:
                    idx = line.find(s)
                    while idx != -1:
                        text_widget.tag_add("tag_html", f"{pos}+{idx}c", f"{pos}+{idx+len(s)}c")
                        idx = line.find(s, idx+1)
        pos += 1
 
def get_source():
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("提示", "请输入网址！")
        return
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        status_label.config(text="动态渲染加载中...", fg="#0099ff")
        root.update()
        global current_files
        current_files.clear()
        file_listbox.delete(0, tk.END)
        headers = {"User-Agent":"Mozilla/5.0 (Android) Chrome/120.0.0.0 Safari/537.36"}
        if IS_ANDROID:
            res = requests.get(url, timeout=20, headers=headers, verify=False)
            html = res.text
        else:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opt = Options()
            opt.add_argument("--headless=new")
            opt.add_argument("--no-sandbox")
            opt.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=opt)
            driver.get(url)
            html = driver.page_source
            driver.quit()
        current_files.append({"name":"index.html","content":html})
        js_links = re.findall(r'src=["\']([^"\']+\.js[^"\']*)', html)
        css_links = re.findall(r'href=["\']([^"\']+\.css[^"\']*)', html)
        for src in js_links:
            full_url = src if src.startswith("http") else url.rstrip("/")+"/"+src.lstrip("/")
            try:
                r = requests.get(full_url, timeout=10, headers=headers, verify=False)
                name = os.path.basename(full_url.split("?")[0])
                current_files.append({"name":name,"content":r.text})
            except:
                pass
        for href in css_links:
            full_url = href if href.startswith("http") else url.rstrip("/")+"/"+href.lstrip("/")
            try:
                r = requests.get(full_url, timeout=10, headers=headers, verify=False)
                name = os.path.basename(full_url.split("?")[0])
                current_files.append({"name":name,"content":r.text})
            except:
                pass
        for f in current_files:
            file_listbox.insert(tk.END, f["name"])
        show_file(0)
        status_label.config(text=f"抓取成功 | 文件数:{len(current_files)}", fg="#00cc66")
    except Exception as e:
        status_label.config(text="获取失败", fg="#ff4444")
        messagebox.showerror("错误", str(e))
 
def show_file(index):
    global current_file_index
    if index < 0 or index >= len(current_files):
        return
    current_file_index = index
    f = current_files[index]
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f["content"])
    set_syntax_highlight(text_area)
    text_area.config(state=tk.DISABLED)
 
def on_file_select(evt):
    sel = file_listbox.curselection()
    if sel:
        show_file(sel[0])
 
def save_source():
    if current_file_index < 0:
        messagebox.showwarning("提示", "暂无内容！")
        return
    f = current_files[current_file_index]
    path = filedialog.asksaveasfilename(defaultextension=".html",filetypes=[("HTML","*.html"),("JS","*.js"),("Python","*.py"),("Java","*.java"),("C","*.c"),("所有文件","*.*")])
    if path:
        with open(path, "w", encoding="utf-8") as ff:
            ff.write(f["content"])
        messagebox.showinfo("成功", "保存完成")
 
def copy_all():
    root.clipboard_clear()
    root.clipboard_append(text_area.get(1.0, tk.END))
    messagebox.showinfo("提示", "已复制全部")
 
def clear_text():
    global current_files, current_file_index
    current_files.clear()
    current_file_index = -1
    file_listbox.delete(0, tk.END)
    text_area.config(state=tk.NORMAL)
    text_area.delete(1.0, tk.END)
    text_area.config(state=tk.DISABLED)
    status_label.config(text="就绪", fg="#888888")
 
root = tk.Tk()
root.title("读取网站源代码")
root.geometry("1500x900")
root.minsize(900, 600)
root.configure(bg="#121212")
 
main_frame = tk.Frame(root, bg="#121212")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
 
left_frame = tk.Frame(main_frame, bg="#121212", width=220)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
left_frame.pack_propagate(False)
tk.Label(left_frame, text="文件列表：", bg="#121212", fg="#fff", font=("sans-serif",12,"bold")).pack()
file_listbox = tk.Listbox(left_frame, bg="#1e1e1e", fg="#eee", selectbackground="#2563eb", font=("sans-serif",10))
file_listbox.pack(fill=tk.BOTH, expand=True)
file_listbox.bind("<<ListboxSelect>>", on_file_select)
 
right_frame = tk.Frame(main_frame, bg="#121212")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
 
title_frame = tk.Frame(right_frame, bg="#1e1e1e", height=60)
title_frame.pack(fill=tk.X)
tk.Label(title_frame, text="读取网站源代码", bg="#1e1e1e", fg="#fff", font=("sans-serif",16,"bold")).pack(pady=12)
 
url_frame = tk.Frame(right_frame, bg="#121212")
url_frame.pack(fill=tk.X, pady=15)
tk.Label(url_frame, text="网址：", bg="#121212", fg="#ccc", font=("sans-serif",12)).pack(side=tk.LEFT)
entry_url = tk.Entry(url_frame, font=("sans-serif",12), bg="#2a2a2a", fg="#fff", insertbackground="#fff", relief=tk.FLAT)
entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
 
btn_style = {"relief":tk.FLAT, "font":("sans-serif",11), "padx":12, "pady":6}
tk.Button(url_frame, text="获取", command=get_source, bg="#2563eb", fg="white",**btn_style).pack(side=tk.LEFT,padx=4)
tk.Button(url_frame, text="保存", command=save_source, bg="#059669", fg="white",**btn_style).pack(side=tk.LEFT,padx=4)
tk.Button(url_frame, text="复制", command=copy_all, bg="#d97706", fg="white",**btn_style).pack(side=tk.LEFT,padx=4)
tk.Button(url_frame, text="清空", command=clear_text, bg="#dc2626", fg="white",**btn_style).pack(side=tk.LEFT)
 
status_label = tk.Label(right_frame, text="就绪", bg="#121212", fg="#888888", font=("sans-serif",10))
status_label.pack(anchor="w")
 
text_area = scrolledtext.ScrolledText(right_frame, font=("monospace",10), bg="#1e1e1e", fg="#e0e0e0", insertbackground="#fff", selectbackground="#3a3a3a", relief=tk.FLAT, state=tk.DISABLED)
text_area.pack(fill=tk.BOTH, expand=True, pady=10)
 
root.mainloop()
