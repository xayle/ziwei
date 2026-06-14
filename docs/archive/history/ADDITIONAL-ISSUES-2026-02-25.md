# 🔍 追加问题清单 (2026-02-25 继续审查)

> 基于方案v5.2和代码审查的深入分析，继续发现更多风险点

---

## 系统架构层面

### 问题 #14: **缓存策略完全缺失**

**现状**:
```
- 方案说"不做缓存"，但没有考虑：
  □ 同一時间有100个朋友查同一个日期（2000年1月1日）
  □ sxtwl每次都要重新计算，浪费CPU
  □ 如果添加sxtwl库升级（含bug），所有在途查询用旧版本还是新版本
```

**风险**:
- 高并发时服务器CPU飙升
- 无法支撑"分享给朋友后同时访问"的场景
- 无法快速响应（计算>500ms的日期时容易超时）

**建议**:
```
至少加L1缓存（内存）：
  - 缓存对象：(year, month, day) + (sxtwl_version) → pillars
  - 缓存TTL: 24小时（足够分享链接的生命周期）
  - 缓存大小：最多10000条记录（~1000年范围内的常用日期）
  
不需要Redis那么复杂，Python dict就够了

风险控制：
  □ sxtwl升级时自动清空缓存
  □ 记录缓存命中率（性能监控）
  □ 如果发现缓存有bug，能快速禁用
```

---

### 问题 #15: **并发和竞态条件未考虑**

**现状**:
```python
# 假设发展路径：越来越多朋友分享链接
# 某时刻：
#   - 100个request同时进来（比如分享链接被转发到群里）
#   - 都在计算2000年1月1日
#   - 同时访问constants表（是否有竞态）
#   - 同时调用sxtwl库（库本身线程安全吗）

# 缺失测试：
□ 没有压力测试（多并发时会不会crash）
□ 没有验证sxtwl库是否线程安全
□ ganzhi/relations的字典操作是否线程安全
```

**风险**:
- 高并发时出现间歇性bug（很难复现）
- 内存泄漏（某个请求异常导致资源未释放）
- sxtwl库在高并发时可能返回错误结果

**建议**:
```
□ 用locust或JMeter做压力测试：100并发持续1分钟
□ 验证sxtwl库文档中的线程安全性说明
□ 对constants表和计算过程加锁（如果需要）
□ 监控内存使用和异常率
□ 设置request queue （如果并发超过阈值，返回"服务繁忙"而不是卡顿）
```

---

### 问题 #16: **库版本管理混乱**

**现状**:
```
requirements.txt：
  - fastapi  （无版本号）
  - sxtwl    （无版本号）  ← 关键！这是计算引擎
  - cnlunar  （无版本号）
  
问题：
□ 某天pip install自动升级sxtwl到新版本
□ 新版本有bug，所有在线结果计算错误
□ 无法追溯某个用户的查询用的是哪个sxtwl版本
□ 分享链接用老版本打开，再查一遍用新版本，结果不同（用户会困惑）
```

**风险**:
- 无法复现用户反馈的bug（不知道他用的哪个sxtwl版本）
- 无法rollback到上个稳定版本（想改都改不了）
- sxtwl如果有breaking change，整个系统崩溃

**建议**:
```
requirements-lock.txt (新增):
  fastapi==0.104.1
  sxtwl==2023.01.28
  cnlunar==0.2.4
  jinja2==3.1.2
  pytest==7.4.0
  
requirements.txt (仅用于初始开发):
  fastapi>=0.100
  sxtwl>=2020
  cnlunar>=0.2
  
部署流程：
  1. 开发用requirements.txt（宽松）
  2. 测试通过后锁定到-lock版本
  3. 上线用-lock版本（严格）
  4. 如果发现bug，更新-lock版本后重新测试
  5. 记录每个版本的上线时间和用户数
  
sxtwl升级流程：
  □ 先创建新环境测试
  □ 运行run_cases.py所有样例，确认结果一致
  □ 如果有差异，标记为breaking change，需要回填口径
  □ 同时升级rule_version
```

