# Kindle to PDF Automation

A simple desktop application to automate the process of converting a Kindle book from the Kindle for PC application into a PDF file by taking screenshots.

## Features

- **Automated Screenshots:** Automatically takes screenshots of each page.
- **Page Turning:** Simulates key presses to turn pages in the Kindle app.
- **PDF Conversion:** Compiles the captured screenshots into a single PDF file.
- **Simple GUI:** An easy-to-use interface built with Tkinter.
- **Auto-Find Window:** Automatically finds the Kindle application window and brings it to the foreground.
- **Full-Screen Mode:** Puts the Kindle app into full-screen mode for clean captures.

---

## ?? Security Warning

This application takes control of your mouse and keyboard to automate interactions with the Kindle application. 

- **Do not use your mouse or keyboard** while the screenshot process is running.
- Ensure that **no sensitive information** is visible on your screen, as the application takes full-screen captures.

The author of this program is not responsible for any unintended consequences. Use at your own risk.

---

## Requirements

- **Operating System:** Windows
- **Python:** 3.6+
- **Kindle for PC:** The official desktop application from Amazon must be installed.

---

## Installation & Setup

1.  **Clone the repository:**
    `ash
    git clone https://github.com/nishis2rp/kindle-to-pdf-app.git
    cd kindle-to-pdf-app
    `

2.  **Create and activate a Python virtual environment:**
    `ash
    # Create the virtual environment
    python -m venv venv

    # Activate it
    .\venv\Scripts\activate
    `

3.  **Install the required dependencies:**
    `ash
    pip install -r requirements.txt
    `

---

## Usage

1.  **Start the Kindle for PC application.** You can be logged in and have your book open, or just have the app running.
2.  **Run the script:**
    `ash
    python main.py
    `
3.  The application window will appear. Enter the total number of pages you wish to capture.
4.  Click the **"Start"** button.
5.  The script will find the Kindle window, bring it to the front, and put it into full-screen mode. The process will begin after a short delay.
6.  Once finished, the Kindle app will exit full-screen mode, and a success message will appear.

All generated PDFs will be saved in the Kindle_PDFs directory within the project folder.

---
