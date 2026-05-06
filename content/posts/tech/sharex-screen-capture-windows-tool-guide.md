---
title: "ShareX 全面指南：Windows 最强截图与文件分享工具"
date: "2026-05-02T20:05:17+08:00"
slug: "sharex-screen-capture-windows-tool-guide"
description: "ShareX 是 Windows 平台最全能的免费截图与文件分享工具。本文深入解析其多模态截图体系、上传器生态、自定义工作流与二次开发路径，覆盖从安装配置到自定义上传器的完整知识，助你从入门到精通。"
draft: false
categories: ["技术笔记"]
tags: ["ShareX", "截图工具", "Windows", "C#", "文件分享", "GIF录制", "OCR"]
---

# ShareX 全面指南：Windows 最强截图与文件分享工具

## 📖 一、ShareX 是什么

[ShareX](https://github.com/ShareX/ShareX) 是一款运行在 Windows 平台的开源免费工具，主打截图、录屏、文件分享三大功能。它诞生于 2007 年，由 Jaex（Kim Larsson）主导开发，目前托管于 GitHub，采用 GPL-3.0 开源许可证。截至 2026 年初，项目已积累约 36,500 颗星、3,600+ 个 Fork，是同类型工具中社区最活跃的项目之一。

ShareX 的核心能力可以概括为"**一次触发，全自动执行**"：用户按下自定义快捷键，程序自动完成截图（或录屏）→ 图片注释/标注 → 上传到指定目标 → 将链接复制到剪贴板。整个流程可以在数秒内完成，途中无需人工干预。

官方提供两种安装方式：

- **Setup 安装包**（`ShareX-20.0.4-setup-x64.exe`）：标准安装，自动创建开始菜单快捷方式
- **Portable 压缩包**（`ShareX-20.0.4-portable-x64.zip`）：解压即用，配置数据存储在程序目录下，适合放在 U 盘或重装系统时保持设置

官网地址为 [getsharex.com](https://getsharex.com)，也上架了 [Steam](https://store.steampowered.com/app/400040/ShareX/) 和 [Microsoft Store](https://apps.microsoft.com/detail/9nblggh4z1sp)。

## 🔬 二、技术架构解析

### 2.1 模块化设计

ShareX 采用多项目（Multi-project）结构，主仓库下包含 8 个独立模块，各自职责清晰：

| 模块 | 职责 |
|------|------|
| `ShareX` | 主程序入口、UI 层（WinForms）、热键管理、任务调度 |
| `ShareX.HelpersLib` | 通用辅助函数、配置读写、跨模块工具类 |
| `ShareX.HistoryLib` | 上传历史记录管理 |
| `ShareX.ImageEditor` | 内置图片编辑器 |
| `ShareX.ImageEffectsLib` | 图片特效滤镜（模糊、锐化、浮雕等） |
| `ShareX.IndexerLib` | 图像内容索引与 OCR |
| `ShareX.MediaLib` | 媒体文件处理（FFmpeg 集成、缩略图生成） |
| `ShareX.ScreenCaptureLib` | 区域截图、滚动截图、屏幕录制核心逻辑 |
| `ShareX.UploadersLib` | 全部上传器实现（60+ 种目标） |
| `ShareX.NativeMessagingHost` | 浏览器扩展与主机进程的通信层 |

主程序使用 **WinForms** 构建界面，这是一个常被现代开发者低估的框架——在高频 UI 交互场景下，WinForms 的消息循环足够轻量，配合自定义绘制可以实现高性能的截图覆盖层。`ShareX.ScreenCaptureLib/Forms/RegionCaptureForm.cs` 即负责区域截图时那个半透明边框 UI。

### 2.2 截图技术栈

ShareX 的截图能力建立在 Windows 原生 API 之上，核心调用链如下：

1. **GDI+（Graphics Device Interface）**：`Graphics.CopyFromScreen` 是最基础的屏幕抓取方式，适用于全屏和窗口截图
2. **BitBlt + CreateCompatibleDC**：对于区域截图，ShareX 通过 BitBlt（Bit Block Transfer）将指定屏幕区域位图块传输到内存 DC，再保存为 `System.Drawing.Bitmap`
3. **`RegionCaptureForm` 覆盖层**：当用户启动区域截图时，ShareX 创建一个无边框透明窗体覆盖全屏，监听鼠标拖拽事件实时绘制选区边框。这个窗体通过 Win32 API 的 `SetWindowLong` 与 `SetLayeredWindowAttributes` 实现半透明效果
4. **FFmpeg 集成**：屏幕录制功能通过调用系统已安装的 FFmpeg，将抓取的原始帧编码为 MP4/GIF。`ShareX.ScreenCaptureLib/Forms/ScreenRecordForm.cs` 负责录制控制，FFmpeg 参数可通过 UI 自定义（分辨率、帧率、编码器）

关键代码路径在 `ShareX.ScreenCaptureLib/Forms/RegionCaptureForm.cs`，其中鼠标事件处理：

```csharp
// ShareX.ScreenCaptureLib/Forms/RegionCaptureForm.cs（示意）
protected override void OnMouseDown(MouseEventArgs e)
{
    _startPoint = e.Location;
    _isSelecting = true;
    // 开始绘制选区
}

protected override void OnMouseMove(MouseEventArgs e)
{
    if (_isSelecting)
    {
        _currentPoint = e.Location;
        Invalidate(); // 触发 OnPaint 重绘
    }
}

protected override void OnMouseUp(MouseEventArgs e)
{
    _isSelecting = false;
    var region = new Rectangle(
        Math.Min(_startPoint.X, _currentPoint.X),
        Math.Min(_startPoint.Y, _currentPoint.Y),
        Math.Abs(_currentPoint.X - _startPoint.X),
        Math.Abs(_currentPoint.Y - _startPoint.Y));
    CaptureRegion(region); // 执行实际截图
}
```

### 2.3 上传器架构

`ShareX.UploadersLib` 是整个工具链中最复杂的部分。它采用了**适配器模式**（Adapter Pattern），每种上传目标都是一个独立类，统一实现 `IUploaderService` 接口（或继承 `Uploader` 基类）。

上传器配置由 `UploadersConfig` 类集中管理，该类继承 `SettingsBase<UploadersConfig>`，通过 JSON 序列化存储在 `%AppData%\ShareX\Uploaders.json`。上传器分为四大类：

- **图片上传器**：Imgur、Flickr、Chevereto、vgy.me 等
- **文件上传器**：Dropbox、Google Drive、OneDrive、FTP、SFTP、Amazon S3、Google Cloud Storage、Backblaze B2、Box 等
- **文本上传器**：Pastebin、 hastebin、dpaste 等
- **短链接服务**：Bit.ly、tinyurl、tny.im 等

所有上传器共享一套 `UploadResult` 数据结构，包含 URL、删除URL、文件名、文件大小等信息。任务完成后，结果通过 `NotificationForm`（通知气泡）或主界面任务列表呈现给用户。

### 2.4 自定义 Uploader 机制

对于没有预设的上传目标，ShareX 支持**自定义 uploader**（Custom Uploader）。用户可以通过 JSON 格式配置请求参数：

```json
{
  "Name": "My Server",
  "RequestUrl": "https://example.com/upload",
  "FileFormName": "file",
  "Headers": {
    "Authorization": "Bearer YOUR_TOKEN"
  },
  "ResponseType": "Text",
  "URL": "https://example.com/files/{json:hash}"
}
```

`{json:hash}` 是一个内联变量，在上传完成后从服务器响应 JSON 中提取对应字段作为最终 URL。类似的变量还有 `{json:path.to.field}`、`{response}`（原始响应文本）等。这套机制足够灵活，可以对接任何 RESTful 风格的图床或文件服务器。

## ⚙️ 三、安装与配置

### 3.1 安装方式对比

| 安装方式 | 安装包大小 | 配置存储位置 | 适合场景 |
|------|------|------|------|
| Setup 安装包 | ~116 MB | `%AppData%\ShareX` | 长期日常使用 |
| Portable 压缩包 | ~173 MB | 程序同级目录 | 移动使用、重装系统保护 |

首次启动时，ShareX 会弹出**首次配置向导**（First Time Config Form），引导用户选择默认截图保存位置、默认上传器以及快捷键。建议在这一步配置好「截图后自动上传并复制链接」这一最核心的工作流。

### 3.2 快捷键配置

ShareX 的快捷键体系非常精细，分为三个层级：

**主快捷键**（在设置 → 快捷键中配置）：

| 功能 | 默认快捷键 | 说明 |
|------|------|------|
| 全屏截图 | `PrintScreen` | 截取整个屏幕 |
| 区域截图 | `Ctrl + Shift + PrtScn` | 拖拽选择区域 |
| 窗口截图 | `Ctrl + Shift + W` | 截取指定窗口 |
| 录屏 | `Ctrl + Shift + R` | 开始/停止屏幕录制 |

**快速任务菜单**（Quick Task）：在托盘图标右键或通过热键呼出，可以临时选择不同的截图/上传组合。

**自定义工作流**：通过「Actions」功能，可以将多个步骤绑定到一个快捷键，例如"截图 → 模糊处理 → 上传到 Imgur → 复制链接"可以合并为一个快捷键。

### 3.3 图片后期处理

截图后，ShareX 可以自动执行一系列「后期动作」：

1. **图片编辑器**（Image Editor）：内置编辑器支持标注、画框、马赛克、箭头、文字等操作，底层由 `ShareX.ImageEditor` 模块驱动
2. **图像效果**（Image Effects）：提供约 20 种预设滤镜，包括暗角（Vignette）、模糊（Blur）、锐化（Sharpen）、灰度、反转等
3. **水印**：可配置文字或图片水印，支持位置、透明度、边距等参数
4. **OCR 识别**：通过 `ShareX.IndexerLib` 调用 Windows 内置 OCR API，将截图中的文字提取出来。配置路径：设置 → 截图 → 启用「文字识别（OCR）」，快捷键为 `Ctrl + Shift + O`

### 3.4 滚动截图（Scrolling Screenshot）

ShareX 支持滚动截图，底层通过 `ShareX.ScreenCaptureLib/Forms/ScrollingCaptureForm.cs` 实现。其工作原理是：

1. 用户选中目标窗口
2. 模拟滚动（WM_VSCROLL / WM_HSCROLL 消息），分片截取可视区域
3. 将所有切片在内存中垂直拼接
4. 输出完整长图

这个功能对于截取网页、聊天记录、文档等超长内容非常有用。滚动速度和每次滚动的像素量可在设置中调整，以适配不同应用窗口的滚动粒度。

## 🎬 四、核心功能实战演示

### 4.1 基础截图流程

1. 按下 `Ctrl + Shift + PrtScn`（区域截图快捷键）
2. 屏幕变暗，拖拽鼠标选择目标区域
3. 松开鼠标，截图自动保存并上传到配置的图床
4. 链接自动复制到剪贴板，直接 `Ctrl + V` 粘贴使用

整个过程通常在 3 秒以内完成。

### 4.2 屏幕录制 GIF/MP4

1. 按 `Ctrl + Shift + R` 开始录制（或在快捷键设置中配置）
2. 首次录制前，ShareX 会提示下载 FFmpeg（需要系统已安装或在设置中指定路径）
3. 选择录制区域，开始录制。录制过程中可按 `Esc` 停止
4. 停止后自动弹出编辑界面，可裁剪时长、添加字幕
5. 输出格式支持 MP4 和 GIF，可通过设置 → 屏幕录制 → 输出格式切换

GIF 录制是很多开发者制作 Demo 的首选方案，相较于 MP4，GIF 无需额外解码器，在多数平台直接嵌入展示。

### 4.3 监控文件夹（Watch Folder）

ShareX 支持**文件夹监控**（Watch Folder）功能：指定一个文件夹后，所有复制进去的文件都会自动触发上传。这对于频繁需要将本地文件分享到图床的场景特别有用。

配置路径：设置 → 监控文件夹 → 添加文件夹路径、文件类型过滤、上传器选择。

### 4.4 上传到多个目标

ShareX 支持将同一文件**同时上传到多个上传器**。在「Destination」设置中，可以为不同文件类型配置不同的上传目标组合。例如：

- 截图 → 自动上传到 Imgur + Chevereto（双保险）
- 视频文件 → 上传到 Google Drive

这个多目标上传机制基于 `UploadManager` 的 `Upload(WorkerTask task)` 方法，它会遍历 `task.destinations` 列表，串行执行每个上传任务。

### 4.5 截图后的标注与注释

区域截图完成后，ShareX 默认弹出**图片编辑器**，用户可以：

- 使用**画笔工具**自由绘制（颜色、笔触大小可调）
- 使用**箭头/矩形/椭圆**工具标注重点
- 使用**模糊/马赛克工具**遮盖敏感信息
- 使用**文字工具**添加注释
- 使用**裁剪工具**调整画面范围

编辑完成后，点击「上传」或「保存」完成后续流程。编辑器支持高DPI 缩放，界面在 4K 显示器上也能清晰显示。

## 🚀 五、高级配置与定制

### 5.1 自定义截图后工作流（Actions）

ShareX 的 **Actions** 功能是一个强大的任务编排工具。每个 Action 由一个触发条件（快捷键）和多个执行步骤组成：

**示例：自动加水印并上传**

```
触发条件：Ctrl + Shift + W

步骤 1：执行截图（区域截图）
步骤 2：应用图像效果（添加水印）
步骤 3：复制图像到剪贴板
步骤 4：上传到 FTP 服务器
步骤 5：复制链接到剪贴板
```

Actions 支持的条件包括：截图、文件复制到剪贴板、文件拖放入 ShareX、监控文件夹文件变化等。支持嵌套逻辑（If-Then）和变量传递，可以构建相当复杂的自动化流程。

### 5.2 自定义上传器实战

下面以配置一个自建图床为例，说明如何用自定义上传器对接私有 API：

1. 打开 ShareX → 设置 → 上传器 → 目的地 → 添加新上传器 → 选择「自定义」
2. 配置以下参数：
   - **Request URL**：`https://your-imagehost.com/api/upload`
   - **Method**：`POST`
   - **File form name**：`image`
   - **Headers**：`Authorization: Bearer YOUR_ACCESS_TOKEN`
   - **URL**：`https://your-imagehost.com/{json:url}`（从响应 JSON 中取 url 字段）

上传后，ShareX 会将 `{json:url}` 替换为服务器返回的 JSON 中 `url` 字段的值，实现动态 URL 获取。

### 5.3 云存储上传器配置

**Backblaze B2** 是一个性价比极高的对象存储，以下是 ShareX 中的配置要点：

| 配置项 | 说明 |
|------|------|
| Endpoint | `s3.us-west-000.backblazeb2.com`（根据 bucket 区域选择） |
| Access Key | Backblaze B2 Application Key ID |
| Secret Key | Application Key |
| Bucket Name | 你的 bucket 名 |
| 自定义域名 | 可在 URL 格式中填入自己的 CDN 域名 |

Amazon S3、Google Cloud Storage、Cloudflare R2 的配置方式与 B2 类似，都属于 S3 兼容存储，ShareX 内置了对应的上传器类（`AmazonS3.cs`、`GoogleCloudStorage.cs`）。

### 5.4 浏览器集成

ShareX 支持通过浏览器扩展（Chrome/Firefox）与桌面端联动。扩展通过 **`ShareX.NativeMessagingHost`** 与桌面程序通信，用户在网页上右键选择「截图并上传到 ShareX」即可将网页内容直接发送回桌面程序处理。

安装路径：设置 → 程序 → 浏览器集成 → 下载对应浏览器的扩展

## 🔧 六、二次开发指南

### 6.1 开发环境搭建

ShareX 使用 MSBuild / .NET 编译，推荐使用 Visual Studio 2022 或 JetBrains Rider 作为 IDE。克隆仓库后：

```bash
git clone https://github.com/ShareX/ShareX.git
cd ShareX
dotnet restore
dotnet build ShareX.sln
```

运行时直接启动 `ShareX/bin/Debug/net8.0/ShareX.exe`（或对应的输出路径）。项目目前主要使用 .NET 8（从 `ShareX.csproj` 可以看到目标框架配置）。

### 6.2 添加新的上传器

在 `ShareX.UploadersLib` 下新建类，继承 `Uploader` 或实现 `IUploaderService`：

```csharp
// ShareX.UploadersLib/FileUploaders/MyCustomUploader.cs
namespace ShareX.UploadersLib.FileUploaders
{
    public class MyCustomUploader : Uploader
    {
        private readonly string _apiKey;
        private readonly string _uploadUrl;

        public MyCustomUploader(string apiKey, string uploadUrl)
        {
            _apiKey = apiKey;
            _uploadUrl = uploadUrl;
        }

        public override Task<UploadResult> UploadAsync(Stream stream, string fileName)
        {
            var request = new HttpRequestSettings
            {
                Url = _uploadUrl,
                Method = HttpMethod.POST,
                Headers = new Dictionary<string, string>
                {
                    ["Authorization"] = $"Bearer {_apiKey}"
                },
                Data = stream,
                FileFormName = "file"
            };

            return SendRequestAsync(request);
        }
    }
}
```

然后在 `UploadersConfig.cs` 中添加对应的配置字段，并在 `DestinationSettingsForm.cs`（上传器设置界面）中添加 UI 控件。

### 6.3 修改截图行为

如果需要修改区域截图的行为，核心文件是：

- `ShareX.ScreenCaptureLib/Forms/RegionCaptureForm.cs` — 区域选择框的 UI 与交互逻辑
- `ShareX.ScreenCaptureLib/ScreenCaptureManager.cs` — 截图触发与图像获取
- `ShareX/CaptureHelpers/` — 各种截图类型的辅助函数（窗口截图、全屏截图等）

### 6.4 热键管理

热键管理由 `ShareX/HotkeyManager.cs` 实现，它通过 Win32 API `RegisterHotKey` 和 `UnregisterHotKey` 注册全局快捷键。当系统收到匹配的 WM_HOTKEY 消息时，会触发对应的 `WorkerTask` 执行。

如果需要新增快捷键功能，应在 `HotkeySettings.cs` 中定义枚举值，并在 `HotkeyManager.cs` 的消息分发逻辑中添加对应的处理分支。

## 📋 七、配置清单与最佳实践

| 场景 | 推荐配置 |
|------|------|
| 日常截图分享 | 区域截图 + 自动上传 Imgur + 复制链接，保存到本地副本 |
| 开发文档配图 | 全屏截图 + 添加水印 + 保存到项目文件夹 |
| 长截图 | 滚动截图 + 压缩优化 + 保存 PNG |
| GIF 录制 | 区域录制 + 帧率 15fps + 输出 GIF + 本地保存 |
| 隐私截图 | 区域截图 + 马赛克处理 + 不上传直接保存 |
| 团队协作 | 自建 S3 兼容图床 + 自定义上传器 + 分享域名 |

**隐私建议**：默认情况下，截图会在上传前临时保存在 `%AppData%\ShareX\Temp` 目录，完成后自动清理。如果截图中包含敏感信息，建议在设置 → 截图 → 取消勾选「截图后自动保存到文件」，只保留剪贴板副本，降低本地残留风险。

## ❓ 八、常见问题

**Q：ShareX 和 Snipaste 有什么区别？**

两者都支持截图标注，但设计哲学不同。Snipaste 专注于截图 + 贴图（把截图钉在桌面上作为参考），轻量级。ShareX 的核心优势在于**上传工作流**，截图后可自动上传到云端并返回链接，适合需要频繁分享截图的开发者和写作者。另一个显著差异是 ShareX 支持屏幕录制和 GIF 制作，Snipaste 不支持。

**Q：上传失败是什么原因？**

常见原因包括：上传器 API 密钥过期、网络代理拦截、文件超出大小限制（各平台不同，Imgur 免费版限制 10MB）。可在 ShareX 主界面查看任务状态，点击失败任务查看详细错误信息。

**Q：如何完全卸载 ShareX？**

如果使用的是 Portable 版，直接删除文件夹即可。安装版用户需通过「设置 → 关于 → 卸载」或系统「应用与功能」卸载。配置文件默认保存在 `%AppData%\ShareX`，如需彻底清除可手动删除该目录。

**Q：FFmpeg 录制没反应怎么办？**

先确认 FFmpeg 已安装且路径已添加到系统 `PATH` 环境变量。在命令行输入 `ffmpeg -version` 验证。如果 ShareX 无法找到，可以在设置 → 屏幕录制中手动指定 FFmpeg 路径。

**Q：能否同时截取多个屏幕？**

可以。在全屏截图时，ShareX 会自动枚举系统中所有显示器，通过 `Screen.AllScreens` 获取显示区域并逐一截图合并。如果需要每个屏幕单独保存一个文件，可在设置 → 截图 → 取消勾选「合并多显示器截图」。

---

ShareX 是那种装上就再也卸不掉的工具——不是因为依赖，而是因为它把"截图→处理→分享"这个高频操作链压缩到了一个快捷键里，真正消除了摩擦。如果你日常需要频繁截图、录屏、制作 GIF 或管理截图上传工作流，ShareX 是 Windows 上最值得掌握的效率工具之一。