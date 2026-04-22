import csv
import io
from urllib.request import urlopen, Request
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.core.exceptions import RequestDataTooBig
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
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


def export_members_csv_response():
    members = FamilyMember.objects.select_related('parent').order_by('generation', 'full_name')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="family_members.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(
        [
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
        ]
    )
    for member in members:
        writer.writerow(
            [
                member.id,
                member.full_name,
                member.parent.full_name if member.parent else '',
                member.father_name,
                member.mother_name,
                member.spouse_name,
                member.gender,
                member.generation,
                member.birth_year or '',
                member.death_year or '',
                member.hometown,
                member.occupation,
                member.achievements,
                member.education,
                member.biography,
                member.notes,
                'True' if member.is_highlighted else 'False',
            ]
        )
    return response


def _import_members_from_csv_text(text):
    created = 0
    updated = 0
    skipped = 0
    failed = 0

    csv.field_size_limit(10_000_000)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return created, updated, skipped, failed + 1

    for row in reader:
        try:
            full_name = (row.get('full_name') or '').strip()
            if not full_name:
                skipped += 1
                continue

            parent_name = (row.get('parent') or '').strip()
            parent = None
            if parent_name:
                parent = FamilyMember.objects.filter(full_name=parent_name).first()

            def to_int(value, default=None):
                value = (value or '').strip()
                if not value:
                    return default
                try:
                    return int(value)
                except ValueError:
                    return default

            payload = {
                'full_name': full_name[:150],
                'parent': parent,
                'father_name': (row.get('father_name') or '').strip()[:150],
                'mother_name': (row.get('mother_name') or '').strip()[:150],
                'spouse_name': (row.get('spouse_name') or '').strip()[:150],
                'gender': (row.get('gender') or 'other').strip() or 'other',
                'generation': to_int(row.get('generation'), 1) or 1,
                'birth_year': to_int(row.get('birth_year')),
                'death_year': to_int(row.get('death_year')),
                'hometown': (row.get('hometown') or '').strip()[:150],
                'occupation': (row.get('occupation') or '').strip()[:150],
                'achievements': (row.get('achievements') or '').strip(),
                'education': (row.get('education') or '').strip()[:150],
                'biography': (row.get('biography') or '').strip(),
                'notes': (row.get('notes') or '').strip(),
                'is_highlighted': (row.get('is_highlighted') or '').strip().lower() in {'1', 'true', 'yes', 'on'},
            }

            if payload['gender'] not in {'male', 'female', 'other'}:
                payload['gender'] = 'other'

            row_id = to_int(row.get('id'))
            if row_id:
                obj = FamilyMember.objects.filter(pk=row_id).first()
                if obj:
                    for key, value in payload.items():
                        setattr(obj, key, value)
                    obj.save()
                    updated += 1
                    continue

            existing = FamilyMember.objects.filter(full_name=full_name, birth_year=payload['birth_year']).first()
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.save()
                updated += 1
            else:
                FamilyMember.objects.create(**payload)
                created += 1
        except Exception:
            failed += 1

    return created, updated, skipped, failed


def import_members_from_csv(uploaded_file):
    raw = uploaded_file.read()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    return _import_members_from_csv_text(text)


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

    for children in nodes_by_parent.values():
        # Stable family order: by birth year, then creation order (id).
        children.sort(key=lambda m: (m.birth_year or 9999, m.id))

    for member in members:
        if member.parent_id is None:
            roots.append(build_tree(nodes_by_parent, member))

    roots.sort(key=lambda node: (node['member'].birth_year or 9999, node['member'].id))

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


def member_detail(request, pk):
    member = get_object_or_404(FamilyMember.objects.select_related('parent'), pk=pk)
    children = list(member.children.order_by('birth_year', 'id').values_list('full_name', 'birth_year'))

    father_name = member.father_name or (member.parent.full_name if member.parent else '')
    payload = {
        'id': member.id,
        'full_name': member.full_name,
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

        if action == 'export_members_csv':
            return export_members_csv_response()

        if action == 'import_members_csv':
            try:
                uploaded = request.FILES.get('members_csv')
                if not uploaded:
                    messages.error(request, 'Vui long chon file CSV truoc khi import.')
                    return redirect('manage_members')
                created, updated, skipped, failed = import_members_from_csv(uploaded)
                messages.success(
                    request,
                    f'Import xong: tao moi {created}, cap nhat {updated}, bo qua {skipped}, loi {failed}.',
                )
            except RequestDataTooBig:
                messages.error(request, 'File qua lon. Hay tach CSV nho hon (duoi 25MB) roi import lai.')
            except UnicodeDecodeError:
                messages.error(request, 'File khong dung UTF-8. Hay luu Excel thanh CSV UTF-8 roi import lai.')
            except Exception:
                messages.error(request, 'Import loi. Vui long kiem tra dinh dang CSV va thu lai.')
            return redirect('manage_members')

        if action == 'import_members_csv_text':
            text = (request.POST.get('members_csv_text') or '').strip()
            if not text:
                messages.error(request, 'Vui long dan noi dung CSV.')
                return redirect('manage_members')
            try:
                created, updated, skipped, failed = _import_members_from_csv_text(text)
                messages.success(
                    request,
                    f'Import xong: tao moi {created}, cap nhat {updated}, bo qua {skipped}, loi {failed}.',
                )
            except Exception:
                messages.error(request, 'Import loi. Vui long kiem tra CSV va thu lai.')
            return redirect('manage_members')

        if action == 'import_members_csv_url':
            csv_url = (request.POST.get('members_csv_url') or '').strip()
            if not csv_url:
                messages.error(request, 'Vui long nhap link CSV.')
                return redirect('manage_members')
            try:
                req = Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=20) as resp:
                    raw = resp.read(25 * 1024 * 1024 + 1)
                if len(raw) > 25 * 1024 * 1024:
                    messages.error(request, 'File CSV qua lon (toi da 25MB).')
                    return redirect('manage_members')
                try:
                    text = raw.decode('utf-8-sig')
                except UnicodeDecodeError:
                    text = raw.decode('cp1252')
                created, updated, skipped, failed = _import_members_from_csv_text(text)
                messages.success(
                    request,
                    f'Import tu link xong: tao moi {created}, cap nhat {updated}, bo qua {skipped}, loi {failed}.',
                )
            except Exception:
                messages.error(request, 'Khong doc duoc link CSV. Kiem tra link public va thu lai.')
            return redirect('manage_members')

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
