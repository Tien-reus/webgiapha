from django.contrib import admin

from .models import Article, ArticleComment, FamilyMember


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'generation', 'parent', 'gender', 'birth_year', 'is_highlighted')
    list_filter = ('generation', 'gender', 'is_highlighted')
    search_fields = ('full_name', 'spouse_name', 'hometown', 'biography')
    autocomplete_fields = ('parent',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'author', 'content')


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('commenter_name', 'article', 'created_at')
    search_fields = ('commenter_name', 'content', 'article__title')


admin.site.site_header = 'Quản trị gia phả'
admin.site.site_title = 'Admin gia phả'
admin.site.index_title = 'Quản lý dữ liệu gia phả'
