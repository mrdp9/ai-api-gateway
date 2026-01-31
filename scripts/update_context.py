import os
from datetime import datetime

CONTEXT_FILE = os.path.join(os.path.dirname(__file__), '../context.md')

# Template for context update
CONTEXT_TEMPLATE = '''\
## [AUTO-UPDATE] {timestamp}

### Change Summary
- {summary}

### Details
- File changed: {file}
- Description: {description}
'''

def update_context(summary, file, description):
    """Append an update to context.md with details."""
    entry = CONTEXT_TEMPLATE.format(
        timestamp=datetime.utcnow().isoformat(),
        summary=summary,
        file=file,
        description=description
    )
    with open(CONTEXT_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

# Example usage:
# update_context('Added new endpoint', 'api/main.py', 'Implemented /summarize endpoint for text summarization.')
