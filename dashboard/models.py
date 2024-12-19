from django.db import models
from django.contrib.auth.models import User


def user_directory_path(instance, filename):
    return f'user/{instance.user.id}/{filename}'


def member_directory_path(instance, filename):
    return f'member/{instance.id}/{filename}'


def movie_directory_path(instance, filename):
    return f'movie/{instance.id}/{filename}'


class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_directory_path, default='default/user.jpg')


class Role(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class CrewMember(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_date = models.DateField()
    description = models.TextField()
    image = models.ImageField(upload_to=member_directory_path, default='default/member.jpg')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=150)
    release_date = models.DateField()
    description = models.TextField()
    poster = models.ImageField(upload_to=movie_directory_path, default='default/movie.jpg')
    crew_members = models.ManyToManyField(
        CrewMember,
        through='MovieCrewMember',
        related_name='movies'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class MovieCrewMember(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    character_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.crew_member} as {self.role} in {self.movie}"


class Template(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    html_structure = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates')

    def __str__(self):
        return f"{self.id} {self.name}"


class FieldType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.id} {self.name}"


class TemplateField(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.ForeignKey(FieldType, on_delete=models.CASCADE, related_name='fields')
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='fields')

    def __str__(self):
        return f"{self.name} ({self.type.name})"


class Status(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.id} {self.name}"


class Post(models.Model):
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_full_html(self):
        post_templates = PostTemplate.objects.filter(post=self).order_by('order')
        full_html = ''

        for post_template in post_templates:
            template = post_template.template
            fields = PostTemplateTemplateField.objects.filter(post_template=post_template)
            template_html = template.html_structure

            for field in fields:
                placeholder = f'{{{{{field.field.name}}}}}'
                template_html = template_html.replace(placeholder, field.content or '')

            full_html += '\n' + template_html

        return full_html


class PostTemplate(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="templates")
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post: {self.post.title} - Template: {self.template.name}"


class PostTemplateTemplateField(models.Model):
    post_template = models.ForeignKey(PostTemplate, on_delete=models.CASCADE, related_name="template_fields")
    field = models.ForeignKey(TemplateField, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"PostTemplate: ({self.post_template}) - Field: {self.field.name}"


class Page(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    visibility = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.IntegerField()

    def __str__(self):
        return self.title
