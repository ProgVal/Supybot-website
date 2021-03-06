import hashlib

from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.forms import ModelForm
from django.http import Http404

from news.models import News
from news.models import NewsComment
from website.settings import LIBRAVATAR_URL

def get_libravatar_url(email):
    return LIBRAVATAR_URL % hashlib.md5(email.lower()).hexdigest()

def index(request):
    return redirect(listing, 1)

def listing(request, page):
    newsList = News.objects.filter(published=True)
    paginator = Paginator(list(newsList), 20)
    try:
        newsList = paginator.page(page)
    except:
        raise Http404()
    context = {'page': newsList}
    return render_to_response('news/listing.tpl', context)

class NewsCommentForm(ModelForm):
    class Meta:
        model = NewsComment
        fields = ('text',)

@csrf_protect
def read(request, slug):
    news = get_object_or_404(News, slug=slug, published=True)
    if request.method == 'POST':
        assert request.user.is_authenticated()
        form = NewsCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.key = news
            comment.user = request.user
            comment.save()
    # Fetch the comments after posting this one.
    comments = NewsComment.objects.filter(key=news)

    email = news.author.email
    url = get_libravatar_url(email)
    news.author.avatar = url
    url_cache = {email: url}
    for comment in comments:
        email = comment.user.email
        if email in url_cache:
            url = url_cache[email]
        else:
            url = get_libravatar_url(email)
            url_cache[email] = url
        comment.user.avatar = url
    context = {'news': news, 'user': request.user, 'comments': comments}
    context.update(csrf(request))
    return render_to_response('news/read.tpl', context)
