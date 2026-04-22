from pathlib import Path

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import JsonResponse
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


def build_forest(members):
    nodes_by_parent = {}
    roots = []
    members_by_id = {member.id: member for member in members}

    for member in members:
        parent_id = member.parent_id if member.parent_id in members_by_id else None
        nodes_by_parent.setdefault(parent_id, []).append(member)

    for children in nodes_by_parent.values():
        children.sort(key=lambda m: (m.birth_year or 9999, m.id))

    for member in members:
        if member.parent_id is None or member.parent_id not in members_by_id:
            roots.append(build_tree(nodes_by_parent, member))

    roots.sort(key=lambda node: (node['member'].generation, node['member'].birth_year or 9999, node['member'].id))
    return roots


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
    selected_branch = request.GET.get('branch', '').strip()
    members_qs = FamilyMember.objects.select_related('parent')

    valid_branches = {choice[0] for choice in FamilyMember.Branch.choices}
    if selected_branch in valid_branches:
        members_qs = members_qs.filter(branch=selected_branch)
    else:
        selected_branch = ''

    members = list(members_qs)
    roots = build_forest(members)

    context = {
        'tree': roots,
        'member_count': len(members),
        'branch_choices': FamilyMember.Branch.choices,
        'selected_branch': selected_branch,
    }
    return render(request, 'genealogy/family_tree.html', context)


def branches_outline(request):
    members = list(FamilyMember.objects.select_related('parent').order_by('generation', 'full_name'))
    grouped = []

    for branch_key, branch_label in FamilyMember.Branch.choices:
        branch_members = [member for member in members if member.branch == branch_key]
        grouped.append(
            {
                'key': branch_key,
                'label': branch_label,
                'count': len(branch_members),
                'tree': build_forest(branch_members),
            }
        )

    outline_path = Path(__file__).resolve().parent / 'data' / 'canh_ho_outline.txt'
    context = {
        'branches': grouped,
        'outline_text': outline_path.read_text(encoding='utf-8'),
    }
    return render(request, 'genealogy/branches_outline.html', context)


def member_detail(request, pk):
    member = get_object_or_404(FamilyMember.objects.select_related('parent'), pk=pk)
    children = list(member.children.order_by('birth_year', 'id').values_list('full_name', 'birth_year'))

    father_name = member.father_name or (member.parent.full_name if member.parent else '')
    payload = {
        'id': member.id,
        'full_name': member.full_name,
        'branch': member.get_branch_display(),
        'birth_year': member.birth_year,
        'death_year': member.death_year,
        'hometown': member.hometown,
        'father_name': father_name,
        'mother_name': member.mother_name,
        'spouse_name': member.spouse_name,
        'occupation': member.occupation,
        'achievements': member.achievements,
        'education': member.education,
        'notes': member.notes or member.biography,
        'generation': member.generation,
        'children': [{'full_name': n, 'birth_year': y} for n, y in children],
    }
    return JsonResponse(payload)


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        comment_form = ArticleCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.save()
            messages.success(request, '?a g?i binh lu?n.')
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
            messages.success(request, '?a xoa thanh vien kh?i danh sach.')
            return redirect('manage_members')

        if action == 'save_member':
            instance = get_object_or_404(FamilyMember, pk=request.POST.get('member_id')) if request.POST.get('member_id') else None
            form = FamilyMemberForm(request.POST, instance=instance)
            article_form = ArticleForm(instance=edit_article)
            if form.is_valid():
                saved = form.save()
                message = f'?a c?p nh?t thong tin cho {saved.full_name}.' if instance else f'?a them thanh vien {saved.full_name}.'
                messages.success(request, message)
                return redirect('manage_members')
        elif action == 'delete_article':
            article = get_object_or_404(Article, pk=request.POST.get('article_id'))
            article.delete()
            messages.success(request, '?a xoa bai vi?t.')
            return redirect('manage_members')
        elif action == 'save_article':
            instance = get_object_or_404(Article, pk=request.POST.get('article_id')) if request.POST.get('article_id') else None
            article_form = ArticleForm(request.POST, request.FILES, instance=instance)
            form = FamilyMemberForm(instance=edit_member)
            if article_form.is_valid():
                saved = article_form.save()
                message = f'?a c?p nh?t bai vi?t {saved.title}.' if instance else f'?a them bai vi?t {saved.title}.'
                messages.success(request, message)
                return redirect('manage_members')
    else:
        form = FamilyMemberForm(instance=edit_member)
        article_form = ArticleForm(instance=edit_article)

    members = FamilyMember.objects.select_related('parent').order_by('branch', 'generation', 'full_name')
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
            messages.success(request, '?a xoa bai vi?t.')
            return redirect('manage_articles')
        if action == 'save_article':
            instance = get_object_or_404(Article, pk=request.POST.get('article_id')) if request.POST.get('article_id') else None
            article_form = ArticleForm(request.POST, request.FILES, instance=instance)
            if article_form.is_valid():
                saved = article_form.save()
                message = f'?a c?p nh?t bai vi?t {saved.title}.' if instance else f'?a ??ng bai vi?t {saved.title}.'
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
    messages.success(request, '?a ??ng xu?t.')
    return redirect('about')
