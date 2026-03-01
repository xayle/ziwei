# CSP (Content Security Policy) 安全策略说明

## 问题描述

之前的CSP策略设置为 `script-src 'self'`，这阻止了所有内联JavaScript执行，导致 verify.html 的功能无法正常运行。

### 错误信息示例
```
Executing inline script violates the following Content Security Policy directive 
'script-src 'self''. Either the 'unsafe-inline' keyword, a hash, or a nonce 
is required to enable inline execution.
```

---

## 当前解决方案

### ✅ 快速修复（已应用）

**修改位置**: `run.py` - `add_security_headers()` 函数

**修改前**:
```python
"script-src 'self'; "
```

**修改后**:
```python
"script-src 'self' 'unsafe-inline'; "
```

### 当前完整CSP配置

```
Content-Security-Policy: 
  default-src 'self'; 
  connect-src 'self'; 
  style-src 'self' 'unsafe-inline'; 
  script-src 'self' 'unsafe-inline'; 
  img-src 'self' data:; 
  font-src 'self'; 
  object-src 'none'; 
  frame-ancestors 'none';
```

**注意**: `connect-src` 使用 `'self'` 即可，无需单独指定路径（如 `/api/`），因为 `'self'` 已包含同源的所有路径。

---

## 安全影响评估

### ⚠️ 使用 'unsafe-inline' 的风险

1. **XSS攻击风险**: 如果有XSS漏洞，攻击者可以注入并执行恶意脚本
2. **降低CSP保护等级**: CSP的主要目的之一就是阻止内联脚本

### ✅ 风险缓解措施

1. **受控环境**: 仅用于内部工具，非公开互联网应用
2. **输入验证**: 所有用户输入都经过严格验证（见 `schemas.py`）
3. **转义输出**: 动态内容使用 `esc()` 函数转义
4. **无用户生成内容**: 不允许用户上传或提交HTML/JavaScript
5. **其他CSP规则**: 仍然启用了其他安全规则（frame-ancestors, object-src等）

---

## 🔒 更安全的替代方案（可选升级）

### 方案1: 使用 Nonce (推荐)

**工作原理**: 为每个请求生成唯一的随机字符串，只允许带有匹配nonce的脚本执行。

**实现步骤**:

1. **修改 run.py**:
```python
import secrets
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/static/verify.html")
async def serve_verify_html(request: Request):
    nonce = secrets.token_urlsafe(16)
    response = templates.TemplateResponse(
        "verify.html", 
        {"request": request, "nonce": nonce}
    )
    response.headers["Content-Security-Policy"] = (
        f"script-src 'self' 'nonce-{nonce}'; "
        # ... 其他策略
    )
    return response
```

2. **修改 verify.html**:
```html
<script nonce="{{ nonce }}">
  // 所有JavaScript代码
</script>
```

**优点**: ✅ 仍然阻止XSS注入脚本  
**缺点**: ❌ 需要将 verify.html 转换为模板

---

### 方案2: 使用 SHA-256 Hash

**工作原理**: 计算内联脚本的SHA-256哈希值，只允许匹配哈希的脚本执行。

**实现步骤**:

1. **计算脚本哈希**:
```bash
# Linux/Mac
cat verify.html | grep -Pzo '(?s)<script>\K.*?(?=</script>)' | openssl dgst -sha256 -binary | openssl base64

# PowerShell
$script = (Get-Content verify.html -Raw) -replace '(?s).*<script>(.*?)</script>.*', '$1'
$hash = [Convert]::ToBase64String([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($script)))
Write-Host "sha256-$hash"
```

2. **添加到CSP**:
```python
"script-src 'self' 'sha256-<计算出的hash>';"
```

**优点**: ✅ 静态配置，不需要模板  
**缺点**: ❌ 每次修改脚本都需要重新计算hash

---

### 方案3: 外部JavaScript文件（最安全，推荐生产）

**工作原理**: 将所有内联脚本提取到外部 `.js` 文件。

**实现步骤**:

1. **创建 static/verify.js**:
   - 将 verify.html 中 `<script>` 标签内的所有代码移到此文件
   
2. **修改 verify.html**:
```html
<!-- 删除内联 <script> -->
<script src="/static/verify.js"></script>
```

