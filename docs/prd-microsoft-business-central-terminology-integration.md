# Feature Overview
Add capability to extract and apply official Microsoft Business Central terminology from reference XLIFF files to ensure translation consistency with Microsoft's official terminology, particularly for domain-specific terms.

# Problem Statement
When translating Business Central applications, Google Translate often provides technically correct but contextually inappropriate translations for business terminology. Example: translating "Quote" to "Citat" in Danish when in Business Central context, it should be "Tilbud".

# Proposed Solution
Develop a terminology extraction and application system that:

1. Extracts Business Central-specific terminology from official Microsoft XLIFF files
2. Applies this terminology during translation before falling back to Google Translate
3. Annotates translations with their source (Microsoft or Google)

# Technical Requirements
1. Terminology Identification & Extraction

## Definition of "Terminology"
- Business objects (Tables, Fields, Pages) names and captions (priority #1)
- Business-specific terms that have domain-specific translations
- Common terms that appear frequently in UI elements
- Single words or compound terms that have specific meaning in Business Central

## Extraction Logic
- Parse XLIFF files looking for high-priority elements (Tables, Fields, Pages)
- Build a terminology database from source/target pairs
- Example: extract that "Quote" translates to "Tilbud" in Sales/Purchase contexts

2. Terminology Storage
## Storage Format: SQLite database with appropriate indexing
- Fast lookups for thousands of terms
- Persistent between runs
## Schema:
- Terms table: source term, target term, context, object type, language
- Metadata table: source file, version, language pair
## Runtime Optimization:
- Load into in-memory dictionary on startup for maximum performance during translation

3. Translation Process Integration
## Modify translation pipeline:
- Check terminology database for exact matches
- Apply terminology translation if found
- Fall back to Google Translate only when terms aren't in database
- Apply case-matching and other post-processing
## Add source attribution annotation in output XLIFF:

```xml
<trans-unit id="example-id">
  <source>Sales Quote</source>
  <target>Salgstilbud</target>
  <note from="BCXLFTranslator">Source: Microsoft Terminology</note>
</trans-unit>
```

5. Statistics Generation
## Track and report:
- Number/percentage of terms translated using Microsoft terminology
- Number/percentage of terms translated using Google Translate
- Total number of translations processed
## Display statistics at the end of translation process
## Optionally save statistics to a report file

5. Command-line Interface Enhancements
- Add new command to extract terminology:

```powershell
bcxlftranslator --extract-terminology <microsoft-reference.xlf> --lang <language-code>
```

- Add option to use terminology during translation:

```powershell
bcxlftranslator input.xlf output.xlf --use-terminology
```

# Development Plan
## Phase 1 (MVP):
1. Implement terminology extraction from reference files
2. Create SQLite storage for terminology
3. Modify translation pipeline to check terminology first
4. Add source attribution in output files
5. Implement basic statistics tracking and reporting

## Testing Strategy
- Unit tests for terminology extraction logic
- Integration tests with sample XLIFF files
- Performance tests with large terminology databases
- Comparison tests between translations with/without terminology

## Future Enhancements (Post-MVP)
1. Context-awareness for terms with multiple possible translations
2. Terminology database maintenance tools
3. Handling of term variations (plurals, grammatical forms)
4. Fuzzy matching for similar terms
5. User-editable terminology database