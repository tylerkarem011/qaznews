from django.db import models

class Category(models.Model):
    name = models.CharField("Категория атауы", max_length=100)
     
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField("Жаңалықтың тақырыбы", max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    content = models.TextField("Жаңалықтың сипаттамасы")
    image_url = models.CharField("Суреттің URL сілтемесі", max_length=500)
    views = models.IntegerField("Көргендер саны", default=0)
    likes = models.IntegerField("Лайктар саны", default=0)
    created_at = models.DateTimeField("Жариялау уақыты мен күні", auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.CharField("Автор", max_length=100)
    content = models.TextField("Пікір")
    created_at = models.DateTimeField("Уақыт", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author}: {self.content[:30]}..."


class Bookmark(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField("Уақыт", auto_now_add=True)

    def __str__(self):
        return f"Bookmark: {self.post.title}"


class Subscriber(models.Model):
    email = models.EmailField("Email", unique=True)
    is_active = models.BooleanField("Активный", default=True)
    created_at = models.DateTimeField("Тіркелген уақыт", auto_now_add=True)

    def __str__(self):
        return self.email

class Adv(models.Model):
    name = models.CharField("Компания аты", max_length=255, default="Company name")
    image_url = models.CharField("URL сілтемесі", max_length=500)

    def __str__(self):
        return self.name