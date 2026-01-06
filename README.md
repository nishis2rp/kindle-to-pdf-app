# Kindle to PDF Automation App

This application automates the Kindle for PC desktop application to capture screenshots of all pages of a book and then combines these screenshots into a single, searchable (image-based) PDF file. It provides a user-friendly graphical interface to configure the automation process.

## Features

*   **Automated Screenshot Capture:** Automatically navigates through Kindle pages and captures screenshots of the book content.
*   **Dynamic Region Detection:** Intelligently identifies the book's reading area on the screen, adapting to different window sizes and resolutions.
*   **Manual Region Selection:** Allows users to manually define the capture area by dragging a rectangle on the screen for precise control.
*   **Test Capture Functionality:** Provides a "Test Capture" button to verify the selected capture region before starting the full automation.
*   **Configurable Page Turning:** Supports automatic detection of reading direction (Left-to-Right or Right-to-Left) or manual selection.
*   **Adjustable Delays:** Configurable delays for page turns, Kindle startup, window activation, etc., to ensure stability and accuracy.
*   **End-of-Book Detection:** Automatically stops when the end of the book is detected based on consecutive identical pages, with adjustable sensitivity.
*   **Image Optimization:** Options to optimize captured images (grayscale conversion, resizing) before PDF creation to reduce file size.
*   **Customizable Output:** Allows users to specify the output folder and filename for the generated PDF.
*   **Image Format and Quality Control:** Choose between PNG (high quality) or JPEG (lightweight with adjustable compression) for images within the PDF.
*   **Pause/Resume & Stop Control:** Full control over the automation process with Start/Pause/Resume buttons.
*   **Emergency Stop Hotkey:** Global hotkeys (`Esc` or `Ctrl+Q`) to immediately halt the automation.
*   **Real-time Monitoring:** Features a progress bar, a log area for status updates, and a live preview of captured pages.
*   **Disk Space Check:** Verifies sufficient disk space before starting the capture process.
*   **OS Sleep Prevention:** Prevents the operating system from going to sleep or turning off the display during automation.
*   **Persistent Settings:** All user preferences are saved and loaded automatically from `config.json`.

---

## Security and Usage Considerations

This application interacts with the Kindle for PC application by simulating mouse and keyboard inputs.

*   **DRM Compliance:** This system captures what is displayed on your screen and does NOT circumvent Digital Rights Management (DRM). It adheres to fair use principles by capturing legally displayed content.
*   **Mouse and Keyboard Occupation:** The PC cannot be used for other tasks during the automation process. **Do not move the mouse or type on the keyboard while the script is running.** Consider running it on a dedicated virtual machine (VM) or a secondary PC.
*   **Kindle Window State:** Ensure the Kindle for PC application is in a state where the book content is clearly visible. The application will attempt to bring the Kindle window to the foreground and maximize it.
*   **Output Folder Visibility:** Ensure the `Kindle_PDFs` output folder (or your custom selected folder) is accessible and has sufficient write permissions.

---

## Requirements

*   **OS:** Windows 10/11 (64-bit AMD/Intel processor is recommended due to `opencv-python` dependencies).
*   **Python:** Python 3.10 or 3.11 (AMD64/Intel 64-bit version recommended).
*   **Kindle for PC:** The Amazon Kindle for PC desktop application must be installed.
*   **Libraries:** All Python dependencies listed in `requirements.txt`.

---

## Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nishis2rp/kindle-to-pdf-app.git
    cd kindle-to-pdf-app
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create virtual environment (ensure you are using Python 3.11 or 3.10 AMD64)
    py -3.11 -m venv venv 
    # Activate virtual environment
    .\venv\Scripts\activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

---

## How to Use (Manual)

### Launching the Application

You can launch the application in two ways:

1.  **From the Python script:**
    ```bash
    .\venv\Scripts\python.exe main.py
    ```
2.  **Using the generated executable:**
    Navigate to the `dist` folder in your project directory and double-click `main.exe`.

### GUI Overview

The application features a two-pane layout:

*   **Left Pane (Settings):** Contains all configurable parameters for the automation.
*   **Right Pane (Monitoring):** Displays real-time progress, a live preview of captured pages, and a detailed log.

### Settings Explanation (Left Pane)

#### 1. Target Settings