---

### 问题 #17: **分享链接的隐私和持久化矛盾**

**现状**:
```
页脚说："不主动存储任何输入数据"
但实际是：
□ 分享链接 = 用户生日信息存储在URL里
□ URL被浏览器保存在历史记录
□ URL被代理/CDN保存在日志里
□ URL在用户点击分享时可能被第三方截获

问题：
□ 说"不存储"只是文字游戏，实际隐私保护为0
□ 用户理解"不存储"是指"后端没有存"
□ 但URL本身就是分布式存储，根本删不掉
```

**现实后果**:
- 用户打开分享链接后，那个4柱就被永久记录在：
  - 浏览器历史
  - ISP日志
  - 反向代理日志
  - CDN日志
  - 搜索引擎缓存（如果被爬虫发现）

**建议**:
```
选择一个方向（二选一）：

方案A：真正的隐私（推荐）
  - 不用URL参数存数据
  - 改成：POST计算 → 返回JSON → 前端生成HTML
  - 分享不再是链接，改成"生成报告PDF"或"分享到clipboard"
  - 代价：失去"一键分享"的便利性，提高了隐私

方案B：接受URL存储
  - 彻底改页脚说明：
    "为了分树享链接功能，生日数据会被保存在URL中
     请勿向陌生人分享此链接
     分享对象应该是信任的朋友"
  - 添加"删除历史记录教程"
  - 提示用户"打开链接后想想是否要删除浏览器历史"

目前方案v5.2是两方面都没做好，很危险
```

---

### 问题 #18: **GDPR和用户数据权利**

**现状**:
```
EU GDPR要求：
□ 用户有权查看个人数据
□ 用户有权删除个人数据
□ 用户有权获得数据导出

方案v5.2的问题：
□ 没有"我的分享"列表（用户无法查看自己生成过的结果）
□ 没有"删除结果"功能（分享链接永久存在）
□ 没有"数据导出"功能

这在EU国家可能违法
```

**建议**:
```
如果要合规，需要添加：
1. 用户账户系统
   - 虽然说"不做用户系统"，但GDPR强制要求
   - 可以简化：邮箱注册 + token (不需要密码)
   
2. "我的分享"页面
   - 显示用户生成过的所有查询
   - 时间、日期、关键信息
   
3. 删除功能
   - POST /api/v1/results/{id}/delete
   - 标记为"已删除"（保留审计日志，但对外隐藏）
   
4. 数据导出
   - GET /api/v1/export (下载JSON或CSV)
   
或者，改下页脚说明：
  "本站未对EU/China等地区提供服务，无法保证GDPR合规"
  （这样可以规避法律风险，但会失去那些用户）
```

---

## 数据和计算层面

### 问题 #19: **闰月处理的双库差异未测试**

**现状**:
```
方案说：
□ 用"节"切月（立春/惊蛰等）
□ 闰月会有，但没有特殊处理

风险：
□ sxtwl和cnlunar对闰月的理解可能不同
□ 如果在闰月7月期间计算，两库可能给出不同的月柱（一个是闰7，一个是8）
□ 用户问"为什么我农历闰7月生，算出来是8月"→ 无法解释

缺失测试：
□ run_cases.py没有闰月样例
□ 没有验证sxtwl的闰月输出
□ 没有验证cnlunar的闰月输出
```

**建议**:
```
run_cases.py增加10个闰月样例（最近20年都有）：
  - 2023年闰2月（最近的）：在闰月期间查询
  - 2020年闰4月：在端口查询
  - 等等
  
验证：
  □ sxtwl算出闰月时，month_pillar是什么
  □ cnlunar算出闰月时，month_pillar是什么
  □ 如果不同，如何说明给用户听
  □ rule_version中添加 jieqi_lunar_month: v1.0（表示闰月处理版本）
```

---

### 问题 #20: **经度精度的隐藏假设**

