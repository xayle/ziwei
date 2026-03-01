#!/usr/bin/env python3
"""
应用性能优化索引
Phase 1 性能优化 - 创建5个推荐数据库索引
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from db import get_engine


def apply_indexes():
    """应用性能优化索引"""
    
    # 读取SQL脚本
    sql_file = Path(__file__).parent / "create_performance_indexes.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL文件不存在: {sql_file}")
        return False
    
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # 分割SQL语句（按分号分隔，忽略注释）
    statements = []
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if line.startswith('--') or not line:
            continue
        statements.append(line)
    
    # 合并多行语句
    sql_statements = ' '.join(statements).split(';')
    sql_statements = [s.strip() for s in sql_statements if s.strip()]
    
    print("\n" + "="*60)
    print("  📊 BaZi Service - 性能索引创建工具")
    print("="*60 + "\n")
    
    engine = get_engine()
    success_count = 0
    
    try:
        with engine.connect() as conn:
            for idx, statement in enumerate(sql_statements, 1):
                if not statement or statement.startswith('--'):
                    continue
                
                try:
                    # 提取索引名称用于日志
                    index_name = "unknown"
                    if "idx_" in statement:
                        import re
                        match = re.search(r'idx_\w+', statement)
                        if match:
                            index_name = match.group(0)
                    
                    print(f"🔄 正在创建索引 #{idx}: {index_name}...", end=" ")
                    conn.execute(text(statement))
                    conn.commit()
                    print("✅ 成功")
                    success_count += 1
                    
                except Exception as e:
                    print(f"⚠️  警告: {str(e)}")
                    # 如果索引已存在，不算错误
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        success_count += 1
                        print(f"   (索引已存在，跳过)")
        
        print("\n" + "="*60)
        print(f"✅ 索引创建完成: {success_count}/{len(sql_statements)} 个成功")
        print("="*60 + "\n")
        
        if success_count == len(sql_statements):
            print("🎉 预期性能提升: +80% 查询速度")
            print("📊 建议: 重新运行性能测试验证改进效果\n")
            return True
        else:
            print("⚠️  部分索引创建失败，请检查日志\n")
            return False
            
    except Exception as e:
        print(f"\n❌ 索引创建失败: {str(e)}\n")
        return False


if __name__ == "__main__":
    success = apply_indexes()
    sys.exit(0 if success else 1)
