import hashlib
from PIL import Image, UnidentifiedImageError
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.conf import settings

from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework import status

from .serializers import *


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


def _validate_image(file):
    errors = []

    if file:
        extension = file.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png']

        if extension not in allowed_extensions:
            errors.append(
                f"Nieobsługiwane rozszerzenie pliku: .{extension}. Dozwolone to: {', '.join(allowed_extensions)}")

        try:
            img = Image.open(file)
            img.verify()
        except UnidentifiedImageError:
            errors.append("Przesłany plik nie jest prawidłowym obrazem.")
        except Exception as e:
            errors.append(f"Wystąpił błąd podczas weryfikacji obrazu: {str(e)}")

    return errors


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)


class UserDataView(APIView):
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        return UserData.objects.get(user=self.request.user)

    def get(self, request):
        user_data = self.get_object()
        serializer = UserDataSerializer(user_data)
        return Response(serializer.data)

    def post(self, request):
        return self.put(request)

    def put(self, request):
        user_data = self.get_object()
        serializer = UserDataSerializer(user_data, data=request.data, partial=True)

        if serializer.is_valid():
            image = request.data.get('image', None)
            if image:
                errors = _validate_image(image)
                if len(errors) > 0:
                    return Response({'error': '\n'.join(errors)}, status=status.HTTP_400_BAD_REQUEST)

                image = _rename_image_file(image)
                image = _resize_image(image)
                user_data.image = image

            user_data.save()
            return Response(UserDataSerializer(user_data).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_data = self.get_object()

        if user_data.image and user_data.image.name != user_data.image.field.default:
            user_data.image.delete()

        user_data.image = user_data.image.field.default
        user_data.save()

        return Response(UserDataSerializer(user_data).data)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserCurrentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request):
        return request.user

    def get(self, request):
        user = self.get_object(request)

        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = self.get_object(request)
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PageListView(ListAPIView):
    queryset = Page.objects.filter(visibility=True).order_by('order')
    serializer_class = PagesSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)


class PageDetailView(RetrieveAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)