**现状**:
```
真太阳时计算用公式：
  真太阳时偏移 = (经度 - 120) × 4 + E

假设：
□ 经度精度到0.01度（约1km）
□ 假设用户输入的"116.41"的精度
□ 但城市下拉里怎么回事？"北京=116.41"是市中心还是市平均？

问题：
□ 用户在北京郊区（116.8度），用116.41会算出差5分钟的时差
□ 这5分钟可能导致时柱错误（边界判定在±15分钟）
□ 用户根本不知道"116.41"到底是什么地方

问案例：
  用户说"我生在北京通州，你推荐我用116.41经度"
  结果时柱算错了，用户骂"你算的垃圾"
```

**建议**:
```
在输入页明确标注：
  "城市经度为城市中心坐标
   如您生活在郊区，建议手输经度以获得更准确的真太阳时
   
   经度精度说明：
   - 精确到0.1度：误差 ±6分钟
   - 精确到0.01度：误差 ±36秒（推荐）
   - 精确到0.001度：误差 ±3.6秒（可选，若有GPS数据）"

并在结果页标注：
  "当前经度：北京市中心(116.41°E)
   实际经度误差可能导致时差±{calculated_error}分钟
   若时柱边界，建议参考两套结果"
```

---

### 问题 #21: **错误结果的自动检测缺失**

**现状**:
```
假设sxtwl库有bug：
□ 某个特殊日期（比如闰月的最后一天）算出了错误的日柱
□ 代码没有异常（sxtwl返回了结果，只是结果错了）
□ 用户查询那个日期，得到错误四柱
□ 用户不知道这是bug，当作真实数据相信

这种"无声的bug"最危险，因为：
□ 没有error log告警
□ 用户可能传播这个错误结果给朋友
□ 别人相信了这个错误四柱

缺失防护：
□ 没有"结果合理性检查"
  比如：日柱天干应该与五虎遁推算的一致，否则alert
□ 没有"库对比"时的异常警告
  比如：sxtwl和cnlunar差异>3天，应该标记为high-risk而不是normal
```

**建议**:
```
在verify.py中添加"健康检查"：

1. 自洽性检查（sxtwl内部）
   if day_pillar_from_sxtwl != day_pillar_from_五虎遁_backward:
     alert("sxtwl internal inconsistency detected")
     
2. 库对比检查
   if sxtwl_day_pillar != cnlunar_day_pillar:
     if diff_days > 3:
       level = L3, reasons += "library_diff_critical"
     
3. 边界sanity check
   if jieqi_time == None and status==near_jieqi_boundary:
     alert("cannot determine jieqi_time but marked as boundary")
     
4. 告警输出
   如果任何sanity check失败，返回：
   {
     error: "data_quality_alert",
     severity: "critical",  # 用户应该看到这个
     details: "计算过程中发现数据异常，建议咨询专家"
   }
```

---

## 前端和用户体验层面

### 问题 #22: **XSS漏洞风险（Jinja2动态渲染）**

**现状**:
```
result.html用Jinja2渲染：
  <div>{{ validation.reasons }}</div>
  
如果reasons里有用户输入（虽然没有，但假设有）：
  reasons = ["solar_time_disabled", "<img src=x onerror=alert('xss')>"]
  
Jinja2默认自动转义，但如果设置错误，就会XSS

还有更隐蔽的：
□ 五行条形图数据：如果somehow包含HTML，会被执行
□ 神煞列表、地支关系：如果somehow包含<script>会被执行
```

**建议**:
```
代码规范：
1. 所有Jinja2模板顶部加：
   {# jinja2: autoescape = true #}
   
2. 任何来自后端的动态内容，都用|e过滤：
   <div>{{ validation.reasons|e }}</div>
   
3. JSON嵌入到前端时，用|tojson和|safe组合：
   const data = {{ result_data|tojson|safe }};
   （这样JSON被安全转义，JS能正确解析）
   
4. 禁止使用|safe除非确认数据来源安全
   
5. 前端形成的HTML片段（比如五行条形图），不能直接innerHTML
   改成textContent或create元素

测试：
□ 在input里注入'<img src=x onerror=alert(1)>看会不会执行
□ 检查result.html源码，看每个动态字段是否转义了
```

