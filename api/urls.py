from django.urls import path
from .views import *


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('user/current/image/', UserDataView.as_view(), name='userdata'),
    path('user/current/images/', UserImagesView.as_view(), name='user-images-list'),
    path('user/current/posts/', CurrentUserPostsView.as_view(), name='user-posts-list'),
    path('user/current/', UserCurrentDetailView.as_view(), name='user-current-detail'),
    path('user/<int:id>', UserDetailView.as_view(), name='user-detail'),
    path('pages/', PageListView.as_view(), name='pages-list'),
    path('page/<int:pk>/', PageDetailView.as_view(), name='page-detail'),
    path('category/', CategoryListView.as_view(), name='category-list'),
    path('movies/', MovieListView.as_view(), name='movies-list'),
    path('movie/<int:id>/', MovieDetailView.as_view(), name='movie-detail'),
    path('upload/', UploadImageView.as_view(), name='upload-images'),
    path('post/', PostCreateView.as_view(), name='post-create'),
    path('post/details/<int:id>', PostDetailAPIView.as_view(), name='post-create'),
    path('post/<int:id>/', PostView.as_view(), name='post-detail'),
    path('templates/', TemplateListView.as_view(), name='template-list'),
    path('posts/', PostListView.as_view(), name='post-list'),
]
