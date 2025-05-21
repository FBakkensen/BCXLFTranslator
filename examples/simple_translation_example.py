"""
Simple example script demonstrating how to use BCXLFTranslator to translate an XLIFF file.

This script creates a sample XLIFF file, translates it, and displays the results.
It can be used to verify that the translation functionality is working correctly.

Usage:
    python -m examples.simple_translation_example
"""
import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.main import translate_xliff

# Create a simple XLIFF file
xliff_content = """<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
      <trans-unit id="test2">
        <source>This is a test</source>
        <target></target>
      </trans-unit>
      <trans-unit id="test3">
        <source>Business Central</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>
"""

async def main():
    # Create temporary input and output files in the examples directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "example_input.xlf")
    output_file = os.path.join(script_dir, "example_output.xlf")
    
    try:
        print("BCXLFTranslator Simple Example")
        print("=============================")
        print("This example demonstrates the translation of a simple XLIFF file.")
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        print("\nCreating sample XLIFF file...")
        
        # Write the test XLIFF to the input file
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(xliff_content)
        
        print("Translating file...")
        # Run the translation
        stats = await translate_xliff(input_file, output_file)
        
        # Print the statistics
        print(f"\nTranslation statistics:")
        print(f"Total translations: {stats.total_count}")
        print(f"Google Translate: {stats.google_translate_count} ({stats.google_translate_percentage:.1f}%)")
        
        # Print the translated content
        print("\nTranslated content:")
        with open(output_file, "r", encoding="utf-8") as f:
            print(f.read())
        
        print("\nExample completed successfully!")
        print(f"The translated file has been saved to: {output_file}")
        print("You can examine this file to see the translation results.")
        print("The example files will be deleted when you press Enter.")
        input("Press Enter to clean up and exit...")
            
    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
            print(f"Removed {input_file}")
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Removed {output_file}")
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
