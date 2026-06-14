# PDF Merger Project

This project is a simple application for merging and managing PDF files using a graphical user interface built with PyQt6. The application allows users to add, remove, move, split, and merge PDF files easily.

## Features

- Add PDF files to the list
- Remove selected PDF files from the list
- Move PDF files up or down in the list
- Split a PDF file at a specified page
- Merge selected PDF files into a single PDF file

## Project Structure

```
PDF-Merger
├── src
│   ├── main.py            # Entry point of the application
│   ├── ui
│   │   ├── __init__.py    # UI package initializer
│   │   ├── main_window.py  # Main window UI definition
│   │   ├── merge_progress_dialog.py # Merge progress dialog UI definition
|   |   └── about_dialog.py # About dialog UI definition
│   └── logic
│       ├── __init__.py    # Logic package initializer
│       └── pdf_operations.py # PDF handling operations
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Setup Instructions

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies using pip:

   ```
   pip install -r requirements.txt
   ```

## Usage Guidelines

1. Run the application by executing the `main.py` file:

   ```
   python src/main.py
   ```

2. Use the interface to add PDF files to the list.
3. Select a PDF file to remove or move it within the list.
4. Specify a page number to split a PDF file.
5. Select multiple PDF files to merge them into a single file.

## Building for Windows

To create a standalone `.exe` and an Installer:

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Install [Inno Setup 6](https://jrsoftware.org/isdl.php) if you want to generate a Windows Installer (`.exe` setup).

3. Run the build script:
   ```bash
   python build_windows.py
   ```

### Output:
- **Standalone Executable**: Located in `dist/PDFMerger.exe`.
- **Installer**: If Inno Setup is installed, a setup file will be created in `installer/PDFMergerSetup.exe`.

## Dependencies

- PyQt6
- PyPDF2 or PyMuPDF (for PDF handling)

## License

This project is licensed under the MIT License. See the LICENSE file for more details.


## Credits

Icons from [Flaticon](https://www.flaticon.com/free-icon/pdf-file-format_15266347?term=pdf&page=1&position=22&origin=search&related_id=15266347)