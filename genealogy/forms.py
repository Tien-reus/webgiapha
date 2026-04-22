from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Article, ArticleComment, FamilyMember


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = [
            'full_name',
            'branch',
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
        ]
        widgets = {
            'biography': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].required = False
        self.fields['parent'].required = False
        self.fields['parent'].queryset = FamilyMember.objects.order_by('branch', 'generation', 'full_name')
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        if parent:
            # Keep branch + generation consistent with the selected parent.
            cleaned_data['branch'] = parent.branch
            cleaned_data['generation'] = parent.generation + 1

        full_name = (cleaned_data.get('full_name') or '').strip()
        branch = cleaned_data.get('branch')
        birth_year = cleaned_data.get('birth_year')
        if full_name and branch:
            duplicate_qs = FamilyMember.objects.filter(
                full_name__iexact=full_name,
                branch=branch,
                birth_year=birth_year,
            )
            if self.instance and self.instance.pk:
                duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)
            if duplicate_qs.exists():
                self.add_error(
                    'full_name',
                    'Thành viên này đã tồn tại trong cành họ (trùng họ tên và năm sinh).',
                )
        return cleaned_data


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'author', 'image', 'image_url']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(label='Tai kho?n', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='M?t kh?u', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ArticleCommentForm(forms.ModelForm):
    class Meta:
        model = ArticleComment
        fields = ['commenter_name', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Nh?p n?i dung binh lu?n...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commenter_name'].widget.attrs.setdefault('class', 'form-control')
        self.fields['content'].widget.attrs.setdefault('class', 'form-control')
