from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название книги")
    author = models.CharField(max_length=150, verbose_name="Автор")
    genre = models.CharField(max_length=100, blank=True, verbose_name="Жанр")
    year = models.PositiveIntegerField(verbose_name="Год издания")

    class Meta:
        unique_together = ('title', 'author', 'year')

    def __str__(self):
        return f"{self.title} — {self.author} ({self.year})"
