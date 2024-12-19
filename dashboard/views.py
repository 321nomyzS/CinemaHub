import hashlib
import os
import re
import shutil
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from datetime import datetime
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.timezone import make_aware
from django.http import JsonResponse

from dashboard.models import *


@login_required
def main_page(request):
    return render(request, 'base.html')


@login_required
def show_users(request):
    users = User.objects.all()
    return render(request, 'show_users.html', {'users': users})


@login_required
def show_user(request, id):
    user = User.objects.get(id=id)
    return render(request, 'show_user.html', {'user_data': user})


def _validate_user_data(request, validate_password=True, except_user=None):
    errors = []

    username = request.POST.get('username')
    email = request.POST.get('email')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    file = request.FILES.get('image', None)

    if not username:
        errors.append("Nazwa użytkownika jest wymagana.")
    if not email or '@' not in email:
        errors.append("Wymagany jest poprawny adres e-mail.")
    if not first_name:
        errors.append("Imię jest wymagane.")
    if not last_name:
        errors.append("Nazwisko jest wymagane.")

    if User.objects.exclude(id=except_user).filter(username=username).exists():
        errors.append("Nazwa użytkownika jest już zajęta.")
    if User.objects.exclude(id=except_user).filter(email=email).exists():
        errors.append("Adres e-mail jest już zajęty.")

    if validate_password:
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if not password1 or len(password1) < 6:
            errors.append("Hasło musi zawierać co najmniej 6 znaków.")
        if password1 != password2:
            errors.append("Hasła nie są zgodne.")
    if file:
        extension = file.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png']

        if extension not in allowed_extensions:
            errors.append(f"Nieobsługiwane rozszerzenie pliku: .{extension}. Dozwolone to: {', '.join(allowed_extensions)}")
        try:
            img = Image.open(file)
            img.verify()
        except UnidentifiedImageError:
            errors.append("Przesłany plik nie jest prawidłowym obrazem.")
        except Exception as e:
            errors.append(f"Wystąpił błąd podczas weryfikacji obrazu: {str(e)}")

    return errors


def _rename_image_file(file):
    md5 = hashlib.md5()
    for chunk in file.chunks():
        md5.update(chunk)

    file_hash = md5.hexdigest()
    extension = os.path.splitext(file.name)[1]
    new_name = f"{file_hash}{extension}"
    file.name = new_name

    return file


def _resize_image(image, max_size=500):
    img = Image.open(image)
    if img.height > max_size or img.width > max_size:
        aspect_ratio = img.width / img.height
        if img.width > img.height:
            new_width = max_size
            new_height = int(max_size / aspect_ratio)
        else:
            new_height = max_size
            new_width = int(max_size * aspect_ratio)

        img = img.resize((new_width, new_height))

    buffer = BytesIO()
    img_format = image.name.split('.')[-1].lower()
    if img_format in ['jpg', 'jpeg']:
        img_format = 'JPEG'
    elif img_format == 'png':
        img_format = 'PNG'
    else:
        img_format = 'JPEG'

    img.save(buffer, format=img_format)
    buffer.seek(0)

    return ContentFile(buffer.read(), name=image.name)


@csrf_protect
@login_required
def add_user(request):
    if request.method == 'POST':
        is_admin = request.POST.get('is-admin') is not None
        is_mod = request.POST.get('is-mod') is not None

        errors = _validate_user_data(request)
        if not request.user.is_superuser:
            if is_admin or is_mod:
                errors.append("Nie masz uprawnień do nadawania uprawnień")
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_user.html')

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        is_admin = request.POST.get('is-admin') is not None
        is_mod = request.POST.get('is-mod') is not None
        image = request.FILES.get('image', None)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        if is_admin:
            user.is_staff = True
            user.is_superuser = True
        if is_mod:
            user.is_staff = True

        user.save()

        user_data = UserData(
            user=user,
        )
        if image:
            image = _rename_image_file(image)
            image = _resize_image(image)
            user_data.image = image

        user_data.save()

        messages.success(request, "Użytkownik został pomyślnie dodany")
        return redirect('show_users')

    return render(request, 'add_user.html')


