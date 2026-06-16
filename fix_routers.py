import os
import glob
import re

for file in glob.glob('backend/app/*/router.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace prefix="..." with empty string
    content = re.sub(r'prefix=\s*\"/[^\"]*\"\,?\s*', '', content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Done!')
