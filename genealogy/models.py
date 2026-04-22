from django.db import models


class FamilyMember(models.Model):
    class Branch(models.TextChoices):
        CANH_TRUONG = 'canh_truong', 'Canh tr??ng'
        CANH_2 = 'canh_2', 'Canh 2'
        CANH_3 = 'canh_3', 'Canh 3'
        CANH_4 = 'canh_4', 'Canh 4'
        CANH_5 = 'canh_5', 'Canh 5'

    class Gender(models.TextChoices):
        MALE = 'male', 'Nam'
        FEMALE = 'female', 'N?'
        OTHER = 'other', 'Khac'

    full_name = models.CharField('H? va ten', max_length=150)
    parent = models.ForeignKey(
        'self',
        verbose_name='Thanh vien ??i tr??c',
        related_name='children',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    spouse_name = models.CharField('Ten v?/ch?ng', max_length=150, blank=True)
    father_name = models.CharField('Ten cha', max_length=150, blank=True)
    mother_name = models.CharField('Ten m?', max_length=150, blank=True)
    gender = models.CharField('Gi?i tinh', max_length=10, choices=Gender.choices, default=Gender.OTHER)
    branch = models.CharField('Canh h?', max_length=20, choices=Branch.choices, default=Branch.CANH_TRUONG)
    generation = models.PositiveIntegerField('??i th?', default=1)
    birth_year = models.PositiveIntegerField('N?m sinh', null=True, blank=True)
    death_year = models.PositiveIntegerField('N?m m?t', null=True, blank=True)
    hometown = models.CharField('Que quan', max_length=150, blank=True)
    occupation = models.CharField('Ngh? nghi?p', max_length=150, blank=True)
    achievements = models.TextField('Cong danh', blank=True)
    education = models.CharField('Trinh ??', max_length=150, blank=True)
    biography = models.TextField('Ti?u s? ng?n', blank=True)
    notes = models.TextField('Ghi chu', blank=True)
    is_highlighted = models.BooleanField('N?i b?t ? trang gi?i thi?u', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Thanh vien gia ph?'
        verbose_name_plural = 'Thanh vien gia ph?'
        ordering = ['branch', 'generation', 'full_name']

    def __str__(self):
        return self.full_name

    @property
    def lifespan(self):
        if self.birth_year and self.death_year:
            return f'{self.birth_year} - {self.death_year}'
        if self.birth_year:
            return f'Sinh n?m {self.birth_year}'
        return 'Ch?a c?p nh?t n?m sinh'


class Article(models.Model):
    title = models.CharField('Tieu ??', max_length=200)
    content = models.TextField('N?i dung')
    author = models.CharField('Tac gi?', max_length=120)
    image_url = models.URLField('Hinh ?nh', blank=True)
    image = models.FileField('T?i ?nh len', upload_to='articles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bai vi?t'
        verbose_name_plural = 'Bai vi?t'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url


class ArticleComment(models.Model):
    article = models.ForeignKey(
        Article,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Bai vi?t',
    )
    commenter_name = models.CharField('Ten ng??i binh lu?n', max_length=120)
    content = models.TextField('N?i dung binh lu?n')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Binh lu?n bai vi?t'
        verbose_name_plural = 'Binh lu?n bai vi?t'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.commenter_name} - {self.article.title}'
