from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from blog.forms import PostForm, CommentForm
from blog.models import Post, Comment


class CommentMixin:
    form_class = CommentForm
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class DispatchNeededMixin:

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        view_name = request.resolver_match.view_name
        dispatch_dict = {
                'blog:edit_comment': dispatch_comment,
                'blog:delete_comment': dispatch_comment,
                #  'blog:edit_post': dispatch_post_edit,
                'blog:delete_post': dispatch_post_delete,
                'blog:edit_profile': dispatch_user_edit,
                         }
        for view_url in dispatch_dict:
            if view_name == view_url:
                dispatch_dict[view_url](self, request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


def dispatch_comment(self, request: HttpRequest, *args, **kwargs):
    comment = get_object_or_404(self.model, pk=self.kwargs['post_id'])
    if comment.author != request.user:
        raise PermissionDenied


#  def dispatch_post_edit(self, request: HttpRequest, *args, **kwargs):
#      instance = Post.objects.get(pk=self.kwargs['post_id'])
#      if not request.user.is_authenticated:
#          return HttpResponseForbidden()
#      if instance.author != request.user:
#          return redirect('blog:post_detail', pk=self.kwargs['post_id'])


def dispatch_post_delete(self, request: HttpRequest, *args, **kwargs):
    post = get_object_or_404(self.model, pk=self.kwargs['post_id'])
    if post.author != request.user:
        raise PermissionDenied


def dispatch_user_edit(self, request: HttpRequest, *args, **kwargs):
    instance = get_object_or_404(User, pk=self.kwargs['pk'])
    if instance.id != request.user.id:
        raise PermissionDenied


class PostMixin:
    context_object_name = 'page_obj'
    model = Post


class PostModelMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'