import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from django import forms
from .models import Book


class BaseBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'genre', 'year']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Мастер и Маргарита',
                'required': True
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Михаил Булгаков',
                'required': True
            }),
            'genre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Роман'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 1967',
                'min': 1000,
                'max': datetime.now().year,
                'required': True
            }),
        }

    def validate_unique(self):
        pass

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 2:
            raise forms.ValidationError("Название должно содержать минимум 2 символа.")
        if title.isdigit():
            raise forms.ValidationError("Название не может состоять только из цифр.")
        return re.sub(r'\s+', ' ', title)

    def clean_author(self):
        author = self.cleaned_data.get('author', '').strip()
        if len(author) < 2:
            raise forms.ValidationError("Имя автора должно содержать минимум 2 символа.")
        if not re.match(r'^[А-Яа-яЁёA-Za-z\s\.\-]+$', author):
            raise forms.ValidationError("Имя автора может содержать только буквы, пробелы, точки и дефис.")
        return re.sub(r'\s+', ' ', author)

    def clean_genre(self):
        genre = self.cleaned_data.get('genre', '').strip()
        if genre:
            if len(genre) < 2:
                raise forms.ValidationError("Жанр должен содержать минимум 2 символа.")
            if any(char.isdigit() for char in genre):
                raise forms.ValidationError("Название жанра не должно содержать цифры.")
        return re.sub(r'\s+', ' ', genre)

    def clean_year(self):
        year = self.cleaned_data.get('year')
        current_year = datetime.now().year
        if year is None:
            raise forms.ValidationError("Укажите год издания.")
        if year < 1000 or year > current_year:
            raise forms.ValidationError(f"Год издания должен быть в диапазоне от 1000 до {current_year}.")
        return year


class BookForm(BaseBookForm):
    STORAGE_CHOICES = [
        ('db', 'База данных (PostgreSQL / SQLite)'),
        ('json', 'Файл JSON'),
        ('xml', 'Файл XML'),
    ]
    storage = forms.ChoiceField(
        choices=STORAGE_CHOICES,
        label="Куда сохранить",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class EditBookForm(BaseBookForm):
    pass


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Выберите файл (.json или .xml)",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.xml'
        })
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if not uploaded_file:
            raise forms.ValidationError("Файл не выбран.")

        filename = uploaded_file.name.lower()
        if not (filename.endswith('.json') or filename.endswith('.xml')):
            raise forms.ValidationError("Разрешена загрузка только файлов формата .json или .xml.")

        content = uploaded_file.read().decode('utf-8', errors='strict')
        uploaded_file.seek(0)

        if filename.endswith('.json'):
            try:
                data = json.loads(content)
                if not isinstance(data, list):
                    raise forms.ValidationError("JSON-файл должен содержать список записей (массив объектов).")
            except json.JSONDecodeError:
                raise forms.ValidationError("Ошибка чтения: файл содержит некорректный JSON.")
        elif filename.endswith('.xml'):
            try:
                ET.fromstring(content)
            except ET.ParseError:
                raise forms.ValidationError("Ошибка чтения: файл содержит некорректный XML.")

        return uploaded_file