@csrf_protect
@login_required
def edit_user(request, id):
    user = User.objects.get(id=id)
    if request.method == 'POST':
        is_admin = request.POST.get('is-admin') is not None
        is_mod = request.POST.get('is-mod') is not None

        errors = _validate_user_data(request, request.POST['password1'] != '', id)
        if not request.user.is_superuser:
            if is_mod != user.is_staff or is_admin != user.is_superuser:
                errors.append("Nie masz uprawnień do zmiany uprawnień")

        if not request.user.is_superuser and user.is_superuser:
            if request.POST["password1"] != '':
                errors.append("Nie możesz zmienić hasła temu użytkownikowi")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'edit_user.html', {"user_data": user})

        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        image = request.FILES.get('image', None)

        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name

        if password1 != "":
            user.set_password(password1)

        if is_admin and is_admin:
            user.is_superuser = True
            user.is_staff = True
        if is_admin and not is_mod:
            user.is_superuser = True
            user.is_staff = True
        if not is_admin and is_mod:
            user.is_superuser = False
            user.is_staff = True
        if not is_admin and not is_mod:
            user.is_superuser = False
            user.is_staff = False

        user.save()

        user_data = UserData.objects.get(user=user)
        if image:
            image = _rename_image_file(image)

            if user_data.image.name != user_data.image.field.default:
                user_data.image.delete()

            image = _resize_image(image)
            user_data.image = image
            user_data.save()

        return redirect('show_users')

    return render(request, 'edit_user.html', {"user_data": user})


@login_required
def delete_user(request, id):
    user = User.objects.get(id=id)
    user_data = UserData.objects.get(user=user)
    user_folder_path = os.path.join(settings.MEDIA_ROOT, f'user/{id}')

    if request.user.is_superuser:
        if user_data.image and user_data.image.name != user_data.image.field.default:
            user_data.image.delete()
        user.delete()

        if os.path.exists(user_folder_path):
            shutil.rmtree(user_folder_path)

        messages.success(request, "Użytkownik został pomyślnie usunięty")
        return redirect('show_users')

    if user.is_superuser or user.is_staff:
        messages.error(request, "Nie masz uprawnień do usunięcia tego użytkownika")
        return redirect('show_users')

    if user_data:
        if user_data.image and user_data.image.name != user_data.image.field.default:
            user_data.image.delete()
        user_data.delete()

    if os.path.exists(user_folder_path):
        shutil.rmtree(user_folder_path)

    messages.success(request, "Użytkownik został pomyślnie usunięty")
    return redirect('show_users')


@login_required
def show_posts(request):
    posts = Post.objects.all()
    return render(request, 'show_posts.html', {'posts': posts})


@login_required
def show_post(request, id):
    post = Post.objects.get(id=id)
    full_html = post.get_full_html()
    post_templates = PostTemplate.objects.filter(post=post).order_by('order')
    post_template_template_fields = PostTemplateTemplateField.objects.filter(post_template__in=post_templates)
    return render(request, 'show_post.html', {'post': post,
                                              'full_html': full_html,
                                              'post_templates': post_templates,
                                              'post_template_template_fields': post_template_template_fields
                                              }
                  )


@login_required
def show_raw_post(request, id):
    post = Post.objects.get(id=id)
    full_html = post.get_full_html()
    return render(request, 'show_raw_post.html', {'post': post, 'full_html': full_html})


@login_required
def delete_post(request, id):
    post = Post.objects.get(id=id)
    post.delete()
    messages.success(request, "Post został pomyślnie usunięty")

    return redirect('show_posts')


