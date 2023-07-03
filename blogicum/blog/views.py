from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic import DetailView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.db.models import QuerySet
from django.http import HttpResponse, HttpRequest
from django.http import Http404
from django.forms import Form

from blog.services import queryset_annotate, get_comments, get_posts_author
from blog.services import get_posts, get_paginator, get_post_pk_comments
from blog.forms import CommentForm, UserForm
from blog.forms import PostForm
from blog.models import Comment, Post, Category
from blog.mixins import DispatchNeededMixin, CommentMixin
from blog.mixins import PostMixin, PostModelMixin


AMOUNT_OBJ_ON_ONE_PAGE = 10


class AddCommentView(LoginRequiredMixin, CommentMixin, CreateView):

    def form_valid(self, form: Form) -> HttpResponse:
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['pk']}
                            )


class EditCommentView(DispatchNeededMixin, CommentMixin, UpdateView):
    pk_url_kwarg = 'comment_id'

    def get_queryset(self) -> QuerySet[Comment]:
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']}
                            )

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context['post_id'] = self.kwargs['post_id']
        return context


class DeleteCommentView(DispatchNeededMixin, CommentMixin, DeleteView):
    pk_url_kwarg = 'comment_id'

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['post_id']}
                            )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.delete(request, *args, **kwargs)


class IndexView(PostMixin, ListView):
    template_name = 'blog/index.html'
    queryset = queryset_annotate(get_posts())

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context['page_obj'] = get_paginator(
            objects=self.queryset,
            page_number=self.request.GET.get('page'),
            posts_on_page=AMOUNT_OBJ_ON_ONE_PAGE,
        )
        return context


class PostDetailView(LoginRequiredMixin, DispatchNeededMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = get_post_pk_comments(self.kwargs['pk'])
        return context


class CategoryPostsView(PostMixin, ListView):
    template_name = 'blog/category.html'

    def get_queryset(self) -> QuerySet[Post]:
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(Category,
                                     slug=category_slug,
                                     is_published=True)
        if not category.is_published:
            raise Http404('Категория не опубликована')
        return queryset_annotate(get_posts()).filter(category=category,)

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(Category,
                                     slug=category_slug,
                                     is_published=True)
        context['page_obj'] = get_paginator(
            objects=context['page_obj'],
            page_number=self.request.GET.get('page'),
            posts_on_page=AMOUNT_OBJ_ON_ONE_PAGE,
        )
        context['category'] = category
        return context


class ProfileView(View):
    template_name = 'blog/profile.html'

    def get(self, request: HttpRequest, username: str) -> HttpResponse:
        profile = get_object_or_404(User, username=username)
        posts = queryset_annotate(get_posts_author(profile))
        context = {
            'profile': profile,
            'page_obj': get_paginator(
                objects=posts,
                page_number=self.request.GET.get('page'),
                posts_on_page=AMOUNT_OBJ_ON_ONE_PAGE,
            ),
            'comments': get_comments(profile),
        }
        return render(request, self.template_name, context)


class UserUpdateView(LoginRequiredMixin, DispatchNeededMixin, UpdateView):
    model = User
    form_class = UserForm
    success_url = reverse_lazy('blog:index')
    template_name = 'registration/registration_form.html'


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        instance = get_object_or_404(self.model, id=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.object.id})


class PostCreateView(LoginRequiredMixin, PostModelMixin, CreateView):

    def get_success_url(self) -> str:
        username = self.request.user.username
        return reverse_lazy('blog:profile',
                            kwargs={'username': username})

    def form_valid(self, form: Form) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(DispatchNeededMixin,
                     LoginRequiredMixin,
                     DeleteView):
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'
    model = Post
