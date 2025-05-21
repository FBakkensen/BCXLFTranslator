# BCXLFTranslator

A Python CLI tool for automating translations of XLIFF files (XML Localization Interchange File Format) used in software localization processes, especially for Business Central applications. Designed primarily for Windows environments.

## Features

- Automatic translation of XLIFF files using Google Translate
- Preserves XML formatting and namespaces
- Intelligent case matching to maintain proper capitalization
- Translation caching to ensure consistency and reduce API calls
- Handles specialized formatting like dotted words (e.g., "Prod.Order")
- Retry mechanism for handling transient errors
- Detailed progress reporting during translation
- Support for namespace-specific XML attributes
- **Translation source attribution**
- **Statistics reporting**

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Windows OS (primary target platform)

### Install from source (Windows)

```powershell
# Clone the repository
git clone https://github.com/yourusername/BCXLFTranslator.git
cd BCXLFTranslator

# Install the package in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev]"
```

### Install required dependencies

```powershell
# In PowerShell
pip install -r requirements.txt
```

### Quick Setup on Windows

For convenience on Windows systems, you can use the included batch file to set up the environment:

```powershell
# From PowerShell, execute the activation script
.\activate_venv.bat
```

## Usage

### Basic Usage (Windows PowerShell)

```powershell
# Using the module directly (recommended for src layout)
python -m src.bcxlftranslator.main input.xlf output.xlf
```

### Command-Line Arguments

- `input.xlf`: Path to the source XLIFF file to be translated
- `output.xlf`: Path where the translated XLIFF file should be saved
- `--help`: Show help information

### Example Workflow

1. Export XLIFF translation file from Business Central
2. Run BCXLFTranslator on the file
3. Import the translated file back into Business Central

```powershell
# Example with specific files in PowerShell
python -m src.bcxlftranslator.main "./BaseApp.en-US.xlf" "./BaseApp.fr-FR.xlf"

# With full paths (Windows style)
python -m src.bcxlftranslator.main "C:\Projects\BC\BaseApp.en-US.xlf" "C:\Projects\BC\BaseApp.fr-FR.xlf"
```

### Translation Source Attribution

The output XLIFF includes source attribution notes:

```xml
<trans-unit id="example-id">
  <source>Custom Field</source>
  <target>Brugerdefineret felt</target>
  <note from="BCXLFTranslator">Source: Google Translate</note>
</trans-unit>
```

### Translation Statistics

After translation, BCXLFTranslator provides statistics about translation:

```
Translation statistics:
---------------------
Total translations: 534
Google Translate used: 534 (100.0%)
```

## How It Works

BCXLFTranslator processes XLIFF files by:

1. Parsing the XML structure while preserving namespaces
2. Identifying source and target languages from file metadata
3. Finding translation units that need translation
4. Translating text using Google Translate with intelligent caching
5. Applying case matching to maintain capitalization patterns
6. Preserving XML attributes and structure
7. Adding source attribution notes
8. Writing the translated content back to the output file
9. Generating translation statistics

## Advanced Features

### Case Matching

The translator intelligently matches the capitalization pattern of the source text:
- ALL CAPS text stays in ALL CAPS
- Title Case text stays in Title Case
- Preserves special formatting like "Prod.Order" with proper capitalization

### Translation Caching

Identical source texts are cached to:
- Ensure consistency across the document
- Reduce the number of API calls
- Improve translation speed for repeated terms

### Error Handling

The tool includes:
- Retry mechanisms for transient network errors
- Detailed logging of translation progress and errors
- Summary statistics after completion

## Configuration

The following configuration parameters can be adjusted in the code:

- `DELAY_BETWEEN_REQUESTS`: Time delay between translation requests (default: 0.5s)
- `MAX_RETRIES`: Maximum number of retries for failed translations (default: 3)
- `RETRY_DELAY`: Time to wait before retrying (default: 3.0s)

## Known Limitations

- Uses the unofficial `googletrans` library which may be subject to rate limiting
- Translation quality depends on Google Translate's capabilities for the language pair

## Development

### Setting Up a Development Environment (Windows)

```powershell
# Clone the repository
git clone https://github.com/yourusername/BCXLFTranslator.git
cd BCXLFTranslator

# Create a virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# If using standard Command Prompt
# .\venv\Scripts\activate.bat

# Install development dependencies
pip install -e ".[dev]"
```

### Windows-Specific Notes

- File paths in Windows use backslashes (`\`) but these are escape characters in PowerShell strings. Either use:
  - Forward slashes (`/`) which work in Python on Windows
  - Double backslashes (`\\`)
  - PowerShell's `-LiteralPath` parameter style where applicable

- If you encounter permission issues in PowerShell, you may need to adjust execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Running Tests

```powershell
# In PowerShell
python -m pytest -v
```

### Test Coverage

```powershell
pytest --cov=bcxlftranslator
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [googletrans](https://github.com/ssut/py-googletrans) library
- Inspired by the need for efficient XLIFF translation in Business Central development
- Special thanks to contributors and the open source community

## Disclaimer

This tool relies on the unofficial Google Translate API and is not affiliated with or endorsed by Google. Use at your own risk and be aware of Google's terms of service regarding automated translation requests.
