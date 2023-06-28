from blog.models import Category
from blog.services import get_posts
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import CommentForm, PostForm, UserForm
from .models import Comment, Post


@login_required
def add_comment(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author_id = request.user.id
        comment.post_id = post.id
        comment.save()
    return redirect('blog:post_detail', pk=post.id)


@login_required
def edit_comment(request: HttpRequest,
                 post_id: int,
                 comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    form = CommentForm(initial={'text': comment.text})
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', pk=post_id)
    context = {
        'form': form,
        'comment': comment,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request: HttpRequest,
                   post_id: int,
                   comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)
    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)


def index(request: HttpRequest) -> HttpResponse:
    template = 'blog/index.html'
    posts = get_posts(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )
    for post in posts:
        post.comment_count = (Comment.objects.get_queryset()
                                             .filter(post_id=post.pk)
                                             .count()
                              )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    context = {'page_obj': posts}
    return render(request, template, context)


def post_detail(request: HttpRequest, pk: int) -> HttpResponse:
    template = 'blog/detail.html'
    post = get_object_or_404(get_posts(pk=pk,
                                       category__is_published=True,
                                       pub_date__lte=timezone.now(),
                                       is_published=True,)
                             )
    form = CommentForm()
    comments = (Comment.objects.get_queryset()
                               .filter(post_id=pk)
                               .order_by('created_at')
                )
    context = {'post': post,
               'form': form,
               'comments': comments,
               }
    return render(request, template, context)


def category_posts(request: HttpRequest, category_slug: str) -> HttpResponse:
    template = 'blog/category.html'
    category = get_object_or_404(Category,
                                 slug=category_slug,
                                 is_published=True,
                                 )
    page_obj = get_posts(category=category,
                         pub_date__lte=timezone.now(),
                         is_published=True,
                         )
    for post in page_obj:
        post.comment_count = (Comment.objects.get_queryset()
                                             .filter(post_id=post.pk)
                                             .count()
                              )
    paginator = Paginator(page_obj, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category,
               'page_obj': page_obj}
    return render(request, template, context)


def profile_view(request: HttpRequest, username: str) -> HttpResponse:
    profile = User.objects.get(username=username)
    page_obj = Post.objects.get_queryset().filter(author_id=profile.id)
    for post in page_obj:
        post.comment_count = (Comment.objects.get_queryset()
                                             .filter(post_id=post.pk)
                                             .count()
                              )
    template = 'blog/profile.html'
    paginator = Paginator(page_obj, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': profile,
               'page_obj': page_obj
               }
    return render(request, template, context)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy('blog:index')
    template_name = 'registration/registration_form.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=kwargs['pk'])
        if instance.id != request.user.id:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, AccessMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post_id = self.object.id
        return reverse_lazy('blog:post_detail', kwargs={'pk': post_id})

    def form_invalid(self, form):
        if not self.request.user.is_authenticated:
            return self.handle_no_permission()
        return super().form_invalid(form)

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy('blog:profile', kwargs={'username': username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['post_id'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])
