#!/usr/bin/env bash
set -euo pipefail

# 安装 Trae Skills 软链接脚本
# 作用：将当前目录下的所有子文件夹（代表各个 skill）通过相对路径软链接到 .trae/skills/ 目录下

# 获取脚本所在目录的绝对路径，确保在任何地方执行该脚本都有效
SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SKILLS_DIR")"
TRAE_SKILLS_DIR="$PROJECT_ROOT/.trae/skills"

echo "========================================"
echo "🚀 开始安装 Trae Skills..."
echo "========================================"

# 检查目标目录是否存在，不存在则创建
if [ ! -d "$TRAE_SKILLS_DIR" ]; then
    echo "📁 创建目标目录: $TRAE_SKILLS_DIR"
    mkdir -p "$TRAE_SKILLS_DIR"
fi

for existing_link in "$TRAE_SKILLS_DIR"/*; do
    [ -L "$existing_link" ] || continue
    existing_name=$(basename "$existing_link")
    if [ ! -d "$SKILLS_DIR/$existing_name" ]; then
        echo "🧹 清理无效链接: $existing_name"
        rm -rf "$existing_link"
    fi
done

# 遍历 skills 目录下的所有子目录
count=0
for skill_path in "$SKILLS_DIR"/*/; do
    # 如果目录下没有任何子文件夹，遍历会返回原字符串，需做判断
    if [ ! -d "$skill_path" ]; then
        continue
    fi
    
    # 提取 skill 目录名称 (如: hugo-frontmatter-generator)
    skill_name=$(basename "$skill_path")
    
    # 目标软链接的绝对路径
    target_link="$TRAE_SKILLS_DIR/$skill_name"
    
    # 如果目标已经存在（无论是文件、目录还是旧的软链接），先将其删除
    if [ -e "$target_link" ] || [ -L "$target_link" ]; then
        echo "🔄 更新现有链接: $skill_name"
        rm -rf "$target_link"
    else
        echo "🔗 创建全新链接: $skill_name"
    fi
    
    # 执行软链接操作
    # 注意这里使用相对路径：从 .trae/skills/ 出发，退回两层到项目根目录，再进入 skills/ 目录
    # 这样可以保证即使整个项目被移动到其他电脑，软链接依然有效
    ln -s "../../skills/$skill_name" "$target_link"
    
    count=$((count + 1))
done

echo "========================================"
echo "✅ 安装完成！共成功链接 $count 个 Skill。"
echo "请在 Trae 中重新加载或测试这些 Skill。"
echo "========================================"
