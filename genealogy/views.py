from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from pathlib import Path
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminLoginForm, ArticleCommentForm, ArticleForm, FamilyMemberForm
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


def branches_outline(request):
    outline_path = Path(__file__).resolve().parent / 'data' / 'canh_ho_outline.txt'
    outline_text = outline_path.read_text(encoding='utf-8')
    context = {
        'outline_text': outline_text,
    }
    return render(request, 'genealogy/branches_outline.html', context)


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        comment_form = ArticleCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.save()
            messages.success(request, 'Đã gửi bình luận.')
            return redirect('article_detail', pk=article.pk)
    else:
        comment_form = ArticleCommentForm()

    context = {
        'article': article,
        'comments': article.comments.all(),
        'comment_form': comment_form,
    }
    return render(request, 'genealogy/article_detail.html', context)


@user_passes_test(is_admin_user, login_url='/login/')
def manage_members(request):
    member_edit_id = request.GET.get('edit_member')
    article_edit_id = request.GET.get('edit_article')
    member_query = (request.GET.get('member_q') or '').strip()
    article_query = (request.GET.get('article_q') or '').strip()
    edit_member = get_object_or_404(FamilyMember, pk=member_edit_id) if member_edit_id else None
    edit_article = get_object_or_404(Article, pk=article_edit_id) if article_edit_id else None

    if request.method == 'POST':
        action = request.POST.get('action', 'save_member')

        if action == 'delete_member':
            member = get_object_or_404(FamilyMember, pk=request.POST.get('member_id'))
            member.delete()
            messages.success(request, 'Đã xóa thành viên khỏi danh sách.')
            return redirect('manage_members')

        if action == 'save_member':
            instance = get_object_or_404(FamilyMember, pk=request.POST.get('member_id')) if request.POST.get('member_id') else None
            form = FamilyMemberForm(request.POST, instance=instance)
            article_form = ArticleForm(instance=edit_article)
            if form.is_valid():
                saved = form.save()
                message = f'Đã cập nhật thông tin cho {saved.full_name}.' if instance else f'Đã thêm thành viên {saved.full_name}.'
                messages.success(request, message)
                return redirect('manage_members')
        elif action == 'delete_article':
            article = get_object_or_404(Article, pk=request.POST.get('article_id'))
            article.delete()
            messages.success(request, 'Đã xóa bài viết.')
            return redirect('manage_members')
        elif action == 'save_article':
            instance = get_object_or_404(Article, pk=request.POST.get('article_id')) if request.POST.get('article_id') else None
            article_form = ArticleForm(request.POST, request.FILES, instance=instance)
            form = FamilyMemberForm(instance=edit_member)
            if article_form.is_valid():
                saved = article_form.save()
                message = f'Đã cập nhật bài viết {saved.title}.' if instance else f'Đã thêm bài viết {saved.title}.'
                messages.success(request, message)
                return redirect('manage_members')
    else:
        form = FamilyMemberForm(instance=edit_member)
        article_form = ArticleForm(instance=edit_article)

    members = FamilyMember.objects.select_related('parent').order_by('generation', 'full_name')
    if member_query:
        members = members.filter(
            Q(full_name__icontains=member_query)
            | Q(spouse_name__icontains=member_query)
            | Q(hometown__icontains=member_query)
            | Q(parent__full_name__icontains=member_query)
        )

    articles = Article.objects.all()
    if article_query:
        articles = articles.filter(
            Q(title__icontains=article_query)
            | Q(content__icontains=article_query)
            | Q(author__icontains=article_query)
        )

    context = {
        'form': form,
        'article_form': article_form,
        'edit_member': edit_member,
        'edit_article': edit_article,
        'members': members,
        'articles': articles,
        'member_query': member_query,
        'article_query': article_query,
    }
    return render(request, 'genealogy/manage_members.html', context)


@user_passes_test(is_admin_user, login_url='/login/')
def manage_articles(request):
    article_edit_id = request.GET.get('edit_article')
    article_query = (request.GET.get('article_q') or '').strip()
    edit_article = get_object_or_404(Article, pk=article_edit_id) if article_edit_id else None

    if request.method == 'POST':
        action = request.POST.get('action', 'save_article')
        if action == 'delete_article':
            article = get_object_or_404(Article, pk=request.POST.get('article_id'))
            article.delete()
            messages.success(request, 'Đã xóa bài viết.')
            return redirect('manage_articles')
        if action == 'save_article':
            instance = get_object_or_404(Article, pk=request.POST.get('article_id')) if request.POST.get('article_id') else None
            article_form = ArticleForm(request.POST, request.FILES, instance=instance)
            if article_form.is_valid():
                saved = article_form.save()
                message = f'Đã cập nhật bài viết {saved.title}.' if instance else f'Đã đăng bài viết {saved.title}.'
                messages.success(request, message)
                return redirect('manage_articles')
    else:
        article_form = ArticleForm(instance=edit_article)

    articles = Article.objects.all()
    if article_query:
        articles = articles.filter(
            Q(title__icontains=article_query)
            | Q(content__icontains=article_query)
            | Q(author__icontains=article_query)
        )

    context = {
        'article_form': article_form,
        'edit_article': edit_article,
        'articles': articles,
        'article_query': article_query,
    }
    return render(request, 'genealogy/manage_articles.html', context)


@user_passes_test(is_admin_user, login_url='/login/')
def admin_logout(request):
    logout(request)
    messages.success(request, 'Đã đăng xuất.')
    return redirect('about')
