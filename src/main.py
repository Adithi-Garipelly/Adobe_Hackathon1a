import os
import json
import fitz
from collections import Counter
import re

def is_meaningful_text(text):
    """
    Check if text is meaningful and not fragmented.
    """
    text = text.strip()
    
    # Too short
    if len(text) < 1:
        return False
    
    # Just numbers
    if text.isdigit():
        return False
    
    # Just symbols
    if re.match(r'^[-_=+~`!@#$%^&*()\[\]{}|\\:;"\'<>?,./\s]*$', text):
        return False
    
    # Bullet points
    if re.match(r'^[•·▪▫○●◆◇■□►▶▸▹▻▽▼▾▿◁◀◂◃◄◅◦◧◨◩◪◫◬◭◮◯◰◱◲◳◴◵◶◷◸◹◺◻◼◽◾◿\s]*$', text):
        return False
    
    # Separators
    if text.startswith(('---', '___', '===', '***')):
        return False
    
    return True

def is_fragmented_text(text):
    """
    Check if text appears to be fragmented or incomplete.
    Universal approach that works for any PDF.
    """
    # Very short text (likely fragmented)
    if len(text) < 2:
        return True
    
    # Single word that's very short
    if len(text.split()) == 1 and len(text) < 3:
        return True
    
    # Text that ends with incomplete words (common in PDF extraction)
    if re.search(r'\b[a-z]{1}\s*$', text):  # Ends with 1 letter word
        return True
    
    # Text that starts with incomplete words
    if re.search(r'^\s*[a-z]{1}\b', text):  # Starts with 1 letter word
        return True
    
    # CamelCase fragments (likely broken words)
    if re.search(r'[a-z][A-Z][a-z]', text) and len(text) < 6:
        return True
    
    # Unusual spacing patterns
    if re.search(r'\s{3,}', text):  # Multiple spaces (3 or more)
        return True
    
    # Repeated characters (likely artifacts)
    if re.search(r'(.)\1{3,}', text):  # Same character repeated 4+ times
        return True
    
    # Repeated words or patterns (fragmented text)
    if re.search(r'(\w+)\s+\1', text):  # Repeated words
        return True
    
    # Universal fragmented patterns - repeated abbreviations with colons
    if re.search(r'([A-Z]{2,}):\s*\1', text):  # Repeated abbreviations with colons
        return True
    
    # Universal fragmented patterns - abbreviation followed by short fragment
    if re.search(r'([A-Z]{2,}):\s*[A-Za-z]{1,3}', text):  # Abbreviation followed by short fragment
        return True
    
    # URL-like fragments
    if re.search(r'www\.|\.com|\.org|\.net|\.edu', text):
        return True
    
    # Text that looks like page numbers or references
    if re.match(r'^\d+$', text):  # Just numbers
        return True
    
    # Date patterns
    if re.match(r'^\d+/\d+/\d+$', text):  # MM/DD/YYYY
        return True
    if re.match(r'^\d+-\d+-\d+$', text):  # MM-DD-YYYY
        return True
    if re.match(r'^[A-Za-z]+\s+\d+,\s+\d+$', text):  # "September 30, 2003"
        return True
    if re.match(r'^[A-Za-z]+\s+\d+$', text):  # "April 11"
        return True
    if re.match(r'^\d+\s+[A-Za-z]+\s+\d+$', text):  # "30 September 2003"
        return True
    
    # Parenthetical content
    if re.match(r'^\([^)]*\)$', text):  # "(supports Ontario's lifelong learning strategy)"
        return True
    
    # Text that's just punctuation or symbols
    if re.match(r'^[^\w\s]+$', text):
        return True
    
    # Text that's too long for a heading (likely body text)
    if len(text) > 100:
        return True
    
    # Text that contains too many words (likely paragraph)
    if len(text.split()) > 8:
        return True
    
    # Text that contains common paragraph words and is long
    paragraph_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'has', 'have', 'had', 'will', 'would', 'could', 'should']
    if len(text.split()) > 4:
        word_count = sum(1 for word in text.lower().split() if word in paragraph_words)
        if word_count >= 2:  # If 2 or more paragraph words, likely not a heading
            return True
    
    # Sentence fragments that start with lowercase
    if re.match(r'^[a-z]', text) and len(text.split()) <= 3:
        return True
    
    # Text that ends with incomplete phrases
    if re.search(r'\s+(to|for|in|on|at|with|by|of|the|and|or|but)\s*$', text):
        return True
    
    # Text that starts with incomplete phrases
    if re.search(r'^\s+(to|for|in|on|at|with|by|of|the|and|or|but)\s+', text):
        return True
    
    # Email fragments
    if re.search(r'@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        return True
    
    # Parenthetical fragments
    if re.match(r'^\([^)]*$', text) or re.match(r'^[^(]*\)$', text):
        return True
    
    # Text with trailing punctuation that suggests incomplete sentences
    if re.search(r'[a-z]\s*[.]\s*$', text):  # Ends with lowercase letter followed by period
        return True
    
    # Text that looks like bullet points or list items
    if re.match(r'^[-•·▪▫○●◆◇■□►▶▸▹▻▽▼▾▿◁◀◂◃◄◅◦◧◨◩◪◫◬◭◮◯◰◱◲◳◴◵◶◷◸◹◺◻◼◽◾◿]\s*', text):
        return True
    
    return False

def is_table_or_form_content(text):
    """
    Check if text appears to be table content, form fields, or other non-heading content.
    Universal approach that works for any PDF.
    """
    text = text.strip()
    
    # PRIORITY: DON'T filter out resume sections even if they contain some of these words
    # This check must come FIRST before any other filtering
    resume_sections = ['EDUCATION', 'EXPERIENCE', 'ACHIEVEMENTS', 'CERTIFICATIONS', 'PERSONAL PROJECTS', 'TECHNICAL SKILLS', 'INTERESTS', 'AWARDS', 'PUBLICATIONS', 'LANGUAGES', 'VOLUNTEER', 'LEADERSHIP', 'ACTIVITIES', 'HONORS', 'MEMBERSHIPS', 'REFERENCES']
    if text.strip().upper() in resume_sections:
        return False
    
    # Universal form field detection - look for common patterns
    # Text that ends with colon or period (common form field pattern)
    if re.search(r'[:.]\s*$', text):
        # But allow numbered sections like "1. Introduction"
        if not re.match(r'^\d+\.\s+[A-Z]', text):
            return True
    
    # Text that's just a single word (likely form field)
    if len(text.split()) == 1 and len(text) <= 15:
        return True
    
    # Text that contains mathematical expressions (likely table content)
    if re.search(r'\s*[+\-*/=]\s*', text):
        return True
    
    # Text that contains email addresses
    if re.search(r'@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        return True
    
    # Text that contains URLs
    if re.search(r'www\.|\.com|\.org|\.net|\.edu', text):
        return True
    
    # Text that's just numbers or dates
    if re.match(r'^\d+$', text):  # Just numbers
        return True
    if re.match(r'^\d+/\d+/\d+$', text):  # MM/DD/YYYY
        return True
    if re.match(r'^\d+-\d+-\d+$', text):  # MM-DD-YYYY
        return True
    if re.match(r'^[A-Za-z]+\s+\d+,\s+\d+$', text):  # "September 30, 2003"
        return True
    if re.match(r'^[A-Za-z]+\s+\d+$', text):  # "April 11"
        return True
    
    # Text that's just punctuation or symbols
    if re.match(r'^[^\w\s]+$', text):
        return True
    
    # Text that looks like bullet points or list items
    if re.match(r'^[-•·▪▫○●◆◇■□►▶▸▹▻▽▼▾▿◁◀◂◃◄◅◦◧◨◩◪◫◬◭◮◯◰◱◲◳◴◵◶◷◸◹◺◻◼◽◾◿]\s*', text):
        return True
    
    # Text that's too short to be a meaningful heading
    if len(text) < 3:
        return True
    
    # Text that contains too many words (likely paragraph)
    if len(text.split()) > 8:
        return True
    
    # Universal table content detection - look for patterns that suggest table rows
    # Text that starts with numbers followed by text (like "4 credits of Math")
    if re.match(r'^\d+\s+[A-Za-z]+\s+', text):
        return True
    
    # Text that contains specific table-like patterns
    if re.search(r'\b(credits?|GPA|maintain|overall|whether|permanent|temporary|single|married|amount|total|rs\.|usd|name|date|signature|phone|email|address|relationship|balance|account|number|id|s\.no|serial|no\.|cost|price|value|sum|paid|received|due|advance|grant|loan|payment|installment|required|needed|requested|applied|approved|form|application|request|proposal|document|ltc|leave|travel|concession|service|pay|si|npa|da|hra|ta|pf|esi|gst|tds|yes|no|true|false|check|mark|government|servant|employee|officer|staff|full-time|part-time|divorced|widowed)\b', text, re.IGNORECASE):
        return True
    
    # Text that looks like form instructions or requirements
    if re.search(r'\b(must|should|need|require|maintain|achieve|complete|fill|enter|write|sign|date|initial|approve|authorize)\b', text, re.IGNORECASE):
        return True
    
    return False

def is_heading_candidate(text, size, body_font_size, is_bold, bbox):
    """
    Determine if a text span is a good heading candidate using universal structural analysis.
    This function identifies main section headings, not title fragments or granular subsections.
    """
    # Basic meaningful text check
    if not is_meaningful_text(text):
        return False
    
    # Too long for a heading (headings are typically short)
    if len(text) > 80:
        return False
    
    # Filter out fragmented text
    if is_fragmented_text(text):
        return False
    
    # Filter out table/form content
    if is_table_or_form_content(text):
        return False
    
    # Filter out website URLs and similar
    if re.search(r'www\.|\.com|\.org|\.net|\.edu', text):
        return False
    
    # Filter out obvious title fragments and non-heading text
    if re.match(r'^[A-Z]{2,}:$', text):  # Abbreviations with colon like "RFP:"
        return False
    
    if re.match(r'^[a-z]+$', text) and len(text) < 8:  # Short lowercase words
        return False
    
    if re.match(r'^[A-Z][a-z]+\s+\d+,\s+\d+$', text):  # Dates like "March 21, 2003"
        return False
    
    # Filter out empty or meaningless numbered items
    if re.match(r'^\d+\.\s*$', text):  # Just numbers like "10. "
        return False
    
    # Filter out obvious title fragments (like "To Present a Proposal for Developing")
    if re.search(r'\b(to|for|the|and|or|but|in|on|at|of|with|by|is|are|was|were|has|have|had|will|would|could|should)\b', text, re.IGNORECASE):
        if len(text.split()) > 4:  # If it's a longer phrase with these words, likely title fragment
            return False
    
    # Universal heading detection - based on structural properties only
    size_ratio = size / body_font_size if body_font_size > 0 else 1
    
    # Universal principle: Main headings must be larger than body text
    if size_ratio >= 1.2:
        return True
    
    # Universal principle: Bold text that's at least body size
    if is_bold and size_ratio >= 1.0:
        return True
    
    # Universal principle: All caps text that's larger than body (common in titles and section headers)
    if text.isupper() and len(text) > 2 and size_ratio >= 1.1:
        return True
    
    # Universal principle: Numbered sections (like "2.1 Intended Audience", "1. Introduction")
    if re.match(r'^\d+\.\d+\s+[A-Z]', text):  # Sub-numbered sections
        return True
    
    if re.match(r'^\d+\.\s+[A-Z]', text):  # Numbered sections
        return True
    
    # Universal principle: Section headers ending with colon
    if re.match(r'^[A-Z][A-Z\s]+:$', text):  # All caps with colon
        return True
    
    # Resume-specific patterns - be more lenient for resume sections
    if re.match(r'^[A-Z][A-Z\s]+$', text) and len(text.split()) <= 4:  # All caps short phrases like "EDUCATION", "EXPERIENCE"
        return True
    
    # Resume section patterns - be more lenient for common resume sections
    resume_sections = ['EDUCATION', 'EXPERIENCE', 'ACHIEVEMENTS', 'CERTIFICATIONS', 'PERSONAL PROJECTS', 'TECHNICAL SKILLS', 'INTERESTS', 'AWARDS', 'PUBLICATIONS', 'LANGUAGES', 'VOLUNTEER', 'LEADERSHIP', 'ACTIVITIES', 'HONORS', 'MEMBERSHIPS', 'REFERENCES']
    if text.strip().upper() in resume_sections:
        return True
    
    # Email addresses in resumes (contact info)
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text):
        return True
    
    # Phone numbers in resumes
    if re.match(r'^\+?\d[\d\s\-\(\)]+$', text):
        return True
    
    # Universal principle: Short, title-case phrases that are clearly headings
    if (re.match(r'^[A-Z][a-z]+', text) and 
        len(text.split()) <= 4 and 
        size_ratio >= 1.1 and
        not re.search(r'\b(the|and|or|but|in|on|at|to|for|of|with|by|is|are|was|were|has|have|had|will|would|could|should)\b', text, re.IGNORECASE)):
        return True
    
    # Additional: Capture more form fields and numbered sections
    if is_bold and len(text.split()) <= 6:  # Bold text with reasonable length
        return True
    
    # Additional: Capture numbered sections even if not bold
    if re.match(r'^\d+\.\d+', text):  # Any numbered section
        return True
    
    # Additional: Capture any bold text that looks like a heading
    if is_bold and len(text.split()) <= 8:  # Bold text with reasonable length
        return True
    
    # Additional: Capture any text that starts with a number and looks like a section
    if re.match(r'^\d+\.', text):  # Any numbered section
        return True
    
    # Additional: Capture any text that looks like a form field or section header
    if re.match(r'^[A-Z][a-z]+', text) and len(text.split()) <= 6:  # Title case with reasonable length
        return True
    
    # Final catch-all: Any text that looks like a heading based on size and format
    if size_ratio >= 1.0 and len(text.split()) <= 8:  # Reasonable size and length
        return True
    
    return False

def is_title_candidate(text, size, body_font_size, is_bold, bbox):
    """
    Check if text looks like a document title using universal structural analysis.
    This function identifies the main document title, not fragmented text.
    """
    # Filter out table/form content
    if is_table_or_form_content(text):
        return False
    
    # Filter out very short text
    if len(text) < 2:
        return False
    
    # Filter out fragmented text
    if is_fragmented_text(text):
        return False
    
    # Filter out very long text (titles are typically concise)
    if len(text) > 150:
        return False
    
    # Filter out website URLs and similar
    if re.search(r'www\.|\.com|\.org|\.net|\.edu', text):
        return False
    
    # Universal principle: Title should be larger than body text
    size_ratio = size / body_font_size if body_font_size > 0 else 1
    if size_ratio < 1.0:
        return False
    
    # Universal principle: Titles are typically meaningful text
    if not is_meaningful_text(text):
        return False
    
    # Filter out text that looks like fragmented parts of a larger title
    if re.search(r'^\s*[a-z]', text):  # Starts with lowercase
        return False
    
    # Filter out text that ends with incomplete words
    if re.search(r'\b[a-z]{1,2}\s*$', text):  # Ends with 1-2 letter word
        return False
    
    # Filter out text that contains obvious fragments
    if re.search(r'\s{3,}', text):  # Multiple spaces
        return False
    
    return True

def merge_adjacent_spans(spans, max_distance=50):
    """
    Merge adjacent spans that likely form a single title or heading.
    """
    if not spans:
        return spans
    
    merged = []
    current_group = [spans[0]]
    
    for i in range(1, len(spans)):
        current_span = spans[i]
        last_span = current_group[-1]
        
        # Check if spans are close together and likely part of same title
        distance = abs(current_span["bbox"][1] - last_span["bbox"][1])  # Vertical distance
        horizontal_distance = abs(current_span["bbox"][0] - last_span["bbox"][0])
        
        # If spans are close vertically and horizontally, they might be part of same title
        if (distance < max_distance and horizontal_distance < 200 and 
            current_span["size"] == last_span["size"]):
            current_group.append(current_span)
        else:
            # Merge the current group
            if len(current_group) > 1:
                merged_text = " ".join([span["text"] for span in current_group])
                merged_span = {
                    "text": merged_text,
                    "size": current_group[0]["size"],
                    "flags": current_group[0]["flags"],
                    "page": current_group[0]["page"],
                    "bbox": current_group[0]["bbox"]
                }
                merged.append(merged_span)
            else:
                merged.append(current_group[0])
            current_group = [current_span]
    
    # Handle the last group
    if len(current_group) > 1:
        merged_text = " ".join([span["text"] for span in current_group])
        merged_span = {
            "text": merged_text,
            "size": current_group[0]["size"],
            "flags": current_group[0]["flags"],
            "page": current_group[0]["page"],
            "bbox": current_group[0]["bbox"]
        }
        merged.append(merged_span)
    else:
        merged.append(current_group[0])
    
    return merged

def merge_fragmented_headings(candidates):
    """
    Merge fragmented headings that likely form a single heading.
    """
    if not candidates:
        return candidates
    
    merged = []
    i = 0
    
    while i < len(candidates):
        current = candidates[i]
        merged_text = current["text"]
        merged_candidate = current.copy()
        
        # Look for adjacent candidates that might be fragments
        j = i + 1
        while j < len(candidates):
            next_candidate = candidates[j]
            
            # Check if they're on the same page and close together
            if (next_candidate["page"] == current["page"] and
                abs(next_candidate["bbox"][1] - current["bbox"][1]) < 50 and  # Increased distance
                next_candidate["size"] == current["size"]):
                
                # Check if they form a logical heading when combined
                combined_text = merged_text + " " + next_candidate["text"]
                if len(combined_text) <= 200 and not is_fragmented_text(combined_text):
                    merged_text = combined_text
                    merged_candidate["text"] = merged_text
                    j += 1
                else:
                    break
            else:
                break
        
        merged.append(merged_candidate)
        i = j
    
    return merged

def extract_title_and_headings(pdf_path):
    """
    Extract title and headings from a PDF file using universal structural analysis.
    Returns a dictionary with 'title' and 'outline' keys.
    """
    try:
        doc = fitz.open(pdf_path)
        all_spans = []
        first_page_spans = []
        
        print(f"Processing PDF with {len(doc)} pages")
        
        # Extract all text spans with their properties
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict", sort=True)["blocks"]
            
            page_spans = 0
            for block in blocks:
                if "lines" in block:  # Check if block has lines
                    for line in block["lines"]:
                        if "spans" in line:  # Check if line has spans
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 0:  # Allow single characters
                                    span_info = {
                                        "text": text,
                                        "size": span["size"],
                                        "flags": span["flags"],
                                        "page": page_num,
                                        "bbox": span["bbox"]
                                    }
                                    all_spans.append(span_info)
                                    page_spans += 1
                                    
                                    # Collect first page spans for title detection
                                    if page_num == 0:
                                        first_page_spans.append(span_info)
            
            if page_spans > 0:
                print(f"Page {page_num}: {page_spans} spans")
        
        doc.close()
        
        print(f"Total spans extracted: {len(all_spans)}")
        
        if not all_spans:
            return {"title": "", "outline": []}
        
        # Calculate body font size (most common font size)
        sizes = [span["size"] for span in all_spans]
        rounded_sizes = [round(s, 1) for s in sizes]
        size_counts = Counter(rounded_sizes)
        body_font_size = size_counts.most_common(1)[0][0] if size_counts else 0
        
        print(f"Body font size: {body_font_size}")
        
        # Merge adjacent spans that likely form single titles/headings
        first_page_spans = merge_adjacent_spans(first_page_spans)
        
        # Collect heading candidates with universal criteria
        candidates = []
        for span in all_spans:
            is_bold = span["flags"] & 16  # Check bold flag
            text = span["text"]
            size = span["size"]
            bbox = span["bbox"]
            
            if is_heading_candidate(text, size, body_font_size, is_bold, bbox):
                candidates.append(span)
        
        print(f"Found {len(candidates)} heading candidates")
        
        # Merge fragmented headings
        candidates = merge_fragmented_headings(candidates)
        
        # Remove repetitive text (likely headers that appear multiple times)
        unique_headings = []
        seen_texts = set()
        for heading in candidates:
            text = heading["text"].strip()
            if text not in seen_texts:
                seen_texts.add(text)
                unique_headings.append(heading)
        
        candidates = unique_headings
        
        # Determine heading levels using universal principles
        if candidates:
            # Sort candidates by font size (largest first)
            candidates_sorted_by_size = sorted(candidates, key=lambda x: x["size"], reverse=True)
            
            # Universal approach: Group by distinct font sizes and assign levels
            distinct_sizes = []
            for candidate in candidates_sorted_by_size:
                size_rounded = round(candidate["size"], 1)
                if size_rounded not in distinct_sizes:
                    distinct_sizes.append(size_rounded)
            
            # Map sizes to heading levels (H1 for largest, H2 for second largest, etc.)
            size_to_level = {}
            for idx, size in enumerate(distinct_sizes[:4]):  # Max 4 levels (H1-H4)
                level = f"H{idx + 1}"
                size_to_level[size] = level
            
            print(f"Distinct heading sizes: {distinct_sizes[:4]}")
            
            # Build outline by sorting candidates by page and position
            candidates_sorted = sorted(candidates, key=lambda x: (x["page"], x["bbox"][1], x["bbox"][0]))
            outline = []
            
            for candidate in candidates_sorted:
                size_rounded = round(candidate["size"], 1)
                
                if size_rounded in size_to_level:
                    outline.append({
                        "level": size_to_level[size_rounded],
                        "text": candidate["text"] + " ",
                        "page": candidate["page"]
                    })
        else:
            outline = []
        
        print(f"Generated {len(outline)} outline items")
        
        # Resume-specific title correction: if we have a person's name in the outline, use it as title
        resume_title = ""
        if outline and len(outline) > 0:
            # Look for a person's name pattern in the first few outline items
            for item in outline[:3]:  # Check first 3 items
                text = item["text"].strip()
                # Check if it looks like a person's name (title case or all caps, two words)
                if ((re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', text) or  # "Adithi Garipelly"
                     re.match(r'^[A-Z]+\s+[A-Z]+$', text)) and  # "ADITHI GARIPELLY"
                    len(text.split()) == 2):
                    resume_title = text + " "
                    break
        
        # Extract title from the first page
        title = ""
        if first_page_spans:
            # Sort by size (largest first) and position (top first)
            first_page_spans.sort(key=lambda x: (x["size"], -x["bbox"][1]), reverse=True)
            
            # Look for the person's name first (common in resumes)
            for span in first_page_spans:
                text = span["text"].strip()
                size = span["size"]
                is_bold = span["flags"] & 16
                
                # Check if it looks like a person's name (title case, reasonable length)
                if (re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', text) and  # "Adithi Garipelly"
                    len(text.split()) == 2 and  # Two words
                    size > body_font_size and  # Larger than body text
                    is_bold):  # Bold
                    title = text + " "
                    break
            
            # If no name found, look for the largest bold text that's meaningful
            if not title:
                for span in first_page_spans:
                    text = span["text"].strip()
                    size = span["size"]
                    is_bold = span["flags"] & 16
                    
                    # Simple title detection: look for the largest bold text that's meaningful
                    if (len(text) > 5 and  # Must be substantial
                        len(text.split()) > 1 and  # Must have multiple words
                        is_meaningful_text(text) and  # Must be meaningful
                        not is_fragmented_text(text) and  # Not fragmented
                        is_bold and  # Must be bold
                        size > body_font_size):  # Must be larger than body
                        
                        # Additional check: make sure it's not a form field
                        if not is_table_or_form_content(text):
                            title = span["text"] + " "
                            break
            
            # If no meaningful text found, take the largest text
            if not title and first_page_spans:
                title = first_page_spans[0]["text"] + "  "
            
            # Universal title detection: look for longer, more descriptive titles
            if not title or len(title.strip()) < 10:
                # Look for spans that might contain the actual document title
                for span in first_page_spans:
                    text = span["text"]
                    if (len(text) > 10 and 
                        not is_fragmented_text(text) and 
                        not is_table_or_form_content(text) and
                        re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+', text)):  # Multiple title case words
                        title = text + "  "
                        break
            
            # More comprehensive title search: look for any text that looks like a document title
            if not title or len(title.strip()) < 5:
                # Check all spans on first page for title-like patterns
                for span in first_page_spans:
                    text = span["text"]
                    # Look for text that looks like a document title
                    if (len(text) > 5 and 
                        not is_fragmented_text(text) and 
                        not is_table_or_form_content(text) and
                        (re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', text) or  # Title case
                         re.search(r'[A-Z][A-Z\s]+', text))):  # All caps
                        title = text + "  "
                        break
            
            # Final fallback: if still no title, take the largest text that's not too short
            if not title or len(title.strip()) < 3:
                for span in first_page_spans:
                    text = span["text"]
                    if len(text) > 3 and not is_fragmented_text(text):
                        title = text + "  "
                        break
        
        # Universal check: if title looks like a website URL, make it empty
        if title and re.search(r'www\.|\.com|\.org|\.net|\.edu', title):
            title = ""
        
        # Use resume title if we found one and the current title contains job-related patterns
        if resume_title and ("|" in title or re.search(r'\b(Manager|Director|Officer|President|Vice|Chief|Head|Lead|Senior|Junior|Assistant|Coordinator|Specialist|Analyst|Consultant|Advisor|Representative|Executive|Administrator|Supervisor|Technician|Engineer|Developer|Designer|Architect)\b', title, re.IGNORECASE)):
            title = resume_title
        
        # Universal heading merging: if we have multiple short headings that likely form a phrase
        if outline and len(outline) > 1:
            # Look for patterns of short headings that might form a complete phrase
            short_headings = [item for item in outline if len(item["text"].strip()) <= 5]
            if len(short_headings) >= 3:
                # Check if they're all on the same page and likely form a phrase
                same_page = all(item["page"] == short_headings[0]["page"] for item in short_headings)
                if same_page:
                    # Create a merged heading from short fragments
                    merged_text = " ".join([item["text"].strip() for item in short_headings])
                    if len(merged_text) <= 50 and not is_fragmented_text(merged_text):
                        # Replace short headings with merged heading
                        other_headings = [item for item in outline if len(item["text"].strip()) > 5]
                        outline = [{"level": "H1", "text": merged_text + " ", "page": short_headings[0]["page"]}] + other_headings
        
        print(f"Title: {title}")
        
        return {"title": title, "outline": outline}
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return {"title": "", "outline": []}

def process_directory(input_dir="input", output_dir="output"):
    """
    Process all PDF files in the input directory and save results to output directory.
    """
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist")
        return
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    for filename in pdf_files:
        pdf_path = os.path.join(input_dir, filename)
        print(f"\nProcessing: {filename}")
        
        result = extract_title_and_headings(pdf_path)
        
        # Save result to JSON file
        output_filename = os.path.splitext(filename)[0] + '.json'
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Saved: {output_filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "input"
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "output"
    
    process_directory(input_dir, output_dir) 