import json
import os
import xml.etree.ElementTree as ET
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Book
from .forms import BookForm, EditBookForm, UploadFileForm

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

JSON_FILE = os.path.join(DATA_DIR, 'books.json')
XML_FILE = os.path.join(DATA_DIR, 'books.xml')


def read_json():
    records = []
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            records.extend(json.load(f))
    # Также считываем данные из загруженных пользователем JSON-файлов
    for fname in os.listdir(UPLOADS_DIR):
        if fname.lower().endswith('.json'):
            fpath = os.path.join(UPLOADS_DIR, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
            except Exception:
                pass
    return records


def write_json(book_data):
    books = []
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            books = json.load(f)
    books.append(book_data)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=4)


def _parse_xml_file(path):
    if not os.path.exists(path):
        return []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        return [{child.tag: child.text for child in item} for item in root.findall('book')]
    except Exception:
        return []


def read_xml():
    records = _parse_xml_file(XML_FILE)
    # Также считываем данные из загруженных пользователем XML-файлов
    for fname in os.listdir(UPLOADS_DIR):
        if fname.lower().endswith('.xml'):
            records.extend(_parse_xml_file(os.path.join(UPLOADS_DIR, fname)))
    return records


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
    form = BookForm()
    upload_form = UploadFileForm()

    if request.method == 'POST':
        # 1. Если отправлена форма загрузки файла JSON/XML
        if 'upload_submit' in request.POST:
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                uploaded_file = upload_form.cleaned_data['file']
                save_path = os.path.join(UPLOADS_DIR, uploaded_file.name)
                with open(save_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                ext = 'json' if uploaded_file.name.lower().endswith('.json') else 'xml'
                messages.success(request, f'Файл «{uploaded_file.name}» успешно загружен в папку data/uploads/.')
                return redirect(f'/?source={ext}')
            else:
                messages.error(request, 'Ошибка загрузки файла! Проверьте формат и структуру JSON/XML.')

        # 2. Если отправлена форма добавления записи
        else:
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

    if source == 'json':
        books = read_json()
    elif source == 'xml':
        books = read_xml()
    else:
        books = Book.objects.all()

    return render(request, 'books/index.html', {
        'form': form,
        'upload_form': upload_form,
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
    results = list(books.values('id', 'title', 'author', 'genre', 'year'))
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