*   **Region Detection Mode:**
    *   **Automatic:** The application will attempt to automatically detect the book's reading area within the Kindle window using image processing.
    *   **Manual:** Allows you to manually specify the capture region.
*   **Select Area... Button:** (Enabled when "Manual" mode is selected)
    *   Click this button. Your screen will become semi-transparent. Drag your mouse to draw a rectangle around the Kindle book's reading content. Release the mouse button to confirm. Press `Esc` to cancel.
*   **Test Capture Button:**
    *   Click to take a single screenshot of the currently defined capture region (either automatically detected or manually selected) and display it in the "Preview" area. Use this to verify your region settings before a full run.
*   **Region Display:** Shows the coordinates (`x, y, width, height`) of the currently selected manual region.

#### 2. Action Parameters

*   **Page Turn Direction:**
    *   **Automatic:** The application will try to determine the correct page-turning direction (Left-to-Right or Right-to-Left) by testing key presses.
    *   **LtoR (Left-to-Right):** Forces page turns using the 'left arrow' key (typical for English books).
    *   **RtoL (Right-to-Left):** Forces page turns using the 'right arrow' key (typical for Japanese manga/vertical text).
*   **Max Pages to Capture:**
    *   Set the maximum number of pages to capture. This acts as a safety limit to prevent infinite loops in case end-of-book detection fails.
*   **End Detect Sensitivity (>=1):**
    *   Specifies how many consecutive identical pages are required to trigger the end-of-book detection. A value of `3` is usually sufficient. Higher values make detection less sensitive (requires more identical pages).

#### 3. Output Settings

*   **Output Folder:** The directory where the final PDF and temporary images will be saved. Click "Browse..." to select a folder.
*   **Filename:** The name of the generated PDF file (e.g., `My_Kindle_Book.pdf`).
*   **Image Format:**
    *   **PNG:** High-quality, lossless image format. Results in larger PDF files.
    *   **JPEG:** Lossy compression, results in smaller PDF files.
*   **JPEG Quality (0-100):** (Enabled when "JPEG" format is selected)
    *   Adjust the compression quality for JPEG images. 100 is highest quality (least compression), 0 is lowest quality (most compression).
*   **Optimize Images (Grayscale/Resize):**
    *   If checked, captured images will be converted to grayscale and resized (width limited to 800px) before being embedded in the PDF. This can significantly reduce PDF file size.

#### 4. Delay Settings (seconds)

Adjust these values based on your PC's performance and Kindle's responsiveness to ensure stable automation.

*   **Page Turn:** Delay after pressing a page-turn key before capturing the next page.
*   **Kindle Startup:** Initial delay after launching Kindle.
*   **Window Activation:** Delay after activating the Kindle window.
*   **Fullscreen Toggle:** Delay after pressing F11 to toggle fullscreen.
*   **Go to Home:** Delay after navigating to the beginning of the book.

### Execution & Monitoring (Right Pane)

*   **Start Automation Button:** Initiates the capture process. Changes to "Pause" and then "Resume" during operation.
*   **Stop Button:** Immediately halts the automation process.
*   **Open Output Folder Button:** Opens the configured output directory.
*   **Progress Bar:** Visually displays the current page being processed out of the total estimated pages.
*   **Preview:** Shows a live thumbnail of the most recently captured page.
*   **Log:** A text area displaying real-time status updates, warnings, and errors.

### Emergency Stop Hotkey

*   At any point during the automation, you can press `Esc` or `Ctrl + Q` on your keyboard to trigger an immediate stop.

---

## Troubleshooting

*   **`NameError: name 'KindleController' is not defined` (or similar import errors):** Ensure you have correctly set up your Python virtual environment with a compatible Python version (e.g., Python 3.11 AMD64) and reinstalled all `requirements.txt` dependencies. This error can occur if `opencv-python` or its underlying `numpy` dependency is not correctly installed for your specific Python version and architecture.
*   **Kindle App Not Found:** Ensure the Kindle for PC application is installed and running. If it's not found automatically, try launching it manually before starting the automation.
*   **Capture Region Issues:** Use the "Test Capture" button and the "Manual Region Selection" feature to precisely define and verify the capture area.
*   **"Nothing happens" after clicking Start:** Check the "Log" area for any error messages. Ensure all required settings (especially output folder/filename if not default) are filled. The automation might be waiting for Kindle to launch or activate.

---