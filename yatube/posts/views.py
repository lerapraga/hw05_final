from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .settings import PER_PAGE


def index(request):
    '''для главной страницы'''
    posts = Post.objects.all()[:PER_PAGE]
    # Показывать по 10 записей на странице.
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PER_PAGE)
    template = 'posts/index.html'
    description = 'Небольшое описание'
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'description': description
    }
    return render(request, template, context)


def group_posts(request, slug):
    '''для страницы, на которой будут посты, отфильтрованные по группам.'''
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    text = 'Здесь будет информация о группах проекта Yatube'
    description = 'Небольшое описание'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'text': text,
        'page_obj': page_obj,
        'description': description
    }
    return render(request, template, context)


def profile(request, username):
    user_author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=user_author)
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_number = post_list.count()
    context = {'post_list': post_list,
               'page_obj': page_obj,
               'post_number': post_number,
               'author': user_author,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()  # type: ignore
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk,)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post.pk,)
    is_edit = True
    context = {'form': form, 'is_edit': is_edit}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    object = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if author != request.user and not object:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    object = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if author != request.user and object:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
