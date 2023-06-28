from django.urls import path
from blog.apps import BlogConfig


from . import views

app_name = BlogConfig.name

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<comment_id>/',
         views.edit_comment,
         name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<comment_id>/',
         views.delete_comment,
         name='delete_comment'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path('posts/<int:post_id>/edit/',
         views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/<int:post_id>/delete/',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('posts/<int:pk>/',
         views.post_detail,
         name='post_detail'),
    path('posts/edit/<int:pk>/',
         views.UserUpdateView.as_view(),
         name='edit_profile'),
    path('profile/<username>/',
         views.profile_view,
         name='profile'),
    path('category/<slug:category_slug>/',
         views.category_posts,
         name='category_posts'),
]
