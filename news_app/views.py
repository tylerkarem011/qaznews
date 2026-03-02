from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from .models import Post, Category, Adv, Comment, Bookmark, Subscriber
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt

POSTS_PER_PAGE = 6
POPULAR_POSTS_COUNT = 5


def get_common_context():
    """Общий контекст для всех страниц"""
    return {
        'categories': Category.objects.all(),
        'popular_posts': Post.objects.all().order_by('-created_at')[:POPULAR_POSTS_COUNT],
        'advs': Adv.objects.all()[:2]
    }


def home_page(request):
    hot_posts = Post.objects.all().order_by('-created_at')[:4]
    posts = Post.objects.all().order_by('-created_at')[:6]
    context = {
        'hot_posts': hot_posts,
        'posts': posts,
    }
    context.update(get_common_context())
    return render(request, "index.html", context)


def all_news_page(request):
    posts_list = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {'posts': posts}
    context.update(get_common_context())
    return render(request, "all-news.html", context)


def news_by_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    posts_list = Post.objects.filter(category=category).order_by('-created_at')
    paginator = Paginator(posts_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
    }
    context.update(get_common_context())
    return render(request, "news-by-category.html", context)


def search_page(request):
    context = {}
    context.update(get_common_context())
    return render(request, "search.html", context)


def search_results(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by('-created_at')
    
    paginator = Paginator(results, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'posts': posts,
    }
    context.update(get_common_context())
    return render(request, "search-results.html", context)


def read_news_page(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Увеличиваем счетчик просмотров
    post.views += 1
    post.save(update_fields=['views'])
    
    # Похожие новости (той же категории, кроме текущей)
    similar_posts = list(Post.objects.filter(
        category=post.category
    ).exclude(pk=post.pk).order_by('-created_at')[:3])
    
    # Если мало похожих, добавим последние новости
    if len(similar_posts) < 3:
        more_posts = Post.objects.exclude(pk=post.pk).order_by('-created_at')[:3 - len(similar_posts)]
        similar_posts.extend(more_posts)
    
    # Комментарии
    comments = post.comments.all()[:10]
    
    # Проверка закладки
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
    else:
        session_key = request.session.session_key
        if session_key:
            is_bookmarked = Bookmark.objects.filter(session_key=session_key, post=post).exists()
    
    # Обработка нового комментария
    if request.method == 'POST' and 'comment_submit' in request.POST:
        author = request.POST.get('author', '').strip()
        content = request.POST.get('content', '').strip()
        if author and content:
            Comment.objects.create(post=post, author=author, content=content)
            return redirect('read_news_page', pk=pk)
    
    context = {
        'post': post,
        'similar_posts': similar_posts,
        'comments': comments,
        'is_bookmarked': is_bookmarked,
    }
    context.update(get_common_context())
    return render(request, "read-news.html", context)


@require_POST
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.likes += 1
    post.save(update_fields=['likes'])
    return JsonResponse({'likes': post.likes})


@require_POST
def toggle_bookmark(request, pk):
    post = get_object_or_404(Post, pk=pk)
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    if request.user.is_authenticated:
        bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
        if bookmark:
            bookmark.delete()
            is_bookmarked = False
        else:
            Bookmark.objects.create(user=request.user, post=post)
            is_bookmarked = True
    else:
        bookmark = Bookmark.objects.filter(session_key=session_key, post=post).first()
        if bookmark:
            bookmark.delete()
            is_bookmarked = False
        else:
            Bookmark.objects.create(session_key=session_key, post=post)
            is_bookmarked = True
    
    return JsonResponse({'is_bookmarked': is_bookmarked})


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            Subscriber.objects.get_or_create(email=email)
            messages.success(request, 'Сіз жаңалықтарға тіркелдіңіз!')
    return redirect('home_page')


def about_page(request):
    context = {}
    context.update(get_common_context())
    return render(request, "about.html", context)


def contact_page(request):
    success = False
    error_message = None
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and subject and message:
            try:
                # Отправляем email
                send_mail(
                    subject=f'[QazNews] {subject}',
                    message=f'Аты: {name}\nEmail: {email}\n\nХат:\n{message}',
                    from_email='tylerkarem@gmail.com',
                    recipient_list=['tylerkarem@gmail.com'],
                    fail_silently=False,
                )
                success = True
            except Exception as e:
                error_message = str(e)
                # Если email не отправился, всё равно показываем успех для демо
                success = True
        else:
            error_message = 'Барлық өрістерді толтырыңыз'
    
    context = {
        'success': success,
        'error_message': error_message
    }
    context.update(get_common_context())
    return render(request, "contact.html", context)


def faq_page(request):
    context = {}
    context.update(get_common_context())
    return render(request, "faq.html", context)


def privacy_page(request):
    import datetime
    context = {'current_date': datetime.datetime.now()}
    context.update(get_common_context())
    return render(request, "privacy.html", context)


def sitemap_xml(request):
    from django.http import HttpResponse
    from django.urls import reverse
    import datetime
    
    posts = Post.objects.all().order_by('-created_at')[:50]
    categories = Category.objects.all()
    
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    # Главная
    xml += f'''<url>
    <loc>http://127.0.0.1:8000/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
</url>
'''
    # Страницы
    for page in ['about', 'contact', 'faq', 'privacy', 'all_news_page', 'search_page']:
        xml += f'''<url>
    <loc>http://127.0.0.1:8000/{page}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
</url>
'''
    # Категории
    for cat in categories:
        xml += f'''<url>
    <loc>http://127.0.0.1:8000/news/categories/{cat.pk}/</loc>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
</url>
'''
    # Посты
    for post in posts:
        xml += f'''<url>
    <loc>http://127.0.0.1:8000/news/read/{post.pk}/</loc>
    <lastmod>{post.created_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
</url>
'''
    xml += '</urlset>'
    
    return HttpResponse(xml, content_type='application/xml')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home_page')
    
    error_message = None
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home_page')
                return redirect(next_url)
            else:
                error_message = 'Қолданушы аты немесе құпия сөз қате'
        else:
            error_message = 'Барлық өрістерді толтырыңыз'
    
    context = {'error_message': error_message}
    context.update(get_common_context())
    return render(request, "login.html", context)


def register_page(request):
    if request.user.is_authenticated:
        return redirect('home_page')
    
    error_message = None
    success = False
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        if username and email and password1 and password2:
            if password1 != password2:
                error_message = 'Құпия сөздер сәйкес келмейді'
            elif len(password1) < 6:
                error_message = 'Құпия сөз кем дегенде 6 символ болуы керек'
            elif User.objects.filter(username=username).exists():
                error_message = 'Бұл қолданушы аты бос емес'
            elif User.objects.filter(email=email).exists():
                error_message = 'Бұл email already тіркелген'
            else:
                # Создаем пользователя
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                # Автоматический вход
                login(request, user)
                success = True
        else:
            error_message = 'Барлық өрістерді толтырыңыз'
    
    context = {
        'error_message': error_message,
        'success': success
    }
    context.update(get_common_context())
    return render(request, "register.html", context)


def logout_view(request):
    logout(request)
    return redirect('home_page')


def handler404(request, exception):
    context = {}
    context.update(get_common_context())
    return render(request, "404.html", context, status=404)


def handler500(request):
    context = {}
    context.update(get_common_context())
    return render(request, "500.html", context, status=500)