#!/usr/bin/env python3
"""
Download skin dataset for training.
Uses HAM10000 dataset (publicly available dermatoscopic images)
"""

import os
import urllib.request
import zipfile
from pathlib import Path
import shutil

def download_ham10000():
    """
    Download HAM10000 dataset - 10,000 dermatoscopic images
    This is a publicly available dataset for skin lesion classification
    """
    
    print("=" * 80)
    print("DOWNLOADING HAM10000 SKIN DATASET")
    print("=" * 80)
    print("\nDataset: HAM10000 (Human Against Machine with 10000 training images)")
    print("Source: Harvard Dataverse")
    print("Size: ~2GB")
    print("Images: 10,015 dermatoscopic images")
    
    output_dir = Path("ml/data/ham10000")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Dataset URLs (Harvard Dataverse)
    urls = {
        "images_part1": "https://dataverse.harvard.edu/api/access/datafile/3289452",
        "images_part2": "https://dataverse.harvard.edu/api/access/datafile/3289453",
        "metadata": "https://dataverse.harvard.edu/api/access/datafile/3289454"
    }
    
    try:
        # Download metadata
        print("\n[1/3] Downloading metadata...")
        metadata_path = output_dir / "HAM10000_metadata.csv"
        if not metadata_path.exists():
            urllib.request.urlretrieve(urls["metadata"], metadata_path)
            print(f"  ✓ Saved to: {metadata_path}")
        else:
            print(f"  ✓ Already exists: {metadata_path}")
        
        # Download images part 1
        print("\n[2/3] Downloading images (Part 1/2)...")
        part1_zip = output_dir / "HAM10000_images_part_1.zip"
        if not part1_zip.exists():
            print("  This may take 10-15 minutes...")
            urllib.request.urlretrieve(urls["images_part1"], part1_zip)
            print(f"  ✓ Downloaded: {part1_zip}")
            
            # Extract
            print("  Extracting...")
            with zipfile.ZipFile(part1_zip, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            print("  ✓ Extracted")
        else:
            print(f"  ✓ Already exists: {part1_zip}")
        
        # Download images part 2
        print("\n[3/3] Downloading images (Part 2/2)...")
        part2_zip = output_dir / "HAM10000_images_part_2.zip"
        if not part2_zip.exists():
            print("  This may take 10-15 minutes...")
            urllib.request.urlretrieve(urls["images_part2"], part2_zip)
            print(f"  ✓ Downloaded: {part2_zip}")
            
            # Extract
            print("  Extracting...")
            with zipfile.ZipFile(part2_zip, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            print("  ✓ Extracted")
        else:
            print(f"  ✓ Already exists: {part2_zip}")
        
        # Count images
        image_dirs = list(output_dir.glob("HAM10000_images_part_*"))
        total_images = sum(len(list(d.glob("*.jpg"))) for d in image_dirs if d.is_dir())
        
        print("\n" + "=" * 80)
        print("DOWNLOAD COMPLETE!")
        print("=" * 80)
        print(f"\n✓ Dataset saved to: {output_dir}")
        print(f"✓ Total images: {total_images}")
        print(f"✓ Metadata: {metadata_path}")
        
        print("\nNext steps:")
        print("1. Start training:")
        print("   python ml/train.py --phase 1")
        print("2. Monitor progress:")
        print("   tensorboard --logdir ml/logs")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nAlternative: Use dummy data for testing")
        print("The training script will automatically generate synthetic data.")
        return False


if __name__ == "__main__":
    download_ham10000()
