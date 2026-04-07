#!/usr/bin/env bash
set -euo pipefail

# 通用 Skills 软链接安装脚本
# 作用：将当前目录下的所有 skill 目录以软链接方式安装到常用 agent 的 skills 目录中

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
declare -a TARGET_NAMES=()
declare -a TARGET_DIRS=()
declare -a REQUESTED_TARGET_NAMES=()
declare -a DETECTED_TARGET_NAMES=()
BUILTIN_TARGETS=("trae" "trae-cn" "openclaw" "opencode" "claude-code" "codex" "vscode")

usage() {
    cat <<EOF
用法:
  $(basename "$0")
    $(basename "$0") --detect
  $(basename "$0") --all
    $(basename "$0") trae claude-code opencode
  $(basename "$0") --target claude-code=/path/to/skills --target openclaw=/path/to/skills

说明:
        - 不带参数时，默认进入检测模式，只安装本机已存在目录的内置目标。
        - --detect 显式启用检测模式。
        - 内置目标: trae、trae-cn、openclaw、opencode、claude-code、codex、vscode。
    - 内置目标使用各工具的默认用户目录；如需跨仓库或自定义位置，请使用 --target name=dir（支持相对路径和绝对路径）。
    - --all 会安装所有内置目标以及通过 --target 追加的目标。
  - --target name=dir 可临时追加安装目标。
    - 在 Windows 上需要系统支持符号链接；若失败，请以管理员权限运行终端或开启 Developer Mode。
EOF
}

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

resolve_dir() {
    local path="$1"

    if [[ "$path" == ~* ]]; then
        path="${HOME}${path#\~}"
    fi

    if [[ "$path" != /* ]]; then
        path="$PWD/$path"
    fi

    printf '%s' "$path"
}

platform_name() {
    case "$(uname -s)" in
        Darwin)
            printf '%s' "macos"
            ;;
        Linux)
            printf '%s' "linux"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            printf '%s' "windows"
            ;;
        *)
            printf '%s' "unknown"
            ;;
    esac
}

windows_path_to_posix() {
    local input_path="$1"

    if [ -z "$input_path" ]; then
        return 1
    fi

    if command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$input_path"
        return 0
    fi

    printf '%s' "$input_path" | sed 's#\\#/#g'
}

vscode_user_dir() {
    local platform
    platform="$(platform_name)"

    case "$platform" in
        macos)
            printf '%s' "$HOME/Library/Application Support/Code/User"
            ;;
        linux)
            printf '%s' "${XDG_CONFIG_HOME:-$HOME/.config}/Code/User"
            ;;
        windows)
            if [ -n "${APPDATA:-}" ]; then
                printf '%s' "$(windows_path_to_posix "$APPDATA")/Code/User"
            else
                printf '%s' "$HOME/AppData/Roaming/Code/User"
            fi
            ;;
        *)
            printf '%s' "$HOME/.vscode"
            ;;
    esac
}

builtin_target_dir() {
    local name="$1"

    case "$name" in
        trae)
            printf '%s' "$HOME/.trae/skills"
            ;;
        trae-cn)
            printf '%s' "$HOME/.traecn/skills"
            ;;
        openclaw)
            printf '%s' "$HOME/.openclaw/workspace/skills"
            ;;
        opencode)
            printf '%s' "$HOME/.opencode/skills"
            ;;
        claude-code)
            printf '%s' "$HOME/.claude/skills"
            ;;
        codex)
            printf '%s' "$HOME/.codex/skills"
            ;;
        vscode)
            printf '%s' "$(vscode_user_dir)/skills"
            ;;
        *)
            return 1
            ;;
    esac
}

relative_path() {
    local from_dir="$1"
    local to_path="$2"

    if command -v python3 >/dev/null 2>&1; then
        python3 - "$from_dir" "$to_path" <<'PY'
import os
import sys

print(os.path.relpath(sys.argv[2], sys.argv[1]))
PY
        return
    fi

    perl -MCwd=abs_path -MFile::Spec -e '
        my ($from_dir, $to_path) = @ARGV;
        print File::Spec->abs2rel(abs_path($to_path), abs_path($from_dir));
    ' "$from_dir" "$to_path"
}

canonical_path() {
    local path="$1"

    if command -v python3 >/dev/null 2>&1; then
        python3 - "$path" <<'PY'
import os
import sys

print(os.path.realpath(sys.argv[1]))
PY
        return
    fi

    perl -MCwd=realpath -e 'print realpath($ARGV[0]) || q()' "$path"
}

is_managed_link() {
    local link_path="$1"
    local resolved_link
    local resolved_skills_dir

    [ -L "$link_path" ] || return 1

    resolved_link="$(canonical_path "$link_path")"
    resolved_skills_dir="$(canonical_path "$SKILLS_DIR")"

    [ -n "$resolved_link" ] || return 1
    [ -n "$resolved_skills_dir" ] || return 1

    case "$resolved_link" in
        "$resolved_skills_dir"/*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

set_target() {
    local name="$1"
    local dir="$2"
    local index

    for index in "${!TARGET_NAMES[@]}"; do
        if [ "${TARGET_NAMES[$index]}" = "$name" ]; then
            TARGET_DIRS[$index]="$dir"
            return
        fi
    done

    TARGET_NAMES+=("$name")
    TARGET_DIRS+=("$dir")
}

target_exists() {
    local name="$1"
    local index

    for index in "${!TARGET_NAMES[@]}"; do
        if [ "${TARGET_NAMES[$index]}" = "$name" ]; then
            return 0
        fi
    done

    return 1
}

get_target_dir() {
    local name="$1"
    local index

    for index in "${!TARGET_NAMES[@]}"; do
        if [ "${TARGET_NAMES[$index]}" = "$name" ]; then
            printf '%s' "${TARGET_DIRS[$index]}"
            return 0
        fi
    done

    return 1
}

add_cli_target() {
    local entry="$1"
    local name="${entry%%=*}"
    local value="${entry#*=}"

    if [ -z "$name" ] || [ "$name" = "$value" ] || [ -z "$value" ]; then
        echo "❌ 无效的 --target 参数: $entry"
        exit 1
    fi

    set_target "$name" "$(resolve_dir "$value")"
    REQUESTED_TARGET_NAMES+=("$name")
}

register_builtin_targets() {
    local target_name

    for target_name in "${BUILTIN_TARGETS[@]}"; do
        set_target "$target_name" "$(builtin_target_dir "$target_name")"
    done
}

detect_existing_builtin_targets() {
    local target_name
    local target_dir

    DETECTED_TARGET_NAMES=()

    for target_name in "${BUILTIN_TARGETS[@]}"; do
        target_dir="$(builtin_target_dir "$target_name")"
        if [ -d "$target_dir" ]; then
            DETECTED_TARGET_NAMES+=("$target_name")
        fi
    done
}

cleanup_invalid_links() {
    local target_dir="$1"

    [ -d "$target_dir" ] || return 0

    for existing_link in "$target_dir"/*; do
        [ -L "$existing_link" ] || continue

        local existing_name
        existing_name="$(basename "$existing_link")"

        if is_managed_link "$existing_link" && [ ! -d "$SKILLS_DIR/$existing_name" ]; then
            echo "🧹 清理无效链接: $target_dir/$existing_name"
            rm -f "$existing_link"
        fi
    done
}

install_to_target() {
    local target_name="$1"
    local target_dir="$2"
    local count=0

    echo "========================================"
    echo "🚀 开始安装 Skills -> $target_name"
    echo "📂 目标目录: $target_dir"
    echo "========================================"

    if [ ! -d "$target_dir" ]; then
        echo "📁 创建目标目录: $target_dir"
        mkdir -p "$target_dir"
    fi

    cleanup_invalid_links "$target_dir"

    for skill_path in "$SKILLS_DIR"/*/; do
        local skill_name=""
        local target_link
        local source_dir
        local relative_source

        [ -d "$skill_path" ] || continue

        skill_name="$(basename "$skill_path")"
        target_link="$target_dir/$skill_name"
        source_dir="${skill_path%/}"
        relative_source="$(relative_path "$target_dir" "$source_dir")"

        if [ -L "$target_link" ]; then
            if is_managed_link "$target_link"; then
                echo "🔄 更新现有链接: $skill_name"
                rm -f "$target_link"
            else
                echo "⚠️  跳过 ${skill_name}：${target_link} 是外部已有软链接，未自动覆盖"
                continue
            fi
        elif [ -f "$target_link" ]; then
            echo "⚠️  跳过 ${skill_name}：${target_link} 已存在同名文件，未自动覆盖"
            continue
        elif [ -d "$target_link" ]; then
            echo "⚠️  跳过 ${skill_name}：${target_link} 已存在同名目录，未自动覆盖"
            continue
        else
            echo "🔗 创建全新链接: $skill_name"
        fi

        ln -s "$relative_source" "$target_link"
        count=$((count + 1))
    done

    echo "========================================"
    echo "✅ $target_name 安装完成，共链接 $count 个 Skill。"
    echo "========================================"
}

register_builtin_targets

INSTALL_ALL=false
DETECT_ONLY=false

while [ $# -gt 0 ]; do
    case "$1" in
        --detect)
            DETECT_ONLY=true
            ;;
        --all)
            INSTALL_ALL=true
            ;;
        --target)
            shift
            [ $# -gt 0 ] || {
                echo "❌ --target 需要一个 name=dir 参数"
                exit 1
            }
            add_cli_target "$1"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            REQUESTED_TARGET_NAMES+=("$1")
            ;;
    esac

    shift