---

### 问题 #23: **移动端适配完全没有具体方案**

**现状**:
```
说"移动端优先"，但：
□ 没有具体的断点设置
□ 没有说明长列表怎么展示（30-50个城市，在5英寸屏上怎么scroll）
□ 没有说明表单怎么排列（日期/时间/性别/城市都竖排吗）
□ 没有说明结果页怎么分屏（四柱卡片、五行图、地支关系、解读等都在一列吗）
□ 没有说明输入时间控制器（HTML5 input type='time'在iOS和Android上表现不同）

测试缺失：
□ 没有在iPhone SE(375px)上测
□ 没有在iPad(768px)上测  
□ 没有在Android大屏手机(720px)上测

结果：上线后会发现某个屏幕尺寸上按钮会挡字，输入框超出屏幕等
```

**建议**:
```
立即创建responsive mockup:

断点定义：
  xs: <= 375px  (iPhone SE/5s)
  sm: 376-500px (iPhone 12/13)
  md: 501-768px (平板竖屏)
  lg: >= 769px  (平板横屏/桌面)

输入页布局：
  xs: 
    [日期选择器 - 100%宽度]
    [时间输入（上行） | 性别选择（下行）- 各50%]
    [城市下拉 - 100%]
    [经度输入（折叠） - 100%]
    [真太阳时开关 - 100%]
    [计算按钮 - 100%]
    
  md+:
    [日期] [时间] [性别]  （一行）
    [城市] [经度] [开关]  （一行）
    [计算按钮 - 50%宽]}

结果页布局：
  xs:
    [警示条（黄条/红条）- 100%]
    [四柱卡片 - 100%，竖排4张]
    [五行条形图 - 100%，竖向]
    [折叠："更多信息"]
      [地支关系] [天干关系] [神煞] [长生] [空亡]
    [解读区 - 100%]
    [版本信息 - 字号偏小]
    
  md+:
    [警示条]  
    [四柱卡片 - 2×2网格]
    [五行条形图 - 50%宽度]
    [侧栏 - 50%宽度，fixed position，包含：版本信息、数据来源]
    [下方：地支/天干/神煞/长生/空亡 - 水平tab或carousel]
    [解读区 - 100%]

必测案例（每改一次都要测）：
□ iPhone 6 (375×667) - 竖屏
□ iPhone 12 (390×844) - 竖屏
□ iPad (768×1024) - 竖屏
□ iPad (1024×768) - 横屏
□ Android Galaxy S10 (360×800) - 竖屏
□ Android大屏 Pixel 7 Pro (512×949) - 竖屏
```

---

### 问题 #24: **时间输入体验差**

**现状**:
```
用HTML5 input type="time"：
□ iOS上是转盘式选择器（很原生）
□ Android上是数字输入框（用户容易输入错误）
□ 不同浏览器表现完全不同

问题：
□ 用户在小屏幕上很容易点错（误点小时/分钟）
□ 没有纠错提示（输入"25:70"后是否会自动修正）
□ 没有说明时间精度（精确到分钟，还是秒）
```

**建议**:
```
方案A：保持HTML5但补充纠错
  <input type="time" id="time-input" value="14:30" 
         pattern="([01]?[0-9]|2[0-3]):[0-5][0-9]"
         required>
  
  JS在blur时验证：
  if (hours > 23 || minutes > 59) {
    show_error("请输入有效时间（HH:MM）")
    input.value = ""  // 清空，让用户重新输入
  }

方案B：自定义选择器（更好的UX）
  两个竖向滚轮，上面是小时，下面是分钟
  （这样在移动端点错的概率就小得多）
  
推荐方案B，因为：
□ 移动端体验更好
□ 跨浏览器表现一致
□ 用户不容易误操作
```

---

## 文档和运营层面

### 问题 #25: **用户文档完全缺失**

