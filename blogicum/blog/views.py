from typing import Dict, Any

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic import DetailView, ListView, View
from django.db.models import Count
from django.db.models import QuerySet
from django.http import HttpResponse, HttpRequest
from django.http import Http404

from blog.services import get_posts, paginator_custom, annotate
from blog.forms import CommentForm, PostForm, UserForm
from blog.models import Comment, Post, Category


class CommentAccessMixin(AccessMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PostIdMixin:
    def get_object(self) -> Post:
        return get_object_or_404(self.model, pk=self.kwargs['post_id'])


class ContextAndModelMixin:
    context_object_name = 'page_obj'
    model = Post


class PostModelMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['pk']}
                            )


class EditCommentView(LoginRequiredMixin, CommentAccessMixin, UpdateView):
    form_class = CommentForm

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']}
                            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_id'] = self.kwargs['post_id']
        return context


class DeleteCommentView(LoginRequiredMixin, CommentAccessMixin, DeleteView):

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']}
                            )

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class IndexView(ContextAndModelMixin, ListView):
    template_name = 'blog/index.html'

    def get_queryset(self) -> QuerySet[Post]:
        return get_posts()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_obj'] = paginator_custom(self, self.get_queryset())
        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self) -> Post:
        return get_object_or_404(self.model, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (Comment.objects
                               .filter(post_id=self.kwargs['pk'])
                               .order_by('created_at')
                               )
        return context


class CategoryPostsView(ContextAndModelMixin, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self) -> QuerySet[Post]:
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(Category,
                                     slug=category_slug,
                                     is_published=True)
        if not category.is_published:
            raise Http404('Категория не опубликована')
        return get_posts().filter(category=category,)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(Category,
                                     slug=category_slug,
                                     is_published=True)
        context['page_obj'] = paginator_custom(self, self.get_queryset())
        context['category'] = category
        return context


class ProfileView(View):
    template_name = 'blog/profile.html'

    def get(self, request: HttpRequest, username: str) -> HttpResponse:
        profile = get_object_or_404(User, username=username)
        posts = annotate(Post.objects.filter(author=profile))
        context = {
            'profile': profile,
            'page_obj': paginator_custom(self, posts),
            'comments': Comment.objects.filter(author=profile),
        }
        return render(request, self.template_name, context)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy('blog:index')
    template_name = 'registration/registration_form.html'

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        instance = get_object_or_404(User, pk=kwargs['pk'])
        if instance.id != request.user.id:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin,
                     PostModelMixin,
                     PostIdMixin,
                     UpdateView):

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        instance = self.get_object()
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.object.id})


class PostCreateView(LoginRequiredMixin, PostModelMixin, CreateView):

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy('blog:profile',
                            kwargs={'username': username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, PostModelMixin, PostIdMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
