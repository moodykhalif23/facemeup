"""
Download ISIC dataset for skin analysis training.
"""

import os
import argparse
from pathlib import Path
import tensorflow_datasets as tfds


def download_isic_dataset(output_dir: str = "ml/data/isic", 
                          dataset_name: str = "isic2019",
                          download_only: bool = False):
    """
    Download ISIC dataset using TensorFlow Datasets.
    
    Args:
        output_dir: Directory to save dataset
        dataset_name: ISIC dataset version
        download_only: If True, only download without loading
    """
    
    print("="*80)
    print("DOWNLOADING ISIC DATASET")
    print("="*80)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDataset: {dataset_name}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Download dataset
        print("\nDownloading dataset...")
        print("Note: This may take a while depending on your internet connection.")
        print("The ISIC dataset is several GB in size.")
        
        if download_only:
            # Just download, don't load
            tfds.load(
                dataset_name,
                data_dir=str(output_dir),
                download=True,
                as_supervised=False
            )
        else:
            # Download and load
            dataset, info = tfds.load(
                dataset_name,
                data_dir=str(output_dir),
                with_info=True,
                as_supervised=False
            )
            
            print("\n✓ Dataset downloaded successfully!")
            print(f"\nDataset info:")
            print(f"  Name: {info.name}")
            print(f"  Version: {info.version}")
            print(f"  Description: {info.description}")
            print(f"  Features: {info.features}")
            
            if hasattr(info, 'splits'):
                print(f"\nSplits:")
                for split_name, split_info in info.splits.items():
                    print(f"  {split_name}: {split_info.num_examples} examples")
        
        print(f"\n✓ Dataset saved to: {output_dir}")
        
    except Exception as e:
        print(f"\n✗ Error downloading dataset: {e}")
        print("\nAlternative: Manual download")
        print("1. Visit: https://www.isic-archive.com/")
        print("2. Download the dataset manually")
        print(f"3. Extract to: {output_dir}")
        print("\nOr use dummy data for testing:")
        print("  The training script will automatically generate dummy data")
        print("  if the ISIC dataset is not found.")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Download ISIC dataset')
    parser.add_argument('--output', type=str, default='ml/data/isic',
                       help='Output directory for dataset')
    parser.add_argument('--dataset', type=str, default='isic2019',
                       choices=['isic2019', 'isic2018', 'isic2017'],
                       help='ISIC dataset version')
    parser.add_argument('--download-only', action='store_true',
                       help='Only download, do not load into memory')
    
    args = parser.parse_args()
    
    success = download_isic_dataset(
        args.output,
        args.dataset,
        args.download_only
    )
    
    if success:
        print("\n" + "="*80)
        print("DOWNLOAD COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Verify dataset:")
        print(f"   ls {args.output}")
        print("2. Start training:")
        print("   python ml/train.py --phase 1")
    else:
        print("\n" + "="*80)
        print("DOWNLOAD FAILED")
        print("="*80)
        print("\nYou can still proceed with training using dummy data.")
        print("The training script will generate synthetic data automatically.")


if __name__ == "__main__":
    main()