def _validate_template_data(request):
    errors = []

    name = request.POST.get('name', '')
    description = request.POST.get('description', '')
    content = request.POST.get('content', '')
    fields_numbers = int(request.POST.get('fields-numbers', 0))

    field_names = []
    field_types = []
    for i in range(1, fields_numbers+1):
        field_name = request.POST.get(f'field-name-{i}', '')
        field_names.append(field_name)
        field_type = request.POST.get(f'field-type-{i}', '')
        field_types.append(field_type)

    for field_type in field_types:
        if field_type == "":
            errors.append("Nie wszystkie pola mają wybrane typy")

    for field_name in field_names:
        if field_name == "":
            errors.append("Nazwa pola nie może być pusta")

    if not name:
        errors.append('Pole nazwa nie może być puste.')

    if not description:
        errors.append('Pole opis nie może być puste.')

    fields_in_template = re.findall(r'{{\s*([\w]+)\s*}}', content)

    unique_field_names = set(field_names)
    if len(field_names) != len(unique_field_names):
        errors.append("Każda nazwa pola może być tylko raz użyta w szablonie.")

    missing_in_form = [field for field in fields_in_template if field not in field_names]
    if missing_in_form:
        errors.append(f"Nie opisałeś następujących pól: {', '.join(missing_in_form)}")

    extra_in_form = [field for field in field_names if field not in fields_in_template]
    if extra_in_form:
        errors.append(f"W szablonie nie znajdują się pola: {', '.join(extra_in_form)}")

    if content == "":
        errors.append("Szablon nie może być pusty")

    return errors


@login_required
def show_templates(request):
    templates = Template.objects.all()
    return render(request, 'show_templates.html', {'templates': templates})


@login_required
def show_template(request, id):
    template = Template.objects.get(id=id)
    fields = TemplateField.objects.filter(template=template)
    return render(request, 'show_template.html', {'template': template, 'fields': fields})


@login_required
def add_template(request):
    field_types = FieldType.objects.all()
    if request.method == 'POST':
        errors = _validate_template_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_template.html', {'field_types': field_types})

        template_name = request.POST.get('name')
        template_description = request.POST.get('description')
        template_created_by = request.user
        template_html = request.POST.get('content')

        template = Template(
            name=template_name,
            description=template_description,
            created_by=template_created_by,
            html_structure=template_html
        )
        template.save()

        field_number = int(request.POST.get('fields-numbers', 0))
        for i in range(1, field_number+1):
            field_type = request.POST.get(f'field-type-{i}')
            field_name = request.POST.get(f'field-name-{i}')
            type_obj = FieldType.objects.get(id=field_type)

            field = TemplateField(
                name=field_name,
                type=type_obj,
                template=template
            )
            field.save()

        messages.success(request, "Szablon został zapisany")
        return redirect('show_template', id=template.id)

    return render(request, 'add_template.html', {'field_types': field_types})


@login_required
def edit_template(request, id):
    template = Template.objects.get(id=id)
    fields = TemplateField.objects.filter(template=template)
    field_types = FieldType.objects.all()

    if request.method == 'POST':
        errors = _validate_template_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'edit_template.html', {'template': template, 'fields': fields, 'field_types': field_types})

        template_name = request.POST.get('name')
        template_description = request.POST.get('description')
        template_created_by = request.user
        template_html = request.POST.get('content')

        template.name = template_name
        template.description = template_description
        template.html_structure = template_html
        template.save()

        field_number = int(request.POST.get('fields-numbers', 0))
        field_names_in_form = set()
        for i in range(1, field_number + 1):
            field_name = request.POST.get(f'field-name-{i}')
            field_type_id = request.POST.get(f'field-type-{i}')
            field_type = FieldType.objects.get(id=field_type_id)

            # Aktualizacja lub dodanie pola
            field, created = TemplateField.objects.update_or_create(
                template=template,
                name=field_name,
                defaults={'type': field_type}
            )
            field_names_in_form.add(field_name)

        # Usunięcie pól, które nie zostały przesłane w formularzu
        TemplateField.objects.filter(template=template).exclude(name__in=field_names_in_form).delete()

        messages.success(request, "Szablon został zapisany")
        return redirect('show_template', id=id)

    return render(request, 'edit_template.html', {'template': template, 'fields': fields, 'field_types': field_types})


@login_required
def delete_template(request, id):
    template = Template.objects.get(id=id)
    fields = TemplateField.objects.filter(template=template)

    for field in fields:
        field.delete()
    template.delete()

    messages.success(request, 'Szablon został usunięty')
    return redirect('show_templates')


@login_required
def show_pages(request):
    pages = Page.objects.all().order_by('order')
    return render(request, 'show_pages.html', {'pages': pages})


def _validate_page_data(request):
    errors = []

    title = request.POST.get('title', '')
    content = request.POST.get('content', '')

    if title == "":
        errors.append('Pole tytuł nie może być puste.')

    if len(title) >= 200:
        errors.append('Pole tytuł musi być krótsze niż 200 znaków.')

    if content == '':
        errors.append('Strona nie może być pusta.')

    return errors


