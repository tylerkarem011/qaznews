from django.urls import path
from django.conf.urls import handler404, handler500
from . import views

handler404 = views.handler404
handler500 = views.handler500

urlpatterns = [
    path('', views.home_page, name='home_page'),
    path('news/read/<int:pk>/', views.read_news_page, name='read_news_page'),
    path('news/search/', views.search_page, name='search_page'),
    path('news/search/results/', views.search_results, name='search_results'),
    path('news/all/', views.all_news_page, name='all_news_page'),
    path('news/categories/<int:pk>/', views.news_by_category, name='news_by_category'),
    path('news/like/<int:pk>/', views.like_post, name='like_post'),
    path('news/bookmark/<int:pk>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('about/', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('faq/', views.faq_page, name='faq_page'),
    path('privacy/', views.privacy_page, name='privacy_page'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('logout/', views.logout_view, name='logout_view'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]