from django.contrib import admin

from .models import Article, ArticleComment, FamilyMember

try:
    from import_export import fields as import_export_fields, resources
    from import_export.admin import ImportExportModelAdmin
    from import_export.widgets import ForeignKeyWidget
except ModuleNotFoundError:
    resources = None
    import_export_fields = None
    ForeignKeyWidget = None
    ImportExportModelAdmin = admin.ModelAdmin


if resources is not None:
    class FamilyMemberResource(resources.ModelResource):
        parent = import_export_fields.Field(
            column_name='parent',
            attribute='parent',
            widget=ForeignKeyWidget(FamilyMember, 'full_name'),
        )

        EXPORT_FIELDS = (
            'id',
            'full_name',
            'parent',
            'father_name',
            'mother_name',
            'spouse_name',
            'gender',
            'generation',
            'birth_year',
            'death_year',
            'hometown',
            'occupation',
            'achievements',
            'education',
            'biography',
            'notes',
            'is_highlighted',
        )

        class Meta:
            model = FamilyMember
            fields = FamilyMemberResource.EXPORT_FIELDS
            export_order = FamilyMemberResource.EXPORT_FIELDS
            import_id_fields = ('id',)
            skip_unchanged = True
            report_skipped = True


@admin.register(FamilyMember)
class FamilyMemberAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'generation', 'parent', 'gender', 'birth_year', 'is_highlighted')
    list_filter = ('generation', 'gender', 'is_highlighted')
    search_fields = ('full_name', 'spouse_name', 'hometown', 'biography')
    autocomplete_fields = ('parent',)

    if resources is not None:
        resource_classes = [FamilyMemberResource]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'author', 'content')


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('commenter_name', 'article', 'created_at')
    search_fields = ('commenter_name', 'content', 'article__title')


admin.site.site_header = 'Quan tri gia pha'
admin.site.site_title = 'Admin gia pha'
admin.site.index_title = 'Quan ly du lieu gia pha'
