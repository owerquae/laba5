import json
import os
import xml.etree.ElementTree as ET
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Book
from .forms import BookForm, EditBookForm

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
JSON_FILE = os.path.join(DATA_DIR, 'books.json')
XML_FILE = os.path.join(DATA_DIR, 'books.xml')


def read_json():
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(book_data):
    books = read_json()
    books.append(book_data)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)


def read_xml():
    if not os.path.exists(XML_FILE):
        return []
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    return [{child.tag: child.text for child in item} for item in root.findall('book')]


def write_xml(book_data):
    if os.path.exists(XML_FILE):
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    else:
        root = ET.Element('books')
        tree = ET.ElementTree(root)
    book_el = ET.SubElement(root, 'book')
    for key, val in book_data.items():
        child = ET.SubElement(book_el, key)
        child.text = str(val)
    tree.write(XML_FILE, encoding='utf-8', xml_declaration=True)


def index(request):
    source = request.GET.get('source', 'db')

    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            storage = form.cleaned_data['storage']
            data = {
                'title': form.cleaned_data['title'],
                'author': form.cleaned_data['author'],
                'genre': form.cleaned_data['genre'],
                'year': form.cleaned_data['year'],
            }

            if storage == 'db':
                is_duplicate = Book.objects.filter(
                    title__iexact=data['title'],
                    author__iexact=data['author'],
                    year=data['year']
                ).exists()

                if is_duplicate:
                    messages.warning(request, 'Такая запись уже есть в базе данных! Нельзя добавлять одинаковые записи.')
                else:
                    Book.objects.create(**data)
                    messages.success(request, 'Запись успешно добавлена в БД.')
            elif storage == 'json':
                write_json(data)
                messages.success(request, 'Запись сохранена в JSON-файл.')
            elif storage == 'xml':
                write_xml(data)
                messages.success(request, 'Запись сохранена в XML-файл.')

            return redirect(f'/?source={storage}')
        else:
            messages.error(request, 'Ошибка! Проверьте правильность заполнения полей формы.')
    else:
        form = BookForm()

    if source == 'json':
        books = read_json()
    elif source == 'xml':
        books = read_xml()
    else:
        books = Book.objects.all()

    return render(request, 'books/index.html', {
        'form': form,
        'books': books,
        'source': source,
    })


def ajax_search(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(author__icontains=query) |
        Q(genre__icontains=query)
    )
    results = list(items.values('id', 'title', 'author', 'genre', 'year')) if False else list(
        books.values('id', 'title', 'author', 'genre', 'year')
    )
    return JsonResponse({'results': results})


def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = EditBookForm(request.POST, instance=book)
        if form.is_valid():
            cd = form.cleaned_data
            duplicate = Book.objects.filter(
                title__iexact=cd['title'],
                author__iexact=cd['author'],
                year=cd['year']
            ).exclude(pk=pk).exists()

            if duplicate:
                messages.warning(request, 'Такая запись уже есть в базе данных! Нельзя сохранять одинаковые записи.')
            else:
                form.save()
                messages.success(request, 'Запись успешно обновлена.')
                return redirect('/?source=db')
        else:
            messages.error(request, 'Ошибка! Проверьте корректность введённых значений.')
    else:
        form = EditBookForm(instance=book)
    return render(request, 'books/edit.html', {'form': form, 'book': book})


def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Запись удалена из БД.')
    return redirect('/?source=db')
