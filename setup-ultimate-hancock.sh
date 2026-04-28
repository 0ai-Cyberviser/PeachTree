#!/bin/bash
# Ultimate Hancock Setup - Complete Automation
# Extracts full Kali system + prepares for 1000x GPU training

set -e

echo "════════════════════════════════════════════════════════════"
echo "  ULTIMATE HANCOCK PENTESTING AI AGENT SETUP"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check we're on Kali
if [ ! -f /etc/debian_version ]; then
    echo "⚠️  Warning: Not running on Debian-based system"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Extract complete Kali system
echo "📦 Step 1: Extracting complete Kali Linux system..."
echo "   This will extract:"
echo "   - Metasploit modules (~2,000)"
echo "   - Exploit-DB database (~5,000)"
echo "   - Wordlists (~50)"
echo "   - NSE scripts (~600)"
echo "   - Tool documentation (~30)"
echo "   - System configs (~8)"
echo "   - Kernel parameters (~20)"
echo "   - Custom scripts (~100)"
echo ""
echo "   Total expected: ~8,000 new records"
echo "   Time: 30-60 minutes"
echo ""
read -p "Start extraction? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Extraction skipped. You can run manually later:"
    echo "  python3 kali_complete_extraction.py"
else
    python3 kali_complete_extraction.py
    echo "✅ Extraction complete!"
fi

echo ""

# Step 2: Merge all datasets
echo "📊 Step 2: Merging all datasets..."
echo "   - Base Hancock: 4,951 records"
echo "   - Kali extraction: ~8,000 records"  
echo "   - Total: ~13,000 unique records"
echo ""
read -p "Merge datasets? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Merge skipped. You can run manually later:"
    echo "  python3 merge_all_datasets.py"
else
    python3 merge_all_datasets.py
    echo "✅ Dataset merge complete!"
fi

echo ""

# Step 3: Prepare for Colab
echo "☁️  Step 3: Preparing for Google Colab training..."
echo ""

CORPUS_FILE="data/hancock/ultimate-training-corpus.jsonl"

if [ -f "$CORPUS_FILE" ]; then
    SIZE=$(du -h "$CORPUS_FILE" | cut -f1)
    COUNT=$(wc -l < "$CORPUS_FILE")
    
    echo "📊 Ultimate Training Corpus ready:"
    echo "   File: $CORPUS_FILE"
    echo "   Size: $SIZE"
    echo "   Records: $COUNT"
    echo ""
    echo "✅ Ready for Colab upload!"
    echo ""
    echo "Next steps:"
    echo "  1. Go to: https://colab.research.google.com/"
    echo "  2. Upload: hancock_training_colab.ipynb"
    echo "  3. Set GPU: Runtime → T4 GPU"
    echo "  4. Upload this file when prompted:"
    echo "     $CORPUS_FILE"
    echo "  5. Run all cells and wait ~12-16 hours"
    echo "  6. Download: hancock-ultimate.zip"
else
    echo "⚠️  Corpus file not found: $CORPUS_FILE"
    echo "   Run merge_all_datasets.py first"
fi

echo ""

# Step 4: Installation prep
echo "💻 Step 4: Preparing boot-time installation..."
echo ""
echo "After Colab training completes, run:"
echo ""
echo "  sudo bash install-boot-agent.sh"
echo ""
echo "This will:"
echo "  - Install model to /opt/hancock"
echo "  - Set up systemd service"
echo "  - Create 'hancock' CLI command"
echo "  - Enable boot-time startup"
echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
echo "  SETUP SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ -f "$CORPUS_FILE" ]; then
    echo "✅ Local setup complete!"
    echo ""
    echo "📦 Files ready:"
    echo "   - hancock_training_colab.ipynb (Colab notebook)"
    echo "   - $CORPUS_FILE (training data)"
    echo "   - ULTIMATE-HANCOCK-SETUP.md (full guide)"
    echo ""
    echo "🚀 Next: Upload to Google Colab for 1000x training"
    echo ""
    echo "See ULTIMATE-HANCOCK-SETUP.md for complete instructions"
else
    echo "⚠️  Setup incomplete"
    echo ""
    echo "Missing: Ultimate training corpus"
    echo "Run: python3 merge_all_datasets.py"
fi

echo ""
