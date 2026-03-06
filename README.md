# ImgCraft 🖼️

Professional-grade photo management and inspiration reporting tool.

## Features
- **Rapid Navigation**: F1/F2 or Arrow keys for lightning-fast browsing.
- **Silent Delete**: Instantly remove photos from disk with the DEL key.
- **Pro Reporting**: Export high-quality PDF reports with bold Chinese notes.
- **Smart Filters**: Find "Untouched" photos or filter by tags instantly.

## Installation & Running

1. **Setup Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Application**:
   ```powershell
   python -m app.main
   ```

## Packaging (Building Binaries)

To create a standalone executable:

### Windows
```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name ImgCraft --add-data "app/styles.css;app" app/main.py
```

### macOS (M-series)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ImgCraft --add-data "app/styles.css:app" app/main.py
```

## Developers
See [AGENT.md](./AGENT.md) for full technical architecture.
可以打标签、输入灵感。
支持点击已有标签，所有此标签的照片可以一并展示，方便都拖到一个文件夹下。反正就是方便我整理照片。
含有灵感的照片，也方便随时查看。
支持导出pdf，pdf的内容就是：有灵感的照片以及灵感的具体内容。
总之，这个软件就是为了方便我处理大量的图片的一个小工具。
适当完善
推荐：python3技术栈，保持功能少而简单。
