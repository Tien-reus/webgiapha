from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Article, ArticleComment, FamilyMember


class ParentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        birth = f", sinh {obj.birth_year}" if obj.birth_year else ""
        return f"{obj.full_name} (ID {obj.id}, Đời {obj.generation}{birth})"


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = [
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
        ]
        widgets = {
            'biography': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_queryset = FamilyMember.objects.order_by('generation', 'full_name', 'id')
        self.fields['parent'] = ParentChoiceField(
            queryset=parent_queryset,
            required=False,
            label=self.fields['parent'].label,
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned_data = super().clean()
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
    username = forms.CharField(label='Tài khoản', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ArticleCommentForm(forms.ModelForm):
    class Meta:
        model = ArticleComment
        fields = ['commenter_name', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Nhập nội dung bình luận...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commenter_name'].widget.attrs.setdefault('class', 'form-control')
        self.fields['content'].widget.attrs.setdefault('class', 'form-control')