@login_required
def add_page(request):
    if request.method == 'POST':
        errors = _validate_page_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_template.html')

        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        visibility = request.POST.get('visibility') is not None
        order = Page.objects.count() + 1

        page = Page(
            title=title,
            content=content,
            visibility=visibility,
            created_by=request.user,
            order=order
        )
        page.save()

        messages.success(request, "Strona została dodana pomyślnie")
        return redirect('show_page', id=page.id)

    return render(request, 'add_page.html')


@login_required
def edit_page(request, id):
    page = Page.objects.get(id=id)

    if request.method == 'POST':
        errors = _validate_page_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'edit_page.html', {'page': page})

        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        visibility = request.POST.get('visibility') is not None

        page.title = title
        page.content = content
        page.visibility = visibility

        page.save()

        messages.success(request, "Strona została zapisana pomyślnie")
        return redirect('show_page', id=page.id)

    return render(request, 'edit_page.html', {'page': page})


@login_required
def edit_pages(request):
    pages = Page.objects.all().order_by('order')

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            for item in data['order']:
                page_id = int(item['page_id'])
                order = int(item['order'])

                page = Page.objects.get(id=page_id)
                page.order = order
                page.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return render(request, 'edit_pages.html', {'pages': pages})


@login_required
def delete_page(request, id):
    page = Page.objects.get(id=id)
    page.delete()
    messages.success(request, "Strona została pomyślnie usunięta")

    return redirect('show_pages')


@login_required
def show_page(request, id):
    page = Page.objects.get(id=id)
    return render(request, 'show_page.html', {'page': page})


@login_required
def show_movies(request):
    movies = Movie.objects.all()
    for movie in movies:
        movie.director = MovieCrewMember.objects.filter(movie=movie, role__id=1).first()

    return render(request, 'show_movies.html', {'movies': movies})


def _validate_movie_data(request):
    errors = []
    title = request.POST.get('title', '')
    release_date = request.POST.get('release_date', '')
    description = request.POST.get('description', '')
    crew_members_count = int(request.POST.get('crew-members-count', 0))
    file = request.FILES.get('image', None)
    category = request.POST.get('category', '')

    if not title:
        errors.append('Pole tytuł nie może być puste.')
    elif len(title) > 150:
        errors.append('Pole tytuł nie może mieć więcej niż 150 znaków.')

    if not release_date:
        errors.append('Data premiery jest wymagana.')
    else:
        try:
            _ = datetime.strptime(release_date, "%Y-%m-%d")
        except ValueError:
            errors.append('Data premiery jest nieprawidłowa.')

    if not description:
        errors.append('Opis jest wymagany.')

    if category == "":
        errors.append('Kategoria jest wymagana.')

    for i in range(1, crew_members_count + 1):
        member_id = request.POST.get(f'member-{i}', '')
        role_id = request.POST.get(f'role-{i}', '')
        character_name = request.POST.get(f'character_name-{i}', '')

        if not member_id:
            errors.append(f'Członek obsady (formularz {i}) musi być wybrany.')
        else:
            if not CrewMember.objects.filter(id=member_id).exists():
                errors.append(f'Członek obsady o ID {member_id} nie istnieje.')

        if not role_id:
            errors.append(f'Rola (formularz {i}) musi być wybrana.')
        else:
            if not Role.objects.filter(id=role_id).exists():
                errors.append(f'Rola o ID {role_id} nie istnieje.')

        if character_name and len(character_name) > 150:
            errors.append(f'Nazwa postaci (formularz {i}) nie może mieć więcej niż 150 znaków.')

    if file:
        extension = file.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png']

        if extension not in allowed_extensions:
            errors.append(f"Nieobsługiwane rozszerzenie pliku: .{extension}. Dozwolone to: {', '.join(allowed_extensions)}")
        try:
            img = Image.open(file)
            img.verify()
        except UnidentifiedImageError:
            errors.append("Przesłany plik nie jest prawidłowym obrazem.")
        except Exception as e:
            errors.append(f"Wystąpił błąd podczas weryfikacji obrazu: {str(e)}")

    return errors


