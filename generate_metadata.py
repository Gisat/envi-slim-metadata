#!/usr/bin/env python3
import argparse
import os
import pandas as pd
from jinja2 import Template

def main():
    parser = argparse.ArgumentParser(description="Generate XML metadata files from CSV and template.")
    parser.add_argument("directory", help="Directory containing .tif files")
    parser.add_argument("--csv", default="metadata_values.csv", help="Path to CSV with metadata values")
    parser.add_argument("--template", default="template_cog.xml", help="Path to XML Jinja2 template")
    args = parser.parse_args()

    # Load metadata CSV
    df = pd.read_csv(args.csv, dtype=str).fillna("")  # keep everything as strings, no NaN
    df_dict = {row["fileIdentifier"]: row.to_dict() for _, row in df.iterrows()}

    # Load template
    with open(args.template, encoding="utf-8") as f:
        template = Template(f.read())

    # Iterate over .tif files in the given directory
    for root, _, files in os.walk(args.directory):
        for fname in files:
            if fname.lower().endswith(".tif"):
                file_identifier = fname
                if file_identifier in df_dict:
                    data = df_dict[file_identifier]
                    xml_output = template.render(**data)

                    xml_path = os.path.join(root, f"{file_identifier}.xml")
                    with open(xml_path, "w", encoding="utf-8") as out:
                        out.write(xml_output)
                    print(f"Generated: {xml_path}")
                else:
                    print(f"No CSV entry found for {file_identifier}, skipping.")

if __name__ == "__main__":
    main()
