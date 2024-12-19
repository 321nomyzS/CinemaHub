from django.urls import path
from .views import *

urlpatterns = [
    path('', main_page, name='main_page'),
    path('users', show_users, name='show_users'),
    path('user/add', add_user, name='add_user'),
    path('user/edit/<id>', edit_user, name='edit_user'),
    path('user/delete/<id>', delete_user, name='delete_user'),
    path('user/<id>', show_user, name='show_user'),
    path('posts', show_posts, name='show_posts'),
    path('post/raw/<id>', show_raw_post, name='show_raw_post'),
    path('post/delete/<id>', delete_post, name='delete_post'),
    path('post/<id>', show_post, name='show_post'),
    path('templates', show_templates, name='show_templates'),
    path('template/add', add_template, name='add_template'),
    path('template/edit/<id>', edit_template, name='edit_template'),
    path('template/delete/<id>', delete_template, name='delete_template'),
    path('template/<id>', show_template, name='show_template'),
    path('pages', show_pages, name='show_pages'),
    path('pages/edit', edit_pages, name='edit_pages'),
    path('page/add', add_page, name='add_page'),
    path('page/edit/<id>', edit_page, name='edit_page'),
    path('page/delete/<id>', delete_page, name='delete_page'),
    path('page/<id>', show_page, name='show_page'),
    path('movies', show_movies, name='show_movies'),
    path('movie/add', add_movie, name='add_movie'),
    path('movie/edit/<id>', edit_movie, name='edit_movie'),
    path('movie/delete/<id>', delete_movie, name='delete_movie'),
    path('movie/<id>', show_movie, name='show_movie'),
    path('members', show_members, name='show_members'),
    path('member/add', add_member, name='add_member'),
    path('member/edit/<id>', edit_member, name='edit_member'),
    path('member/delete/<id>', delete_member, name='delete_member'),
    path('member/<id>', show_member, name='show_member'),
    path('login', login_page, name='login'),
    path('logout', logout_tunnel, name='logout_tunnel')
]
