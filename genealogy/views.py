from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminLoginForm, ArticleForm, FamilyMemberForm
from .models import Article, FamilyMember


def is_admin_user(user):
    return user.is_authenticated and user.is_staff


class AdminLoginView(LoginView):
    template_name = 'genealogy/login.html'
    authentication_form = AdminLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.request.GET.get('next') or '/manage/'


def build_tree(nodes_by_parent, member):
    return {
        'member': member,
        'children': [build_tree(nodes_by_parent, child) for child in nodes_by_parent.get(member.id, [])],
    }


def about(request):
    members = FamilyMember.objects.all()
    context = {
        'member_count': members.count(),
        'generation_count': members.order_by().values('generation').distinct().count(),
        'featured_members': members.filter(is_highlighted=True)[:4],
        'articles': Article.objects.all()[:6],
    }
    return render(request, 'genealogy/about.html', context)


def family_tree(request):
    members = list(FamilyMember.objects.select_related('parent'))
    nodes_by_parent = {}
    roots = []

    for member in members:
        nodes_by_parent.setdefault(member.parent_id, []).append(member)

    for member in members:
        if member.parent_id is None:
            roots.append(build_tree(nodes_by_parent, member))

    context = {
        'tree': roots,
        'member_count': len(members),
    }
    return render(request, 'genealogy/family_tree.html', context)


@user_passes_test(is_admin_user, login_url='/login/')
def manage_members(request):
    member_edit_id = request.GET.get('edit_member')
    article_edit_id = request.GET.get('edit_article')
    edit_member = get_object_or_404(FamilyMember, pk=member_edit_id) if member_edit_id else None
    edit_article = get_object_or_404(Article, pk=article_edit_id) if article_edit_id else None

    if request.method == 'POST':
        action = request.POST.get('action', 'save_member')

        if action == 'delete_member':
            member = get_object_or_404(FamilyMember, pk=request.POST.get('member_id'))
            member.delete()
            messages.success(request, 'Da xoa thanh vien khoi danh sach.')
            return redirect('manage_members')

        if action == 'save_member':
            instance = get_object_or_404(FamilyMember, pk=request.POST.get('member_id')) if request.POST.get('member_id') else None
            form = FamilyMemberForm(request.POST, instance=instance)
            article_form = ArticleForm(instance=edit_article)
            if form.is_valid():
                saved = form.save()
                message = f'Da cap nhat thong tin cho {saved.full_name}.' if instance else f'Da them thanh vien {saved.full_name}.'
                messages.success(request, message)
                return redirect('manage_members')
        elif action == 'delete_article':
            article = get_object_or_404(Article, pk=request.POST.get('article_id'))
            article.delete()
            messages.success(request, 'Da xoa bai viet.')
            return redirect('manage_members')
        elif action == 'save_article':
            instance = get_object_or_404(Article, pk=request.POST.get('article_id')) if request.POST.get('article_id') else None
            article_form = ArticleForm(request.POST, request.FILES, instance=instance)
            form = FamilyMemberForm(instance=edit_member)
            if article_form.is_valid():
                saved = article_form.save()
                message = f'Da cap nhat bai viet {saved.title}.' if instance else f'Da them bai viet {saved.title}.'
                messages.success(request, message)
                return redirect('manage_members')
    else:
        form = FamilyMemberForm(instance=edit_member)
        article_form = ArticleForm(instance=edit_article)

    context = {
        'form': form,
        'article_form': article_form,
        'edit_member': edit_member,
        'edit_article': edit_article,
        'members': FamilyMember.objects.select_related('parent').order_by('generation', 'full_name'),
        'articles': Article.objects.all(),
    }
    return render(request, 'genealogy/manage_members.html', context)


@user_passes_test(is_admin_user, login_url='/login/')
def admin_logout(request):
    logout(request)
    messages.success(request, 'Da dang xuat.')
    return redirect('about')
