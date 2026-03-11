from django import forms

from django.contrib.auth.forms import AuthenticationForm

from .models import Article, FamilyMember


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = [
            'full_name',
            'parent',
            'spouse_name',
            'gender',
            'generation',
            'birth_year',
            'death_year',
            'hometown',
            'biography',
            'is_highlighted',
        ]
        widgets = {
            'biography': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['parent'].queryset = FamilyMember.objects.order_by('generation', 'full_name')
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


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
    username = forms.CharField(label='Tai khoan', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Mat khau', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
