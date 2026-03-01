"""
自动导入更新脚本
在运行此脚本前，请确保已备份你的代码（git commit）
"""
import os
import re
from pathlib import Path

def update_imports_in_file(filepath: str) -> dict:
    """
    更新单个文件中的导入语句
    
    Returns:
        {
            'file': filepath,
            'updated': True/False,
            'changes': [list of changes made],
            'error': error message if any
        }
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # 导入替换规则
        replacements = [
            (r'^from models import', 'from app.models import'),
            (r'^from schemas import', 'from app.schemas import'),
            (r'^from config import', 'from app.config import'),
            (r'^import models$', 'import app.models as models'),
            (r'^import models as', 'import app.models as'),
        ]
        
        for old_pattern, new_text in replacements:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                # 仅在行首匹配（用^确保）
                if re.match(old_pattern, line):
                    new_line = re.sub(old_pattern, new_text, line)
                    if new_line != line:
                        new_lines.append(new_line)
                        changes.append(f"  L{len(new_lines)}: {line.strip()[:60]} → {new_line.strip()[:60]}")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # 检查是否有变化
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                'file': filepath,
                'updated': True,
                'changes': changes,
                'error': None
            }
        else:
            return {
                'file': filepath,
                'updated': False,
                'changes': [],
                'error': None
            }
    
    except Exception as e:
        return {
            'file': filepath,
            'updated': False,
            'changes': [],
            'error': str(e)
        }


def main():
    """执行批量导入更新"""
    
    # 扫描所有 Python 文件
    root_dir = Path('.')
    files_to_update = []
    
    # 优化文件集合
    target_patterns = [
        'run.py',
        'db.py',
        'routers/*.py',
        'services/*.py',
        'tests/*.py',
    ]
    
    for pattern in target_patterns:
        files_to_update.extend(root_dir.glob(pattern))
    
    # 移除重复
    files_to_update = list(set(files_to_update))
    files_to_update.sort()
    
    print("=" * 80)
    print("自动导入更新脚本 - 第一周重构")
    print("=" * 80)
    print()
    print(f"将更新 {len(files_to_update)} 个文件")
    print()
    
    # 更新前警告
    print("⚠️  重要警告：")
    print("  1. 请先做好备份 (git commit)")
    print("  2. 此脚本会修改你的文件")
    print("  3. 修改后请验证导入是否正确")
    print()
    
    response = input("继续? (yes/no): ").strip().lower()
    if response != 'yes':
        print("已取消")
        return
    
    print()
    print("正在处理...")
    print()
    
    # 执行更新
    results = []
    for filepath in files_to_update:
        result = update_imports_in_file(str(filepath))
        results.append(result)
        
        if result['updated']:
            print(f"✅ {result['file']}")
            for change in result['changes'][:3]:  # 显示前3个变化
                print(f"   {change}")
            if len(result['changes']) > 3:
                print(f"   ... 还有 {len(result['changes']) - 3} 个更改")
        elif result['error']:
            print(f"❌ {result['file']} - 错误: {result['error']}")
    
    # 总结
    print()
    print("=" * 80)
    print("完成汇总")
    print("=" * 80)
    
    updated_count = sum(1 for r in results if r['updated'])
    total_changes = sum(len(r['changes']) for r in results)
    error_count = sum(1 for r in results if r['error'])
    
    print(f"✅ 更新文件数：{updated_count}")
    print(f"📝 总变化数：{total_changes}")
    print(f"❌ 错误文件：{error_count}")
    print()
    
    if updated_count > 0:
        print("下一步：")
        print("  1. 验证导入：python -c 'from app.models import *; from app.schemas import *'")
        print("  2. 运行应用：python run.py")
        print("  3. 检查健康状态：curl http://localhost:8000/health")
        print("  4. 运行测试：pytest tests/")
        print()
    else:
        print("没有文件被更新，可能所有导入都已正确。")


if __name__ == '__main__':
    main()