**现状**:
```
用户看到结果后：
□ "L0是什么意思？" - 无文档
□ "为什么有两套四柱？" - 无文档
□ "推荐北京时间是什么意思？" - 无文档
□ "藏干为什么有3个干？" - 无文档
□ "这个推荐建议是准的吗？" - 无文档

只有：
√ 一个"免责声明"（法律语言，用户看不懂）
√ 页脚的"数据来源"（只有书名，没有解释）
```

**建议**:
```
添加这些页面/弹窗：

1. /learn/L_levels （学习：L级别是什么）
   - L0: 双库一致，结果可信
   - L1: 差异仅在时柱，谨慎参考
   - L2: 差异包含月柱，可靠性降低
   - L3: 差异包含日/年柱，建议重新确认生日信息
   - 附图：展示L1/L2/L3的diff examples

2. /learn/dual_library （学习：为什么有两个算法）
   - 解释sxtwl和cnlunar的区别
   - 用人话说"一个用天文计算，一个用官方数据表"
   - 如果不同，应该信谁（一般信sxtwl）

3. /learn/canggan （学习：什么是藏干）
   - 解释5个地支为什么藏3个干
   - 解释权重（0.6/0.2/0.2）是什么意思
   - 给examples

4. /learn/recommendations （学习：推荐是可信的吗）
   - 坦白说：推荐基于模板，不是个性化的
   - 仅供参考，不作为决策依据
   - 复杂情况应该咨询命理师

5. /faq （常见问题）
   - "为什么我在海外，时间怎么填"
   - "我农历闰月生，应该怎么算"
   - "两套结果不一样，哪个对"
   - "我觉得算的不对，怎么反馈"

这些文档可以用弹窗或tooltip实现，不需要额外页面
```

---

### 问题 #26: **bug反馈渠道缺失**

**现状**:
```
用户发现problem时：
□ 没有"反馈"按钮
□ 没有email地址可以联系
□ 没有说明底部谁维护这个网站
□ 甚至没有版权声明

用户可能：
□ 在社交媒体吐槽"某某网站垃圾"
□ 发布错误的四柱给朋友（因为以为算对了）
□ forever distrust这个工具
```

**建议**:
```
添加最小化反馈机制：

1. 结果页底部添加反馈链接：
   <footer>
     <p>如发现计算有误，请点击<a href="mailto:admin@xxx.com">反馈</a></p>
     <p>© 2026 BaZi Checker | 朋友共享版</p>
   </footer>

2. 反馈邮件包含的信息（自动添加）：
   - Timestamp
   - 输入日期和时间
   - 性别和城市
   - 操作系统和浏览器信息
   - 当前rule_version
   - 计算结果（让用户可以引用）

3. 添加一个webhook或日志收集器：
   当用户点"反馈"时，把上面的数据发到某个地方
   （可以是telegram bot，也可以是email）
```

---

### 问题 #27: **依赖文档缺失**

**现状**:
```
requirements.txt中没有注释：
  fastapi       ← 为什么要用这个
  uvicorn       ← 这是什么
  jinja2        ← 为什么不用Vue/React
  sxtwl         ← 这是什么库，从哪里来
  cnlunar       ← 什么时候用这个
  pytest        ← 怎么跑测试

问题：
□ 新的开发者看到会懵逼
□ 容易误删某个依赖（会导致项目崩溃）
□ 无法快速理解架构选型的理由
```

