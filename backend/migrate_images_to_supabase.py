#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
把 images 和 dream_images 表中存本地路径的 file_path：
1. 对应的本地文件上传到 Supabase Storage
2. 把 file_path 更新成 Supabase public URL

使用前请确认：
- .env 中配置了 SUPABASE_URL / SUPABASE_KEY / SUPABASE_PLANT_BUCKET / SUPABASE_DREAM_BUCKET / DATABASE_URL
- 本地文件路径是有效的（脚本会自动跳过找不到的文件）
"""

import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from supabase import create_client, Client


# ============== 加载环境变量 ==============
load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
PLANT_BUCKET = os.environ.get("SUPABASE_PLANT_BUCKET", "plant-images")
DREAM_BUCKET = os.environ.get("SUPABASE_DREAM_BUCKET", "dream-images")
DATABASE_URL = os.environ["DB_URL"]

# ============== 初始化 Supabase & DB 连接 ==============
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
if DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False  # 我们手动控制事务
cursor = conn.cursor(cursor_factory=DictCursor)


def upload_file_to_bucket(bucket: str, storage_path: str, local_path: Path) -> str:
    """上传文件到指定 bucket，并返回 public URL"""
    with local_path.open("rb") as f:
        data = f.read()

    # 根据文件后缀简单判断一下 content-type（可选）
    suffix = local_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        content_type = "image/jpeg"
    elif suffix == ".png":
        content_type = "image/png"
    else:
        content_type = "application/octet-stream"

    # 注意：file_options 的 value 必须是 str / bytes
    supabase.storage.from_(bucket).upload(
        path=storage_path,
        file=data,
        file_options={
            "content-type": content_type,
            "upsert": "true",  # ✅ 必须是字符串，而不是 True
        },
    )

    public_url = supabase.storage.from_(bucket).get_public_url(storage_path)
    return public_url



def migrate_table(
    table_name: str,
    bucket: str,
):
    """
    通用迁移函数：
    - table_name: "images" 或 "dream_images"
    - bucket: PLANT_BUCKET 或 DREAM_BUCKET
    """

    print(f"\n=== 开始迁移表: {table_name} 到 bucket: {bucket} ===")

    # 只迁移那些还不是 URL 的记录（避免重复迁移）
    # 简单判断：file_path 不以 'http' 开头
    cursor.execute(
        f"""
        SELECT id, plant_id, file_path
        FROM {table_name}
        WHERE file_path IS NOT NULL
          AND file_path <> ''
          AND file_path NOT LIKE 'http%'
        ORDER BY id;
        """
    )

    rows = cursor.fetchall()
    total = len(rows)
    print(f"{table_name} 中待迁移记录数: {total}")

    migrated = 0
    skipped = 0
    failed = 0

    for row in rows:
        row_id = row["id"]
        plant_id = row["plant_id"]
        file_path = row["file_path"]

        local_path = Path(file_path)

        if not local_path.exists():
            print(f"[跳过] id={row_id} 本地文件不存在: {local_path}")
            skipped += 1
            continue

        # 存储路径： {plant_id}/{文件名}
        storage_path = f"{plant_id}/{local_path.name}"

        try:
            public_url = upload_file_to_bucket(bucket, storage_path, local_path)

            # 更新数据库记录
            cursor.execute(
                f"UPDATE {table_name} SET file_path = %s WHERE id = %s",
                (public_url, row_id),
            )

            migrated += 1
            print(f"[成功] id={row_id} -> {public_url}")

        except Exception as e:
            failed += 1
            print(f"[失败] id={row_id} 上传或更新出错: {e}")

    # 提交事务
    conn.commit()
    print(
        f"=== 表 {table_name} 迁移完成: 成功 {migrated} 条, 跳过 {skipped} 条, 失败 {failed} 条 ==="
    )


def main():
    try:
        migrate_table("images", PLANT_BUCKET)
        migrate_table("dream_images", DREAM_BUCKET)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
