# 🔄 清除缓存查看新UI功能

## 问题：UI上看不到新增的按钮？

这是因为**浏览器缓存**或**Service Worker缓存**了旧版本的页面。

---

## ✅ 解决方法（按顺序尝试）

### 方法1：硬刷新（最快，推荐）⚡

1. 打开页面：http://127.0.0.1:8000/static/verify.html
2. 按键盘快捷键：
   - **Windows**: `Ctrl + Shift + R`
   - **Mac**: `Cmd + Shift + R`
3. 看到页面右上角有四个新按钮即成功

---

### 方法2：清除Service Worker缓存 🔧

1. 打开页面后，按 `F12` 打开开发者工具
2. 点击顶部的 **Application** 标签（或**应用程序**）
3. 左侧找到 **Service Workers**
4. 找到 `http://127.0.0.1:8000` 的Service Worker
5. 点击 **Unregister**（取消注册）按钮
6. 关闭开发者工具
7. 按 `Ctrl + Shift + R` 硬刷新页面

---

### 方法3：完全清除浏览器缓存 🗑️

#### Chrome / Edge
1. 按 `Ctrl + Shift + Delete`
2. 时间范围选择：**所有时间**
3. 勾选：
   - ✅ Cookie 和其他网站数据
   - ✅ 缓存的图片和文件
4. 点击 **清除数据**
5. 重新访问页面

#### Firefox
1. 按 `Ctrl + Shift + Delete`
2. 时间范围选择：**全部**
3. 勾选：
   - ✅ Cookie
   - ✅ 缓存
4. 点击 **确定**
5. 重新访问页面

---

### 方法4：无痕/隐私模式测试 🕵️

1. 打开浏览器的无痕窗口：
   - Chrome: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`
2. 访问：http://127.0.0.1:8000/static/verify.html
3. 应该能看到新按钮

---

## ✨ 新功能按钮位置

新增的**四个按钮**位于页面**右上角**，在"示例"和"cURL"按钮右侧：

```
┌─────────────────────────────────────────────┐
│  八字命理验证 · BaZi Verify                   │
├─────────────────────────────────────────────┤
│  [示例] [cURL] ⭐收藏 ⚖️对比 📥导出 🌙深色    │
│                                             │
│  [输入区域...]                               │
└─────────────────────────────────────────────┘
```

---

## 🎯 新增功能说明

### 1. ⭐ 收藏功能
- **有结果时点击**：保存当前八字到本地收藏夹
- **无结果时点击**：查看/加载收藏列表
- 数据保存在浏览器localStorage中

### 2. ⚖️ 对比功能
- 点击一次：保存当前八字为对比基准（按钮变黄）
- 排另一个八字：自动对比并显示差异
- 再次点击：退出对比模式

### 3. 📥 导出功能
- 选项1：下载JSON文件
- 选项2：复制到剪贴板
- 选项3：打印/保存为PDF

### 4. 🌙 深色模式
- 切换深色/浅色主题
- 自动保存偏好设置
- 支持跨会话保存

---

## 🔍 验证是否成功

打开浏览器**开发者工具**（F12），在 **Console** 标签执行：

```javascript
console.log('按钮检查:');
console.log('收藏:', document.getElementById('btn-favorite'));
console.log('对比:', document.getElementById('btn-compare'));
console.log('导出:', document.getElementById('btn-export'));
console.log('深色:', document.getElementById('btn-dark-toggle'));
```

如果输出的不是 `null`，说明按钮已正确加载。

---

## 🐛 仍然看不到？

### 检查1：服务器是否运行
```powershell
curl http://127.0.0.1:8000/health
```
应该返回 `{"status":"healthy"}`

### 检查2：HTML是否包含按钮
```powershell
curl http://127.0.0.1:8000/static/verify.html | Select-String "btn-favorite"
```
应该有匹配结果

### 检查3：IE浏览器兼容性
如果使用IE浏览器（不推荐），请换用：
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

---

## 📞 技术支持

如果以上方法都无效，请提供以下信息：

1. 浏览器名称和版本
2. 操作系统
3. F12开发者工具中的错误信息（Console标签）
4. 截图

---

## ⚡ 快速命令（PowerShell）

重启服务器并清除所有缓存：

```powershell
# 停止服务器
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { taskkill /PID $_.OwningProcess /F }

# 等待2秒
Start-Sleep -Seconds 2

# 启动服务器
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd d:\Users\Administrator\Desktop\c1; .\.venv\Scripts\python.exe -m uvicorn run:app --host 127.0.0.1 --port 8000"
```

然后在浏览器中按 `Ctrl + Shift + R` 硬刷新。

---

**祝您顺利看到新功能！** 🎉