**建议**:
```
在requirements.txt同一目录创建 DEPENDENCIES.md：

# 依赖说明

## 生产依赖
- **fastapi** (v0.104+)
  用途：Web框架
  为什么选它：轻量、性能好、内置文档生成
  不用Django/Flask的原因：过重，对此项目来说

- **uvicorn** (v0.24+)
  用途：ASGI服务器（运行FastAPI）
  为什么选它：官方推荐，性能好，部署简单

- **jinja2** (v3.1+)
  用途：模板渲染（生成HTML结果页）
  为什么不用Vue/React：
    ✓ 不需要打包工具
    ✓ 后端直接生成HTML（部署简单）
    ✓ 用户直接GET/POST（无API复杂度）
    ✗ 代价是前端交互有限（但本项目不需要复杂交互）

- **sxtwl** (v2023.01.28+)
  用途：主引擎，计算干支纳音等
  来源：许剑伟《寿星天文历》
  何时用：优先使用，如果安装失败则降级到cnlunar

- **cnlunar** (v0.2.4+)
  用途：校验引擎/备选引擎
  来源：基于《中国天文年历》
  何时用：(a) sxtwl不可用时作为主引擎，(b) 双库校验时作为对照

## 开发依赖
- **pytest** (v7.4+)
  用途：运行test_core.py
  怎么用：pytest test_core.py -v

<!-- 更多依赖说明 -->

## 更新策略
- 生产环境用 requirements-lock.txt（精确版本）
- 开发环境可用 requirements.txt（允许小版本升级）
- 任何breaking change都需要回测run_cases.py
```

---

### 问题 #28: **部署文档缺失**

**现状**:
```
七、部署方式说：
  pip install -r requirements.txt
  uvicorn run:app --host 0.0.0.0 --port 8000

问题：
□ 怎么配置HTTPS（生产环境必需，否则会被HTTP劫持）
□ 怎么部署到不同平台（Docker/AWS/阿里云/自建服务器）
□ 怎么配置日志（日志输出到文件还是stdout）
□ 怎么监控服务健康（心跳检查、自动重启等）
□ 怎么备份分享数据（如果要持久化的话）
□ 怎么处理依赖升级（临时维护窗口）
```

**建议**:
```
创建 DEPLOYMENT.md：

# 部署指南

## 前置准备
- 服务器OS：Linux (推荐Ubuntu 20.04+)
- Python版本：3.9+ (官方支持 3.9, 3.10, 3.11)
- 可用硬盘空间：>500MB (代码+venv+日志)
- 内存：>=1GB (sxtwl计算偶尔会spike)

## 本地开发环境
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py  # 启动在 http://localhost:8000
```

## 生产部署（Linux服务器）

### 1. 环境安装
```bash
sudo apt-get install python3.10 python3.10-venv python3-pip
cd /opt/bazi-app
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements-lock.txt
```

### 2. 配置反向代理（Nginx）
```nginx
server {
    listen 443 ssl http2;
    server_name bazi.example.com;
    
    # 申请SSL证书（Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/bazi.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bazi.example.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Systemd服务管理
```ini
# /etc/systemd/system/bazi.service
[Unit]
Description=BaZi Calculator
After=network.target

[Service]
Type=notify
User=bazi
WorkingDirectory=/opt/bazi-app
ExecStart=/opt/bazi-app/venv/bin/uvicorn run:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. 启动服务
```bash
sudo systemctl enable bazi
sudo systemctl start bazi
sudo systemctl status bazi
```

### 5. 监控和告警
```bash
# 检查服务是否健康
curl https://bazi.example.com/health
# 如果返回 {"status": "ok"}，表示正常

# 监控内存（可选）
free -m  # 监看内存是否持续增长

# 定期检查日志
tail -f logs/app.log
```

## 故障排除

如果启动失败：
1. 检查日志：`journalctl -u bazi -n 50`
2. 检查依赖：`pip list | grep sxtwl`
3. 检查端口：`netstat -tlnp | grep 8000`
```

---

## 总结

**新增问题清单**：#14-#28，共15个新问题

**按优先级**：
- 🔴 必须周1前完成：#14(缓存/基础), #15(并发), #16(版本管理), #17(隐私), #19(闰月), #25(用户文档)
- 🟠 必须周2前完成：#18(GDPR), #20(经度精度), #21(错误检测), #22(XSS), #24(时间输入UX), #26(反馈渠道), #27(依赖文档)
- 🟡 周3-4可完成：#23(移动端适配fullspec), #28(部署文档)

**总体工作量增加**：再加3-4周（从原来的20+30=50，现在变50+40=90周... 实际上这个项目比最初预期复杂5倍）

