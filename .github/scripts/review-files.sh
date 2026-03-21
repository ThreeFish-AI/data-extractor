#!/usr/bin/env bash
# 审查变更文件的共享脚本
# 用法: review-files.sh <changed_files_list> <diff_base> <diff_head> <output_file>
#   changed_files_list: 变更文件列表文件路径
#   diff_base:          diff 基准 (branch 或 commit SHA)
#   diff_head:          diff 目标 (branch 或 commit SHA)
#   output_file:        审查结果输出文件路径

set -euo pipefail

CHANGED_FILES="$1"
DIFF_BASE="$2"
DIFF_HEAD="$3"
OUTPUT_FILE="$4"
PROMPT_FILE="$(dirname "$0")/../review-prompt.txt"

> "$OUTPUT_FILE"

while IFS= read -r file; do
  if [ -z "$file" ] || [ ! -f "$file" ]; then
    continue
  fi

  {
    echo ""
    echo "========================================"
    echo "Reviewing file: $file"
    echo "========================================"
    echo ""
  } >> "$OUTPUT_FILE"

  DIFF_TMP=$(mktemp)
  REQUEST_TMP=$(mktemp)

  # 获取文件变更差异
  if ! git diff "$DIFF_BASE" "$DIFF_HEAD" -- "$file" > "$DIFF_TMP" 2>/dev/null; then
    echo "Failed to get diff for file: $file" >> "$OUTPUT_FILE"
    rm -f "$DIFF_TMP" "$REQUEST_TMP"
    continue
  fi

  # 构建审查请求
  {
    echo "文件: $file"
    echo ""
    echo "变更内容:"
    echo '```diff'
    cat "$DIFF_TMP"
    echo '```'
    echo ""
    cat "$PROMPT_FILE"
  } > "$REQUEST_TMP"

  # 运行 Claude Code 审查
  cat "$REQUEST_TMP" | npx @anthropic-ai/claude-code review --model=opus --agent=code-reviewer >> "$OUTPUT_FILE"

  # 清理临时文件
  rm -f "$DIFF_TMP" "$REQUEST_TMP"

  echo "" >> "$OUTPUT_FILE"
done < "$CHANGED_FILES"