@login_required
def add_movie(request):
    members = CrewMember.objects.all()
    roles = Role.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        errors = _validate_movie_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_movie.html')

        title = request.POST.get('title', '')
        release_date = request.POST.get('release_date', '')
        description = request.POST.get('description', '')
        crew_members_count = int(request.POST.get('crew-members-count', 0))
        poster = request.FILES.get('image', None)
        category_id = request.POST.get('category', '')

        release_date_obj = datetime.strptime(release_date, '%Y-%m-%d')
        release_date_aware = make_aware(release_date_obj)
        category = Category.objects.get(id=category_id)

        movie = Movie(
            title=title,
            description=description,
            release_date=release_date_aware,
            category=category
        )
        movie.save()

        if poster:
            image = _rename_image_file(poster)
            image = _resize_image(image)
            movie.poster = image
        movie.save()

        for i in range(1, crew_members_count + 1):
            member_id = request.POST.get(f'member-{str(i)}', '')
            role_id = request.POST.get(f'role-{str(i)}', '')

            member = CrewMember.objects.get(id=member_id)
            role = Role.objects.get(id=role_id)
            character_name = request.POST.get(f'character_name-{str(i)}', '')

            movie_crew_member = MovieCrewMember(
                crew_member=member,
                movie=movie,
                role=role,
                character_name=character_name
            )
            movie_crew_member.save()

        messages.success(request, f'Film "{title}" został pomyślnie dodany!')
        return redirect('show_movies')
    return render(request, 'add_movie.html', {'members': members, 'roles': roles, 'categories': categories})


@login_required
def show_movie(request, id):
    movie = Movie.objects.get(id=id)
    return render(request, 'show_movie.html', {'movie': movie})


@login_required
def edit_movie(request, id):
    movie = Movie.objects.get(id=id)
    members = CrewMember.objects.all()
    roles = Role.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        errors = _validate_movie_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_movie.html')

        title = request.POST.get('title', '')
        release_date = request.POST.get('release_date', '')
        description = request.POST.get('description', '')
        crew_members_count = int(request.POST.get('crew-members-count', 0))
        poster = request.FILES.get('image', None)
        category_id = request.POST.get('category', '')

        release_date_obj = datetime.strptime(release_date, '%Y-%m-%d')
        release_date_aware = make_aware(release_date_obj)
        category = Category.objects.get(id=category_id)

        movie.title = title
        movie.description = description
        movie.release_date = release_date_aware
        movie.category = category

        if poster:
            image = _rename_image_file(poster)
            if movie.poster.name != movie.poster.field.default:
                movie.poster.delete()
            image = _resize_image(image)
            movie.poster = image
        movie.save()

        # Delete old movie crew members
        old_movie_crew_members = MovieCrewMember.objects.filter(movie=movie)
        for movie_crew_member in old_movie_crew_members:
            movie_crew_member.delete()

        # Add new movie crew members
        for i in range(1, crew_members_count + 1):
            member_id = request.POST.get(f'member-{str(i)}', '')
            role_id = request.POST.get(f'role-{str(i)}', '')

            member = CrewMember.objects.get(id=member_id)
            role = Role.objects.get(id=role_id)
            character_name = request.POST.get(f'character_name-{str(i)}', '')

            movie_crew_member = MovieCrewMember(
                crew_member=member,
                movie=movie,
                role=role,
                character_name=character_name
            )
            movie_crew_member.save()

        messages.success(request, f'Film "{title}" został pomyślnie zapisany!')
        return redirect('show_movies')

    return render(request, 'edit_movie.html', {'movie': movie, 'members': members, 'roles': roles, 'categories': categories})


@login_required
def delete_movie(request, id):
    movie = Movie.objects.get(id=id)
    movie_crew_members = MovieCrewMember.objects.filter(movie=movie)
    member_folder_path = os.path.join(settings.MEDIA_ROOT, f'movie/{id}')

    for movie_crew_member in movie_crew_members:
        movie_crew_member.delete()

    if movie.poster and movie.poster.name != movie.poster.field.default:
        movie.poster.delete()
    if os.path.exists(member_folder_path):
        shutil.rmtree(member_folder_path)

    movie.delete()

    messages.success(request, "Film został pomyślnie usunięty")
    return redirect('show_movies')


