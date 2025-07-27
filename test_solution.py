#!/usr/bin/env python3
"""
Test script to validate the PDF heading extraction solution.
"""

import os
import json
import subprocess
import sys

def test_solution():
    """Test the solution with sample PDFs."""
    
    print("🧪 Testing PDF Heading Extractor Solution")
    print("=" * 50)
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not available. Please install Docker first.")
        return False
    
    # Check if input directory has PDFs
    input_dir = "input"
    if not os.path.exists(input_dir):
        print(f"❌ Input directory '{input_dir}' does not exist")
        return False
    
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"❌ No PDF files found in '{input_dir}'")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF files to test")
    
    # Build and run the solution
    print("\n🔨 Building Docker image...")
    try:
        subprocess.run(["./build_and_run.sh"], check=True)
        print("✅ Solution built and executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build/run solution: {e}")
        return False
    
    # Check output files
    output_dir = "output"
    if not os.path.exists(output_dir):
        print(f"❌ Output directory '{output_dir}' does not exist")
        return False
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print(f"❌ No JSON output files found in '{output_dir}'")
        return False
    
    print(f"✅ Generated {len(json_files)} JSON output files")
    
    # Validate output format
    print("\n📋 Validating output format...")
    for json_file in json_files:
        json_path = os.path.join(output_dir, json_file)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            if "title" not in data:
                print(f"❌ {json_file}: Missing 'title' field")
                continue
            if "outline" not in data:
                print(f"❌ {json_file}: Missing 'outline' field")
                continue
            
            # Check outline structure
            outline = data["outline"]
            if not isinstance(outline, list):
                print(f"❌ {json_file}: 'outline' is not a list")
                continue
            
            # Check each outline item
            for i, item in enumerate(outline):
                if not isinstance(item, dict):
                    print(f"❌ {json_file}: Outline item {i} is not a dictionary")
                    continue
                
                required_fields = ["level", "text", "page"]
                for field in required_fields:
                    if field not in item:
                        print(f"❌ {json_file}: Outline item {i} missing '{field}' field")
                        break
                else:
                    # Check level format
                    if not item["level"].startswith("H") or item["level"][1:] not in ["1", "2", "3"]:
                        print(f"❌ {json_file}: Invalid level '{item['level']}' in item {i}")
                        continue
                    
                    # Check page number
                    if not isinstance(item["page"], int) or item["page"] < 1:
                        print(f"❌ {json_file}: Invalid page number {item['page']} in item {i}")
                        continue
            
            print(f"✅ {json_file}: Valid format")
            
        except json.JSONDecodeError as e:
            print(f"❌ {json_file}: Invalid JSON format - {e}")
        except Exception as e:
            print(f"❌ {json_file}: Error reading file - {e}")
    
    print("\n🎉 Testing completed successfully!")
    return True

def show_sample_output():
    """Show a sample of the output."""
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("No output directory found")
        return
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print("No JSON files found")
        return
    
    # Show first JSON file as example
    sample_file = json_files[0]
    sample_path = os.path.join(output_dir, sample_file)
    
    print(f"\n📄 Sample output from {sample_file}:")
    print("-" * 40)
    
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Title: {data.get('title', 'N/A')}")
        print(f"Number of headings: {len(data.get('outline', []))}")
        
        if data.get('outline'):
            print("\nFirst few headings:")
            for i, item in enumerate(data['outline'][:5]):
                print(f"  {item['level']}: {item['text']} (Page {item['page']})")
            
            if len(data['outline']) > 5:
                print(f"  ... and {len(data['outline']) - 5} more headings")
    
    except Exception as e:
        print(f"Error reading sample file: {e}")

if __name__ == "__main__":
    success = test_solution()
    if success:
        show_sample_output()
    else:
        sys.exit(1) 