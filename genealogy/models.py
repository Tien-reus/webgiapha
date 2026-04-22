from django.db import models


class FamilyMember(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Nam'
        FEMALE = 'female', 'Nữ'
        OTHER = 'other', 'Khác'

    full_name = models.CharField('Họ và tên', max_length=150)
    parent = models.ForeignKey(
        'self',
        verbose_name='Thành viên đời trước',
        related_name='children',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    spouse_name = models.CharField('Tên vợ/chồng', max_length=150, blank=True)
    father_name = models.CharField('Tên cha', max_length=150, blank=True)
    mother_name = models.CharField('Tên mẹ', max_length=150, blank=True)
    gender = models.CharField(
        'Giới tính',
        max_length=10,
        choices=Gender.choices,
        default=Gender.OTHER,
    )
    generation = models.PositiveIntegerField('Đời thứ', default=1)
    birth_year = models.PositiveIntegerField('Năm sinh', null=True, blank=True)
    death_year = models.PositiveIntegerField('Năm mất', null=True, blank=True)
    hometown = models.CharField('Quê quán', max_length=150, blank=True)
    occupation = models.CharField('Nghề nghiệp', max_length=150, blank=True)
    achievements = models.TextField('Công danh', blank=True)
    education = models.CharField('Trình độ', max_length=150, blank=True)
    biography = models.TextField('Tiểu sử ngắn', blank=True)
    notes = models.TextField('Ghi chú', blank=True)
    is_highlighted = models.BooleanField('Nổi bật ở trang giới thiệu', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Thành viên gia phả'
        verbose_name_plural = 'Thành viên gia phả'
        ordering = ['generation', 'full_name']

    def __str__(self):
        return self.full_name

    @property
    def lifespan(self):
        if self.birth_year and self.death_year:
            return f'{self.birth_year} - {self.death_year}'
        if self.birth_year:
            return f'Sinh năm {self.birth_year}'
        return 'Chưa cập nhật năm sinh'


class Article(models.Model):
    title = models.CharField('Tiêu đề', max_length=200)
    content = models.TextField('Nội dung')
    author = models.CharField('Tác giả', max_length=120)
    image_url = models.URLField('Hình ảnh', blank=True)
    image = models.FileField('Tải ảnh lên', upload_to='articles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bài viết'
        verbose_name_plural = 'Bài viết'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def display_image(self):
        if self.image:
            try:
                if self.image.storage.exists(self.image.name):
                    return self.image.url
            except Exception:
                pass
        return self.image_url


class ArticleComment(models.Model):
    article = models.ForeignKey(
        Article,
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Bài viết',
    )
    commenter_name = models.CharField('Tên người bình luận', max_length=120)
    content = models.TextField('Nội dung bình luận')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bình luận bài viết'
        verbose_name_plural = 'Bình luận bài viết'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.commenter_name} - {self.article.title}'
