# PDF Heading Extractor

A lightweight solution for extracting titles and headings (H1, H2, H3) from PDF documents using PyMuPDF.

## Features

- **Fast Processing**: Processes 50-page PDFs in under 10 seconds
- **Lightweight**: Uses only PyMuPDF library (< 200MB total)
- **Offline**: No network calls required
- **Accurate**: Intelligent heading detection using font size and bold text analysis
- **Docker Ready**: Containerized solution for easy deployment

## How It Works

The solution uses a sophisticated algorithm to detect headings:

1. **Text Extraction**: Extracts all text spans with their properties (font size, bold flags, position)
2. **Body Font Detection**: Identifies the most common font size as the body text baseline
3. **Heading Candidates**: Identifies potential headings using:
   - Font size ≥ 1.2x body font size, OR
   - Bold text with reasonable font size
4. **Heading Levels**: Clusters font sizes into 3 levels (H1, H2, H3)
5. **Title Detection**: Extracts the largest text from the first page as the document title
6. **Output**: Generates structured JSON with title and outline

## Requirements

- Docker
- PDF files to process

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd solution
   ```

2. **Add PDF files to the input directory**
   ```bash
   mkdir -p input output
   # Copy your PDF files to the input/ directory
   ```

3. **Build and run**
   ```bash
   ./build_and_run.sh
   ```

4. **Check results**
   ```bash
   ls output/
   # JSON files will be generated for each PDF
   ```

## Output Format

Each PDF generates a JSON file with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Main Heading",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "Sub Heading",
      "page": 2
    }
  ]
}
```

## Algorithm Details

### Heading Detection Criteria
- **Font Size Analysis**: Text with font size ≥ 1.2x body font size
- **Bold Text Detection**: Uses PDF flags to identify bold text
- **Position Awareness**: Considers text position for title extraction

### Heading Level Assignment
- **H1**: Largest distinct font size among candidates
- **H2**: Second largest distinct font size
- **H3**: Third largest distinct font size

### Title Extraction
- Prioritizes heading candidates on the first page
- Falls back to largest text if no candidates found
- Considers both font size and position (top-left priority)

## Performance

- **Speed**: < 10 seconds for 50-page PDFs
- **Memory**: < 200MB total footprint
- **Accuracy**: High precision heading detection
- **Scalability**: Processes multiple PDFs efficiently

## Docker Configuration

The solution runs in a containerized environment with:
- **Platform**: linux/amd64
- **Base Image**: python:3.9-slim
- **Network**: Disabled (--network none)
- **Volumes**: Input/output directories mounted

## Error Handling

- Graceful handling of corrupted PDFs
- Fallback to empty results for unreadable files
- Comprehensive logging for debugging

## Competition Compliance

✅ **Time Constraint**: < 10 seconds for 50 pages  
✅ **Memory Constraint**: < 200MB total  
✅ **Offline Operation**: No network calls  
✅ **Output Format**: Exact JSON structure  
✅ **Docker Ready**: Containerized solution  

## Testing

Test with sample PDFs:
```bash
# Add test PDFs to input/ directory
./build_and_run.sh
# Check output/ directory for results
```

## License

This project is created for the Adobe Hackathon competition.
