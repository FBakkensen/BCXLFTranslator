# Terminology-Aware Translation System Architecture

## Overview

The Terminology-Aware Translation System enhances the existing BC XLF Translator by incorporating Business Central terminology preservation during the translation process. The system uses baseline terminology from the Base Application XLF files to ensure consistent translations of key business terms across different languages.

## Problem Statement

When translating Business Central applications, certain terminology must be preserved consistently:
- Common business terms (e.g., "Quote" → "Tilbud" in Danish)
- Posted document states (e.g., "Posted" → "Bogført" in Danish)
- Business Central-specific terminology

Using generic translation services like Google Translate may not maintain this specialized terminology, leading to inconsistent translations within and across applications.

## Architecture Components

### 1. Terminology Extraction Component

**Purpose**: Extract terminology pairs from the Base Application XLF files

**Key Classes and Functions**:
- `TerminologyManager`: Main class for terminology management
- `load_from_xlf()`: Load terminology from XLF file with streaming support
- `StreamingXLFParser`: Specialized parser for processing large XLF files efficiently

**Key Features**:
- Stream-based parsing to handle large XLF files (50MB+) without memory issues
- Extract source-target pairs for each language
- Skip irrelevant entries
- Support for incremental processing

### 2. Terminology Storage Component

**Purpose**: Store terminology efficiently for quick lookups during translation

**Key Classes and Functions**:
- `TerminologyDatabase`: In-memory database of terminology pairs
- `add_term()`: Add a terminology entry
- `get_translation()`: Get exact translation for a term
- `get_translation_fuzzy()`: Get translation using fuzzy matching

**Key Features**:
- Multi-language support (each language has its own terminology store)
- Fast dictionary-based lookups
- Persistence to disk (JSON or SQLite format)
- Term similarity scoring for fuzzy matching

### 3. Terminology-Aware Translation Service

**Purpose**: Enhance the existing translation process with terminology lookups

**Key Classes and Functions**:
- `TerminologyAwareTranslator`: Enhanced translator with terminology support
- `translate_with_terminology()`: Main method to translate with terminology awareness
- Integration with the existing `translate_xliff()` function

**Key Features**:
- Check terminology database before using Google Translate
- Apply terminology consistently across the translation
- Fallback to Google Translate when no terminology match is found
- Case preservation using the existing `match_case()` function
- Support for partial matches and context-aware translation

### 4. Configuration System

**Purpose**: Control terminology handling behavior

**Key Classes and Functions**:
- `TerminologyConfig`: Configuration class for terminology settings
- `ConfigLoader`: Load and validate configuration

**Key Features**:
- Configure paths to terminology files for different languages
- Set matching thresholds for fuzzy matching
- Enable/disable terminology features
- Control terminology precedence over machine translation

## Workflow

1. **Initialization**:
   - Load configuration
   - Initialize TerminologyManager
   - Load base terminology files for target languages

2. **Translation Process**:
   - For each translation unit:
     a. Check if the term exists in the terminology database
     b. If found, use the stored translation
     c. If not found, try fuzzy matching if enabled
     d. If no match, use Google Translate
     e. Apply case matching to the result

3. **Post-Processing**:
   - Review and validate translations
   - Statistics generation
   - Error reporting

## Integration with Existing System

The terminology system will integrate with the existing `translate_xliff()` function in `main.py`, enhancing it with terminology awareness:

```python
async def translate_xliff(input_file, output_file, terminology_manager=None):
    # Existing code...

    # Initialize terminology manager if provided
    if terminology_manager is None:
        terminology_manager = TerminologyManager()
        # Load default terminology files based on target language
        if os.path.exists(f"BaseTranslations/Base Application.{target_lang_code}.xlf"):
            terminology_manager.load_from_xlf(
                f"BaseTranslations/Base Application.{target_lang_code}.xlf",
                target_lang_code
            )

    # During translation, check terminology first
    # ...existing code...

    # When translating a source_text:
    translated_text = terminology_manager.get_translation(source_text, target_lang_code)
    if translated_text is None:
        # Try fuzzy matching if exact match not found
        translated_text = terminology_manager.get_translation_fuzzy(source_text, target_lang_code)

    # Fall back to Google Translate if not found in terminology
    if translated_text is None:
        translated_text = await translate_with_retry(...)

    # ...existing code...
```

## Technical Considerations

### Performance Optimization

- **Memory Usage**: Stream-based XLF parsing to handle large files
- **Caching**: Two-level cache (terminology DB + translation cache)
- **Preloading**: Option to preload common terminology files

### Fuzzy Matching Algorithm

- Use of string similarity metrics:
  - Levenshtein distance
  - Token-based similarity (for multi-word terms)
  - Weighted term matching (business terms weigh more)
- Configurable similarity threshold (default: 0.85)

### Extension Points

- Plugin system for custom terminology sources
- User feedback mechanism to improve terminology matching
- Export/import of terminology databases
- Web interface for terminology management

## Testing Strategy

Following TDD principles, tests are implemented before the actual code:

1. **Unit Tests**:
   - Test terminology loading from XLF
   - Test exact and fuzzy term matching
   - Test multi-language support
   - Test streaming of large files

2. **Integration Tests**:
   - Test integration with translation pipeline
   - Test end-to-end translation with terminology

3. **Performance Tests**:
   - Test memory usage with large terminology files
   - Test translation speed with terminology lookup

## Future Enhancements

- Terminology conflict resolution
- UI for terminology management
- Machine learning to improve fuzzy matching
- Shared terminology database across projects
- Version control for terminology databases

## Dependencies

- `difflib`: For fuzzy string matching
- `xml.etree.ElementTree`: For XML parsing
- `sqlite3` (optional): For persistent storage
- Existing translation system dependencies