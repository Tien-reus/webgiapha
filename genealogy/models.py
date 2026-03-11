from django.db import models


class FamilyMember(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Nam'
        FEMALE = 'female', 'Nu'
        OTHER = 'other', 'Khac'

    full_name = models.CharField('Ho va ten', max_length=150)
    parent = models.ForeignKey(
        'self',
        verbose_name='Thanh vien doi truoc',
        related_name='children',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    spouse_name = models.CharField('Ten vo chong', max_length=150, blank=True)
    gender = models.CharField(
        'Gioi tinh',
        max_length=10,
        choices=Gender.choices,
        default=Gender.OTHER,
    )
    generation = models.PositiveIntegerField('Doi thu', default=1)
    birth_year = models.PositiveIntegerField('Nam sinh', null=True, blank=True)
    death_year = models.PositiveIntegerField('Nam mat', null=True, blank=True)
    hometown = models.CharField('Que quan', max_length=150, blank=True)
    biography = models.TextField('Tieu su ngan', blank=True)
    is_highlighted = models.BooleanField('Noi bat o trang gioi thieu', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Thanh vien gia pha'
        verbose_name_plural = 'Thanh vien gia pha'
        ordering = ['generation', 'full_name']

    def __str__(self):
        return self.full_name

    @property
    def lifespan(self):
        if self.birth_year and self.death_year:
            return f'{self.birth_year} - {self.death_year}'
        if self.birth_year:
            return f'Sinh nam {self.birth_year}'
        return 'Chua cap nhat nam sinh'


class Article(models.Model):
    title = models.CharField('Tieu de', max_length=200)
    content = models.TextField('Noi dung')
    author = models.CharField('Tac gia', max_length=120)
    image_url = models.URLField('Hinh anh', blank=True)
    image = models.FileField('Tai anh len', upload_to='articles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bai viet'
        verbose_name_plural = 'Bai viet'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url
