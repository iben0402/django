from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage,\
                                  PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from .models import Post, Comment
from .forms import EmailPostForm, CommentForm
from taggit.models import Tag


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3) # 3 posty na kazdej stronie
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Jeśli page nie jest liczbą całkowitą dostarcz pierwszą stronę
        posts = paginator.page(1)
    except EmptyPage:
        # Jeśli page wykracza poza zakres dostarcz ostatnią stronę wyników
        posts = paginator.page(paginator.num_pages)
    return render(request,
                 'blog/post/list.html',
                 {'page': page,
                  'posts': posts,
                  'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published',
                                   publish__year=year,
                                   publish__month=month,
                                   publish__day=day)

    # Lista aktywnych komentarzy dla tego posta
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # Opublikowano komentarz
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Utwórz obiekt Comment, ale nie zapisuj do bazy danych
            new_comment = comment_form.save(commit=False)
            # Przypisz bieżący post do komentarza
            new_comment.post = post
            # Zapisz komentarz do bazy danych
            new_comment.save()
    else:
        comment_form = CommentForm()

    # Lista podobnych postów
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                  .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                .order_by('-same_tags','-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form,
                   'similar_posts': similar_posts})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Pobierz post wg id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Formularz przesłano
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Pola formualarza zostały pomyślnie zwalidowane
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} poleca, żebyś przeczytał {post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"Komentarzy {cd['name']}: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True

    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})
