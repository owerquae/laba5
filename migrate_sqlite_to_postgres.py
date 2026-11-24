import os
import sqlite3
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from books.models import Book


def migrate_data(sqlite_path='db.sqlite3'):
    if not os.path.exists(sqlite_path):
        print(f"Файл {sqlite_path} не найден.")
        return

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, author, genre, year FROM books_book")
    rows = cursor.fetchall()

    created_count = 0
    for title, author, genre, year in rows:
        _, created = Book.objects.get_or_create(
            title=title,
            author=author,
            year=year,
            defaults={'genre': genre or ''}
        )
        if created:
            created_count += 1

    conn.close()
    print(f"Миграция завершена. Перенесено новых записей: {created_count} из {len(rows)}.")


if __name__ == '__main__':
    migrate_data()
