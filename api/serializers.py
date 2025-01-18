from rest_framework import serializers
from dashboard.models import *


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']  # Hasło będzie automatycznie zahashowane
        )
        user_data = UserData.objects.create(
            user=user
        )
        user_data.save()

        return user


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = ['image']


class UserSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'image']
        read_only_fields = ['id', 'username', 'image']

    def get_image(self, obj):
        try:
            return obj.userdata.image.url
        except UserData.DoesNotExist:
            return None

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Username already exists")
        return value


class PageAuthorSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'image']

    def get_image(self, obj):
        try:
            return obj.userdata.image.url
        except UserData.DoesNotExist:
            return None


class PageSerializer(serializers.ModelSerializer):
    created_by = PageAuthorSerializer()

    class Meta:
        model = Page
        fields = '__all__'


class PagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'title', 'order']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = ['id', 'first_name', 'last_name', 'image']


class MoviesSerializer(serializers.ModelSerializer):
    director = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name')

    class Meta:
        model = Movie
        fields = ['id', 'title', 'release_date', 'description', 'poster', 'director', 'category']

    def get_director(self, obj):
        director = obj.crew_members.through.objects.filter(
            movie=obj, role_id=1
        ).select_related('crew_member').first()

        if director:
            return DirectorSerializer(director.crew_member).data
        return None


class CrewMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = '__all__'


class MovieCrewMemberSerializer(serializers.ModelSerializer):
    crew_member = CrewMemberSerializer()
    role = serializers.CharField(source='role.name')

    class Meta:
        model = MovieCrewMember
        fields = ['crew_member', 'role', 'character_name']


class MovieDetailSerializer(serializers.ModelSerializer):
    crew = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name')

    class Meta:
        model = Movie
        fields = ['id', 'title', 'release_date', 'description', 'poster', 'crew', 'category']

    def get_crew(self, obj):
        crew_members = MovieCrewMember.objects.filter(movie=obj).select_related('crew_member', 'role')
        return MovieCrewMemberSerializer(crew_members, many=True).data

class MovieOfCrewSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ['id', 'poster', 'roles']

    def get_roles(self, obj):
        crew_member = self.context.get('crew_member')
        if crew_member:
            credit_records = MovieCrewMember.objects.filter(movie=obj, crew_member=crew_member).select_related('role')
            roles = {credit.role.name for credit in credit_records}
            return list(roles)
        return None

class CrewDetailSerializer(serializers.ModelSerializer):
    movies = serializers.SerializerMethodField()
    class Meta:
        model = CrewMember
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'description', 'image', 'movies']

    def get_movies(self, obj):
        movies = Movie.objects.filter(moviecrewmember__crew_member_id=obj.id).distinct()
        return MovieOfCrewSerializer(movies, many=True, context={'crew_member': obj}).data

class PostCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=150)
    content = serializers.CharField(required=False, allow_blank=True)
    status = serializers.IntegerField()
    movie_id = serializers.IntegerField(required=False, allow_null=True)
    templates = serializers.ListField(
        child=serializers.DictField(
            child=serializers.JSONField()
        )
    )


class PostSerializer(serializers.ModelSerializer):
    created_by = PageAuthorSerializer()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'status', 'created_at', 'edited_at', 'published_at', 'movie', 'created_by']


class TemplateFieldSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = TemplateField
        fields = ['id', 'name', 'type']


class TemplateSerializer(serializers.ModelSerializer):
    fields = TemplateFieldSerializer(many=True)  # Dodajemy listę pól z nazwami typów

    class Meta:
        model = Template
        fields = ['id', 'name', 'description', 'html_structure', 'fields']



