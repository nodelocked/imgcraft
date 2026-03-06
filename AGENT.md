# ImgCraft Technical Report (AGENT.md)

## Project Overview
**ImgCraft** is a professional-grade photo management tool designed for high-speed organization, tagging, and reporting of image collections. It provides a unique balance between a file explorer and a professional inspiration board.

## Core Features
- **High-Density Sidebar**: Manages collections and folders with minimal waste space.
- **Master Export Engine**: Generates professional PDF reports with bold Chinese support and structured data bundles.
- **Silent Sorting Flow**: One-key silent deletion (`DEL`) and rapid navigation (`F1`/`F2`).
- **"Untouched" Smart Filter**: Automatically identifies images with zero tags or notes.
- **Persistence Layer**: Remembers the last viewed image per folder automatically.

## Technical Architecture
- **Language**: Python 3.x
- **GUI Framework**: PySide6 (Qt)
- **Database**: SQLite (Persists tags, notes, and folder history)
- **Image Engine**: Pillow (Handling high-res image scaling)
- **Reporting**: fpdf2 (Custom Unicode/Chinese engine)
- **CI/CD**: GitHub Actions (Cross-platform builds for Windows & macOS Arm64)

## Version History Summary
- **v0.1.0**: Initial Public Beta. Implemented Professional Mastery features (High-density UI, Power-user hotkeys, Unicode reporting).

## Developer Notes
The UI is built with a custom CSS system tailored for high-density information display. The logic layer is decoupled from the GUI via a `Manager` class to ensure stability.