3. **保持严格CSP**:
```python
"script-src 'self';"  # 不需要 'unsafe-inline'
```

**优点**:  
✅ 最安全的方案  
✅ 符合CSP最佳实践  
✅ 脚本可以被浏览器缓存  
✅ 代码组织更清晰  

**缺点**:  
❌ 需要重构 verify.html（工作量中等）  
❌ 增加一个HTTP请求（可通过缓存优化）  

---

## 📊 安全等级对比

| 方案 | 安全等级 | 实现难度 | 适用场景 |
|------|---------|---------|---------|
| 'unsafe-inline' (当前) | ⭐⭐ | 简单 | 内部工具、开发环境 |
| SHA-256 Hash | ⭐⭐⭐ | 中等 | 静态内容、不常修改 |
| Nonce | ⭐⭐⭐⭐ | 中等 | 动态内容、需要模板 |
| 外部JS文件 (推荐) | ⭐⭐⭐⭐⭐ | 中等 | 生产环境、公开服务 |

---

## 🎯 建议

### 当前环境（内部工具）
✅ **保持当前配置** - 'unsafe-inline' 可以接受，因为：
- 受控访问环境
- 无用户生成内容
- 有其他安全措施

### 生产部署
🔒 **升级到方案3** - 外部JS文件：
1. 提取 verify.html 的 JavaScript 到 `static/verify.js`
2. 移除 CSP 中的 'unsafe-inline'
3. 添加脚本版本号以支持缓存更新: `verify.js?v=2`

---

## 🛠️ 实施外部JS方案的步骤（可选）

如果将来要升级到最安全方案：

### 步骤1: 提取JavaScript
```bash
# 将 verify.html 的 <script> 内容提取到新文件
# 手动或使用脚本自动提取
```

### 步骤2: 创建 static/verify.js
```javascript
// verify.js
(function() {
  'use strict';
  
  // 所有原来在 <script> 标签内的代码
  // ...
})();
```

### 步骤3: 修改 verify.html
```html
<!-- 删除 <script>...</script> -->
<!-- 添加外部引用 -->
<script src="/static/verify.js?v=20260226"></script>
</body>
</html>
```

### 步骤4: 更新 CSP
```python
# run.py
"script-src 'self';"  # 移除 'unsafe-inline'
```

### 步骤5: 测试
- 清除浏览器缓存
- 验证所有功能正常
- 检查控制台无CSP错误

---

## 📚 参考资源

- [MDN - Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP - Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Google - CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [CSP Hash Calculator](https://report-uri.com/home/hash)

---

## 🔧 常见CSP错误修复

### connect-src 无效源错误

**错误信息**:
```
The source list for the Content Security Policy directive 'connect-src' 
contains an invalid source: '/api/'. It will be ignored.
```

**原因**:  
CSP的 `connect-src` 指令不接受相对路径作为源。`/api/` 不是有效的CSP源格式。

**错误配置**:
```python
"connect-src 'self' /api/;"
```

**正确配置**:
```python
"connect-src 'self';"
```

**说明**:  
`'self'` 关键字已经包含了同源的所有路径（包括 `/api/`, `/static/` 等），无需单独指定。

**有效的CSP源格式**:
- `'self'` - 同源（包含所有路径）
- `'none'` - 不允许任何源
- `https://api.example.com` - 完整URL
- `*.example.com` - 通配符域名
- `'unsafe-inline'` - 允许内联（仅script-src/style-src）
- `'unsafe-eval'` - 允许eval（不推荐）

**修复时间**: 2026-02-26

---

## ✅ 检查清单

当前部署状态：

- [x] CSP基础配置已启用
- [x] 内联脚本可正常执行
- [x] style-src 允许内联样式
- [x] connect-src 无效源已修复 ✅
- [x] 防止点击劫持 (X-Frame-Options)
- [x] 防止内容嗅探 (X-Content-Type-Options)
- [ ] 外部JavaScript文件（未来升级）
- [ ] 使用nonce或hash（未来升级）

---

**上次更新**: 2026-02-26  
**当前版本**: v5.3.1 with CSP fixes (script-src 'unsafe-inline' + connect-src 'self')
