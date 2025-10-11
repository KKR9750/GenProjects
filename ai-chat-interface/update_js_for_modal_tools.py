#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JavaScript 수정: 도구 선택 버튼을 Agent 모달 안으로 이동
"""

import re

with open('pre_analysis.js', 'r', encoding='utf-8') as f:
    content = f.read()

print("[INFO] Starting JavaScript modifications...")

# 1. Remove enableAgentPanel에서 도구 버튼 활성화 코드 제거
pattern1 = r'''      // Enable tool selection button
      const selectToolsBtn = document\.getElementById\('selectToolsBtn'\);
      if \(selectToolsBtn\) \{
        selectToolsBtn\.disabled = false;
        // 이벤트 리스너 재등록.*?\n.*?\n.*?\n.*?\n      \}'''

content = re.sub(pattern1, '', content, flags=re.DOTALL)
print("[OK] Step 1: Removed old tools button code from enableAgentPanel")

# 2. updateSelectedToolsCount 함수 수정 (ID 변경)
pattern2 = r'''function updateSelectedToolsCount\(\) \{
      const selectedToolsCount = document\.getElementById\('selectedToolsCount'\);
      if \(selectedToolsCount\) \{
        selectedToolsCount\.textContent = `\$\{selectedTools\.length\}개 선택됨`;
      \}
    \}'''

replacement2 = '''function updateSelectedToolsCount() {
      const countElement = document.getElementById('selectedToolsCountModal');
      if (countElement) {
        countElement.textContent = `${selectedTools.length}개 선택됨`;
      }
      updateToolsPreview();
    }

    function updateToolsPreview() {
      const previewElement = document.getElementById('selectedToolsPreview');
      if (!previewElement) return;

      if (selectedTools.length === 0) {
        previewElement.innerHTML = '<p class="no-tools">선택된 도구 없음</p>';
        return;
      }

      const toolsHtml = selectedTools.map(toolKey => {
        const tool = availableMCPs.find(m => m.key === toolKey);
        return tool ? `<span class="tool-tag">${tool.icon} ${tool.name}</span>` : '';
      }).join('');

      previewElement.innerHTML = toolsHtml;
    }'''

content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
print("[OK] Step 2: Updated updateSelectedToolsCount and added updateToolsPreview")

# 3. initToolsModalEvents 함수 수정 (버튼 ID 변경)
pattern3 = r"const selectToolsBtn = document\.getElementById\('selectToolsBtn'\);"
replacement3 = "const selectToolsBtnModal = document.getElementById('selectToolsBtnModal');"

content = content.replace(pattern3, replacement3)
print("[OK] Step 3: Changed button ID to selectToolsBtnModal")

pattern4 = r"if \(selectToolsBtn\) \{\s+selectToolsBtn\.addEventListener\('click', openToolsModal\);"
replacement4 = "if (selectToolsBtnModal) {\n        selectToolsBtnModal.addEventListener('click', openToolsModal);"

content = re.sub(pattern4, replacement4, content)
print("[OK] Step 4: Updated event listener for modal button")

# Save
with open('pre_analysis.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n[SUCCESS] JavaScript updated successfully!")