class CategoryListView(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        categories = Category.objects.all()

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class RecentMovieListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        movies = Movie.objects.all()

        movies = movies.order_by("-release_date")[:5]
        serializer = MoviesSerializer(movies, many=True)
        return Response(serializer.data)

class MovieListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        category_name = request.query_params.get('category', None)
        director_id = request.query_params.get('director_id', None)
        crew_member_id = request.query_params.get('crew_member_id', None)


        movies = Movie.objects.all()
        if category_name:
            movies = movies.filter(category__name__iexact=category_name)

        if director_id:
            movies = movies.filter(
                moviecrewmember__crew_member_id=director_id,
                moviecrewmember__role__id=1
            )

        if crew_member_id:
            movies = movies.filter(moviecrewmember__crew_member_id=crew_member_id)
        serializer = MoviesSerializer(movies, many=True)
        return Response(serializer.data)


class MovieDetailView(APIView):
    def get(self, request, id):
        try:
            movie = Movie.objects.get(id=id)
        except Movie.DoesNotExist:
            return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MovieDetailSerializer(movie)
        return Response(serializer.data)


class CrewDetailView(APIView):
    def get(self, request, id):
        try:
            crew_member = CrewMember.objects.get(id=id)
        except CrewMember.DoesNotExist:
            return Response({'error': 'Crew Member not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CrewDetailSerializer(crew_member)
        return Response(serializer.data)

class PostCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            post_data = serializer.validated_data
            status_id = request.data.get("status")
            status_obj = Status.objects.get(id=status_id)

            # Tworzenie posta
            post = Post.objects.create(
                title=post_data['title'],
                content=post_data.get('content', ''),
                status=status_obj,
                created_by=request.user,
                movie_id=post_data.get('movie_id')
            )

            templates_data = post_data['templates']
            for template_data in templates_data:
                post_template = PostTemplate.objects.create(
                    post=post,
                    template_id=template_data['template_id'],
                    order=template_data['order']
                )

                for field_data in template_data['fields']:
                    PostTemplateTemplateField.objects.create(
                        post_template=post_template,
                        field_id=field_data['field_id'],
                        content=field_data['content']
                    )

            return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        full_html = post.get_full_html()
        post_data = PostSerializer(post).data
        post_data['html'] = full_html

        return Response(post_data, status=status.HTTP_200_OK)

    def get_object(self, id):
        try:
            return Post.objects.get(id=id)
        except Post.DoesNotExist:
            return None

    def put(self, request, id):
        post = self.get_object(id)
        if not post:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the author of the post
        if post.created_by != request.user or request.user.is_staff:
            return Response({"error": "You do not have permission to edit this post."},
                            status=status.HTTP_403_FORBIDDEN)

        # Update basic fields (title, content, status, movie_id)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            post = serializer.save()

            PostTemplate.objects.filter(post=post).delete()

            # Add new templates (from the request body)
            templates_data = request.data.get("templates", [])
            for template_data in templates_data:
                template = Template.objects.get(id=template_data["template_id"])

                post_template = PostTemplate.objects.create(
                    post=post,
                    template=template,
                    order=template_data["order"]
                )

                for field_data in template_data.get("fields", []):
                    template_field = TemplateField.objects.get(id=field_data["field_id"])

                    PostTemplateTemplateField.objects.create(
                        post_template=post_template,
                        field=template_field,
                        content=field_data.get("content")
                    )

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            post = Post.objects.get(id=id)

            if post.created_by != request.user and not request.user.is_staff:
                return Response({"detail": "Nie masz uprawnień do usunięcia tego posta."}, status=status.HTTP_401_UNAUTHORIZED)
            post.delete()

            return Response({"detail": "Post został usunięty."}, status=status.HTTP_204_NO_CONTENT)

        except Post.DoesNotExist:
            return Response({"detail": "Post nie został znaleziony."}, status=status.HTTP_404_NOT_FOUND)


class CurrentUserPostsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        posts = Post.objects.filter(created_by=user)

        data = [{
            "id": post.id,
            "title": post.title,
            "created_at": post.created_at,
            "status": post.status.name,
            "content": post.content,
            "author": {
                "id": post.created_by.id,
                "first_name": post.created_by.first_name,
                "last_name": post.created_by.last_name,
                "image": post.created_by.userdata.image.url
            }
        }
            for post in posts]

        return Response(data, status=status.HTTP_200_OK)



class TemplateListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        templates = Template.objects.all()
        serializer = TemplateSerializer(templates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        movie_id = request.query_params.get('movie_id', None)
        created_by_id = request.query_params.get('created_by_id', None)

        posts = Post.objects.all().order_by('-created_at').filter(status__id__gt=0)

        if movie_id:
            posts = posts.filter(movie_id=movie_id)

        if created_by_id:
            posts = posts.filter(created_by_id=created_by_id)

        data = [{
                 "id": post.id,
                 "title": post.title,
                 "created_at": post.created_at,
                 "status": post.status.name,
                 "content": post.content,
                 "author": {
                     "id": post.created_by.id,
                     "first_name": post.created_by.first_name,
                     "last_name": post.created_by.last_name,
                     "image": post.created_by.userdata.image.url
                 }
                 }
                for post in posts]

        return Response(data, status=status.HTTP_200_OK)


class PostDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            post = Post.objects.get(id=id)
            post_templates = PostTemplate.objects.filter(post=post).order_by('order')
            templates_data = []

            for post_template in post_templates:
                template_data = {
                    'template_id': post_template.template.id,
                    'order': post_template.order,
                    'fields': []
                }

                fields = PostTemplateTemplateField.objects.filter(post_template=post_template)
                for field in fields:
                    field_data = {
                        'field_id': field.field.id,
                        'name': field.field.name,
                        'content': field.content
                    }
                    template_data['fields'].append(field_data)

                templates_data.append(template_data)

            response_data = {
                'title': post.title,
                'status': post.status.name if post.status else None,
                'content': post.content,
                'movie_id': post.movie.id if post.movie else None,
                'templates': templates_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Post.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)


class UploadImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('image')

        errors = _validate_image(file)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        file = _rename_image_file(file)
        file = _resize_image(file)

        user_folder = os.path.join(settings.MEDIA_ROOT, f'user/{request.user.id}/images/')
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        file_path = os.path.join(user_folder, file.name)

        if os.path.exists(file_path):
            return Response(
                {"error": f"File with name {file.name} already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        file_url = os.path.join(settings.MEDIA_URL, f'user/{request.user.id}/images/{file.name}')
        return Response({"image_url": file_url}, status=status.HTTP_201_CREATED)


class UserImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_folder = os.path.join(settings.MEDIA_ROOT, f'user/{request.user.id}/images/')
        if not os.path.exists(user_folder):
            return Response({"images": []}, status=status.HTTP_200_OK)

        files = os.listdir(user_folder)
        file_urls = [os.path.join(settings.MEDIA_URL, f'user/{request.user.id}/images/', file) for file in files]
        return Response({"images": file_urls}, status=status.HTTP_200_OK)

    def delete(self, request):
        file_path = request.data.get('file_path')

        if not file_path:
            return Response({"error": "Brak ścieżki do pliku w żądaniu."}, status=status.HTTP_400_BAD_REQUEST)

        user_folder = os.path.join(settings.MEDIA_ROOT, f'user/{request.user.id}/images/')
        abs_file_path = os.path.join(settings.MEDIA_ROOT, file_path.lstrip(settings.MEDIA_URL))

        if not abs_file_path.startswith(user_folder):
            return Response({"error": "Plik nie należy do katalogu użytkownika."}, status=status.HTTP_403_FORBIDDEN)

        if not os.path.exists(abs_file_path):
            return Response({"error": "Plik nie istnieje."}, status=status.HTTP_404_NOT_FOUND)

        try:
            os.remove(abs_file_path)
        except Exception as e:
            return Response({"error": f"Wystąpił błąd podczas usuwania pliku: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Plik został pomyślnie usunięty."}, status=status.HTTP_200_OK)