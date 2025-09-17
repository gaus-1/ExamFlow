import os
from urllib.parse import urlparse

import psycopg


def main() -> None:
    dburl = os.environ.get("DATABASE_URL")
    if not dburl:
        raise SystemExit("DATABASE_URL is not set")

    url = urlparse(dburl)
    base_db = url.path.lstrip("/")
    test_db = f"test_{base_db}"

    conn = psycopg.connect(
        dbname="postgres",
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        autocommit=True,
    )

    # Terminate connections
    conn.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
        (test_db,),
    )

    # type: ignore
    # Удаляем тестовую БД (сначала пробуем с WITH (FORCE), если не поддерживается — без него)
    try:
        conn.execute(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)')  # type: ignore
    except Exception:
        conn.execute(f'DROP DATABASE IF EXISTS "{test_db}"')  # type: ignore

    # type: ignore
    # Создаём тестовую БД
    try:
        conn.execute(f'CREATE DATABASE "{test_db}"')  # type: ignore
        print("OK")
    except Exception as e:
        print(f"Ошибка при создании тестовой БД: {e}")

if __name__ == "__main__":
    main()


