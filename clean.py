"""
Clean Generated Files - Remove all output files from research/podcast runs
"""

import os
import glob
from pathlib import Path


def find_generated_files():
    """Find all generated files matching patterns"""
    patterns = [
        'arxiv_results_*.json',
        'arxiv_top5_links_*.json',
        'podcast_script_*.md',
        '*_metadata.json'
    ]
    
    files_to_delete = []
    
    for pattern in patterns:
        matches = glob.glob(pattern)
        files_to_delete.extend(matches)
    
    return sorted(files_to_delete)


def format_size(size_bytes):
    """Format bytes into human-readable size"""
    size = float(size_bytes)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} TB"


def get_file_size(filepath):
    """Get human-readable file size for a file"""
    size = os.path.getsize(filepath)
    return format_size(size)


def clean_files(confirm=True):
    """
    Delete all generated files
    
    Args:
        confirm: If True, ask for confirmation before deleting
    """
    print('\n🧹 CLEAN GENERATED FILES')
    print('=' * 80)
    
    files = find_generated_files()
    
    if not files:
        print('\n✨ No generated files found. Directory is already clean!')
        return
    
    # Show what will be deleted
    print(f'\n📋 Found {len(files)} generated file(s):\n')
    
    total_size = 0
    for idx, file in enumerate(files, 1):
        size = os.path.getsize(file)
        total_size += size
        print(f'   {idx}. {file} ({get_file_size(file)})')
    
    print(f'\n📊 Total size: {format_size(total_size)}')
    
    # Ask for confirmation
    if confirm:
        print('\n⚠️  This will permanently delete these files!')
        response = input('   Continue? (y/N): ').strip().lower()
        
        if response not in ['y', 'yes']:
            print('\n❌ Cleanup cancelled.')
            return
    
    # Delete files
    print('\n🗑️  Deleting files...\n')
    
    deleted_count = 0
    error_count = 0
    
    for file in files:
        try:
            os.remove(file)
            print(f'   ✅ Deleted: {file}')
            deleted_count += 1
        except Exception as error:
            print(f'   ❌ Error deleting {file}: {error}')
            error_count += 1
    
    # Summary
    print('\n' + '=' * 80)
    print(f'✅ Cleanup complete!')
    print(f'   Deleted: {deleted_count} file(s)')
    if error_count > 0:
        print(f'   Errors: {error_count} file(s)')
    print('=' * 80 + '\n')


def list_files_only():
    """Just list the files without deleting"""
    print('\n📋 GENERATED FILES LIST')
    print('=' * 80)
    
    files = find_generated_files()
    
    if not files:
        print('\n✨ No generated files found.')
        return
    
    print(f'\n📄 Found {len(files)} generated file(s):\n')
    
    # Group by type
    by_type = {
        'arXiv Results': [],
        'Top 5 Links': [],
        'Podcast Scripts': [],
        'Metadata': []
    }
    
    for file in files:
        if file.startswith('arxiv_results_'):
            by_type['arXiv Results'].append(file)
        elif file.startswith('arxiv_top5_links_'):
            by_type['Top 5 Links'].append(file)
        elif file.startswith('podcast_script_'):
            by_type['Podcast Scripts'].append(file)
        elif file.endswith('_metadata.json'):
            by_type['Metadata'].append(file)
    
    for category, items in by_type.items():
        if items:
            print(f'\n📂 {category} ({len(items)}):')
            for item in items:
                print(f'   • {item} ({get_file_size(item)})')
    
    total_size = sum(os.path.getsize(f) for f in files)
    print(f'\n📊 Total size: {format_size(total_size)}')
    print('=' * 80 + '\n')


if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--list', '-l', 'list']:
            # Just list files
            list_files_only()
        
        elif arg in ['--force', '-f', 'force']:
            # Delete without confirmation
            clean_files(confirm=False)
        
        elif arg in ['--help', '-h', 'help']:
            # Show help
            print('\n🧹 Clean Generated Files Script')
            print('=' * 80)
            print('\nUsage:')
            print('  python clean.py              # Delete with confirmation prompt')
            print('  python clean.py --list       # List files without deleting')
            print('  python clean.py --force      # Delete without confirmation')
            print('  python clean.py --help       # Show this help\n')
            print('Patterns cleaned:')
            print('  • arxiv_results_*.json')
            print('  • arxiv_top5_links_*.json')
            print('  • podcast_script_*.md')
            print('  • *_metadata.json\n')
        
        else:
            print(f'\n❌ Unknown option: {arg}')
            print('   Use --help to see available options\n')
    
    else:
        # Default: delete with confirmation
        clean_files(confirm=True)