done

if [ "$INSTALL_ALL" = true ]; then
    if [ ${#TARGET_NAMES[@]} -eq 0 ]; then
        echo "❌ 没有可安装的目标"
        exit 1
    fi

    for index in "${!TARGET_NAMES[@]}"; do
        install_to_target "${TARGET_NAMES[$index]}" "${TARGET_DIRS[$index]}"
    done
    exit 0
fi

if [ ${#REQUESTED_TARGET_NAMES[@]} -eq 0 ]; then
    DETECT_ONLY=true
fi

if [ "$DETECT_ONLY" = true ] && [ "$INSTALL_ALL" = false ] && [ ${#REQUESTED_TARGET_NAMES[@]} -eq 0 ]; then
    detect_existing_builtin_targets
    REQUESTED_TARGET_NAMES=("${DETECTED_TARGET_NAMES[@]+${DETECTED_TARGET_NAMES[@]}}")

    if [ ${#REQUESTED_TARGET_NAMES[@]} -eq 0 ]; then
        echo "⚠️  未检测到已存在的内置 agent skills 目录。"
        echo "   如需强制创建并安装全部内置目标，请运行: $(basename "$0") --all"
        exit 0
    fi

    echo "🔎 检测模式：将安装到以下已存在目标: ${REQUESTED_TARGET_NAMES[*]}"
fi

for target_name in "${REQUESTED_TARGET_NAMES[@]}"; do
    if ! target_exists "$target_name"; then
        echo "❌ 未找到安装目标: $target_name"
        echo "   可通过 --target $target_name=/path/to/skills 临时定义"
        exit 1
    fi

    install_to_target "$target_name" "$(get_target_dir "$target_name")"
done

echo "所有请求的安装目标已处理完成。"