@login_required
def show_members(request):
    members = CrewMember.objects.all()
    return render(request, 'show_members.html', {'members': members})


@login_required
def show_member(request, id):
    member = CrewMember.objects.get(id=id)
    return render(request, 'show_member.html', {'member': member})


def _validate_crew_member_data(request):
    errors = []
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    birth_date = request.POST.get('birth_date', '').strip()
    description = request.POST.get('description', '').strip()
    file = request.FILES.get('image', None)

    if first_name == '':
        errors.append('Pole imię nie może być puste.')
    if len(first_name) > 150:
        errors.append('Pole imię może mieć maksymalnie 150 znaków.')

    if last_name == '':
        errors.append('Pole nazwisko nie może być puste.')
    if len(last_name) > 150:
        errors.append('Pole nazwisko może mieć maksymalnie 150 znaków.')

    if description == '':
        errors.append('Pole opis nie może być puste.')

    if birth_date == '':
        errors.append('Pole data urodzenia nie może być puste.')
    else:
        try:
            from datetime import datetime
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
            today = datetime.today().date()
            if birth_date_obj > today:
                errors.append('Nieprawidłowa data urodzenia: data nie może być późniejsza niż dzisiaj.')
        except ValueError:
            errors.append('Nieprawidłowy format daty. Oczekiwany format: YYYY-MM-DD.')

    if file:
        extension = file.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png']

        if extension not in allowed_extensions:
            errors.append(f"Nieobsługiwane rozszerzenie pliku: .{extension}. Dozwolone to: {', '.join(allowed_extensions)}")
        try:
            img = Image.open(file)
            img.verify()
        except UnidentifiedImageError:
            errors.append("Przesłany plik nie jest prawidłowym obrazem.")
        except Exception as e:
            errors.append(f"Wystąpił błąd podczas weryfikacji obrazu: {str(e)}")

    return errors


@login_required
def add_member(request):
    if request.method == 'POST':
        errors = _validate_crew_member_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_member.html')

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        birth_date = request.POST['birth_date']
        description = request.POST['description']
        image = request.FILES.get('image', None)

        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
        birth_date_aware = make_aware(birth_date_obj)

        member = CrewMember(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date_aware,
            description=description,
            created_by=request.user
        )
        member.save()

        if image:
            image = _rename_image_file(image)
            image = _resize_image(image)
            member.image = image
        member.save()

        return redirect('show_members')

    return render(request, 'add_member.html')


@login_required
def edit_member(request, id):
    member = CrewMember.objects.get(id=id)

    if request.method == 'POST':
        errors = _validate_crew_member_data(request)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'edit_member.html', {'member': member})

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        birth_date = request.POST['birth_date']
        description = request.POST['description']
        image = request.FILES.get('image', None)

        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
        birth_date_aware = make_aware(birth_date_obj)

        member.first_name = first_name
        member.last_name = last_name
        member.description = description
        member.birth_date = birth_date_aware
        member.save()

        if image:
            image = _rename_image_file(image)

            if member.image.name != member.image.field.default:
                member.image.delete()

            image = _resize_image(image)
            member.image = image
            member.save()

        messages.success(request, "Członek obsady został zapisany pomyślnie")
        return redirect('show_member', id=member.id)

    return render(request, 'edit_member.html', {'member': member})


@login_required
def delete_member(request, id):
    member = CrewMember.objects.get(id=id)
    member_folder_path = os.path.join(settings.MEDIA_ROOT, f'member/{id}')

    if member.image and member.image.name != member.image.field.default:
        member.image.delete()
    member.delete()

    if os.path.exists(member_folder_path):
        shutil.rmtree(member_folder_path)

    messages.success(request, "Członek obsady został pomyślnie usunięty")
    return redirect('show_members')


@csrf_protect
def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_superuser or user.is_staff:
                login(request, user)
                return redirect('main_page')
            else:
                return render(request, 'login.html', {'error': True})
        else:
            return render(request, 'login.html', {'error': True})

    return render(request, 'login.html')


def logout_tunnel(request):
    logout(request)
    return redirect('login')
