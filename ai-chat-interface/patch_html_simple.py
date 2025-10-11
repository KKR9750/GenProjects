import os
import re

html_path = 'd:/GenProjects/ai-chat-interface/pre_analysis.html'
addition_path = 'd:/GenProjects/ai-chat-interface/pre_analysis_ui_addition.html'
modal_path = 'd:/GenProjects/ai-chat-interface/pre_analysis_tools_modal.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

with open(addition_path, 'r', encoding='utf-8') as f:
    addition_content = f.read()

with open(modal_path, 'r', encoding='utf-8') as f:
    modal_content = f.read()

# Backup
with open(html_path + '.backup', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("[OK] Backup created")

# Insert config section
if 'agent-config-section' not in html_content:
    pattern = r'(\s*)<div class="agent-toolbar">'
    replacement = addition_content + r'\1<div class="agent-toolbar">'
    html_content = re.sub(pattern, replacement, html_content, count=1)
    print("[OK] Config section added")
else:
    print("[SKIP] Config section exists")

# Insert modal
if 'tools-modal' not in html_content:
    pattern = r'(</div>\s*</div>\s*\n\s*\n\s*<script src="pre_analysis\.js")'
    replacement = modal_content + r'\n\n\1'
    html_content = re.sub(pattern, replacement, html_content, count=1)
    print("[OK] Modal added")
else:
    print("[SKIP] Modal exists")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("[SUCCESS] HTML patched!")
