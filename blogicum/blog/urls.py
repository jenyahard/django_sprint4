from blog import views
from blog.apps import BlogConfig

from django.urls import path


app_name = BlogConfig.name

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('posts/<int:pk>/comment/',
         views.AddCommentView.as_view(),
         name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<comment_id>/',
         views.EditCommentView.as_view(),
         name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<comment_id>/',
         views.DeleteCommentView.as_view(),
         name='delete_comment'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path('posts/<int:post_id>/edit/',
         views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/<int:post_id>/delete/',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('posts/<int:pk>/',
         views.PostDetailView.as_view(),
         name='post_detail'),
    path('posts/edit/<int:pk>/',
         views.UserUpdateView.as_view(),
         name='edit_profile'),
    path('profile/<username>/',
         views.ProfileView.as_view(),
         name='profile'),
    path('category/<slug:category_slug>/',
         views.CategoryPostsView.as_view(),
         name='category_posts'),
]
