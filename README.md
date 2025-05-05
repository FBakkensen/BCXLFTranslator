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
- **Microsoft Business Central terminology integration**
- **Terminology extraction and database management**
- **Translation source attribution (Microsoft or Google)**
- **Statistics reporting for translation sources**

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
# Using the module directly
python -m bcxlftranslator.main input.xlf output.xlf

# Or, after installation as a package
bcxlftranslator input.xlf output.xlf

# With PowerShell's .\ syntax for local scripts
.\python -m bcxlftranslator.main input.xlf output.xlf
```

### Command-Line Arguments

- `input.xlf`: Path to the source XLIFF file to be translated
- `output.xlf`: Path where the translated XLIFF file should be saved
- `--extract-terminology`: Extract terminology from Microsoft reference XLIFF file
- `--use-terminology`: Use stored terminology during translation
- `--stats-file`: Save translation statistics to specified file
- `--help`: Show help information
- `--version`: Show version information

### Example Workflow

1. Export XLIFF translation file from Business Central
2. Run BCXLFTranslator on the file
3. Import the translated file back into Business Central

```powershell
# Example with specific files in PowerShell
bcxlftranslator "./BaseApp.en-US.xlf" "./BaseApp.fr-FR.xlf"

# With full paths (Windows style)
bcxlftranslator "C:\Projects\BC\BaseApp.en-US.xlf" "C:\Projects\BC\BaseApp.fr-FR.xlf"
```

## Microsoft Business Central Terminology Integration

### Overview

BCXLFTranslator now includes advanced features to ensure translations are consistent with Microsoft's official Business Central terminology. This helps maintain consistency with Microsoft's official localization and improves translation quality for domain-specific terms.

### Terminology Extraction

Before translating your own files, you can extract official Microsoft terminology from reference XLIFF files:

```powershell
# Extract terminology from Microsoft reference file
python -m bcxlftranslator.main --extract-terminology "path/to/microsoft-reference.xlf" --lang fr-FR

# Multiple files can be processed for comprehensive terminology coverage
python -m bcxlftranslator.main --extract-terminology "path/to/another-reference.xlf" --lang fr-FR
```

The extraction process:
1. Analyzes the XLIFF file to identify Business Central object types (Tables, Pages, Fields)
2. Extracts source and target text pairs
3. Stores them in a SQLite database for future use
4. Prioritizes business-specific terms over general vocabulary

### Using Terminology During Translation

When translating your XLIFF files, enable terminology application:

```powershell
# Use the extracted terminology during translation
python -m bcxlftranslator.main input.xlf output.xlf --use-terminology

# You can also specify a custom terminology database path
python -m bcxlftranslator.main input.xlf output.xlf --use-terminology --terminology-db "path/to/custom/terminology.db"
```

With terminology enabled, the translation process:
1. First checks if terms exist in the terminology database
2. Uses Microsoft's official translations when available
3. Falls back to Google Translate for terms not found in the database
4. Adds source attribution notes to the output XLIFF file

### Translation Source Attribution

When using terminology integration, the output XLIFF includes source attribution notes:

```xml
<trans-unit id="example-id">
  <source>Sales Quote</source>
  <target>Salgstilbud</target>
  <note from="BCXLFTranslator">Source: Microsoft Terminology</note>
</trans-unit>
```

Terms not found in the terminology database will show:

```xml
<trans-unit id="example-id">
  <source>Custom Field</source>
  <target>Brugerdefineret felt</target>
  <note from="BCXLFTranslator">Source: Google Translate</note>
</trans-unit>
```

### Translation Statistics

After translation, BCXLFTranslator provides statistics about terminology usage:

```
Translation statistics:
---------------------
Total translations: 534
Microsoft terminology used: 312 (58.4%)
Google Translate used: 222 (41.6%)
```

You can save these statistics to a file for further analysis:

```powershell
# Save statistics to a CSV file
python -m bcxlftranslator.main input.xlf output.xlf --use-terminology --stats-file "translation-stats.csv"
```

The CSV file includes detailed information about each translated term and its source.

### Terminology Database Management

The terminology database is stored in SQLite format (default location is in the user's AppData directory). It contains:

1. **Terms Table**: Stores source terms, target terms, context, and object type
2. **Metadata Table**: Records source files, versions, and language pairs

Advanced users can interact with the database directly using SQL tools if needed.

## How It Works

BCXLFTranslator processes XLIFF files by:

1. Parsing the XML structure while preserving namespaces
2. Identifying source and target languages from file metadata
3. Finding translation units that need translation
4. Checking the terminology database for official Microsoft translations
5. Translating remaining text using Google Translate with intelligent caching
6. Applying case matching to maintain capitalization patterns
7. Preserving XML attributes and structure
8. Adding source attribution notes
9. Writing the translated content back to the output file
10. Generating translation statistics

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
- `TERMINOLOGY_DB_PATH`: Path to the terminology database (default: AppData location)

## Known Limitations

- Uses the unofficial `googletrans` library which may be subject to rate limiting
- Terminology database is language-pair specific (e.g., EN→FR)
- Translation quality depends on Google Translate's capabilities for the language pair
- Terminology extraction works best with Microsoft official XLIFF files

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
