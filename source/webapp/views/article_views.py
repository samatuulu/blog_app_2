from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import urlencode
from django.views.generic import ListView, DetailView, CreateView, \
    UpdateView, DeleteView

from webapp.forms import ArticleForm, ArticleCommentForm, SimpleSearchForm
from webapp.models import Article, STATUS_ARCHIVED, STATUS_ACTIVE, Tag
from django.core.paginator import Paginator


class IndexView(ListView):
    context_object_name = 'articles'
    model = Article
    template_name = 'article/index.html'
    ordering = ['-created_at']
    paginate_by = 3
    paginate_orphans = 1

    def get(self, request, *args, **kwargs):
        self.form = self.get_search_form()
        self.search_value = self.get_search_value()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['form'] = self.form
        # context['archived_articles'] = self.model.objects.filter(status__icontains=STATUS_ARCHIVED)
        # context['active_articles'] = self.model.objects.filter(status__icontains=STATUS_ACTIVE)
        if self.search_value:
            context['query'] = urlencode({'search': self.search_value})
        tag_filter = self.request.GET
        if 'tag' in tag_filter:
            context['articles'] = Article.objects.filter(tags__name=tag_filter.get('tag'))
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.search_value:
            query = Q(tags__name__iexact=self.search_value)
            queryset = queryset.filter(query)
        return queryset

    def get_search_form(self):
        return SimpleSearchForm(self.request.GET)

    def get_search_value(self):
        if self.form.is_valid():
            return self.form.cleaned_data['search']
        return None


class ArticleView(DetailView):
    template_name = 'article/article.html'
    model = Article
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ArticleCommentForm()
        comments = context['article'].comments.order_by('-created_at')
        self.paginate_comments_to_context(comments, context)
        return context

    def paginate_comments_to_context(self, comments, context):
        paginator = Paginator(comments, 3, 0)
        page_number = self.request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        context['paginator'] = paginator
        context['page_obj'] = page
        context['comments'] = page.object_list
        context['is_paginated'] = page.has_other_pages()


class ArticleCreateView(CreateView):
    model = Article
    template_name = 'article/create.html'
    form_class = ArticleForm

    def tag_post(self):
        tags = self.request.POST.get('tags')
        tag_list = tags.split(',')

        for tag in tag_list:
            tags, created = Tag.objects.get_or_create(name=tag)
            self.object.tags.add(tags)

    def form_valid(self, form):
        self.object = form.save()
        self.tag_post()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('article_view', kwargs={'pk': self.object.pk})


class ArticleUpdateView(UpdateView):
    model = Article
    template_name = 'article/update.html'
    context_object_name = 'article'
    form_class = ArticleForm

    def tag_post(self):
        tags = self.request.POST.get('tags')
        tag_list = tags.split(',')
        self.object.tags.clear()
        for tag in tag_list:
            tags, created = Tag.objects.get_or_create(name=tag)
            self.object.tags.add(tags)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=None)
        tags = self.object.tags.all().values('name')
        line = ''
        print(tags)
        for tag in tags:
            line += tag.get('name') + ','
        form.fields['tags'].initial = line
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.tag_post()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('article_view', kwargs={'pk': self.object.pk})


class ArticleDeleteView(DeleteView):
    model = Article
    template_name = 'article/delete.html'
    context_object_name = 'article'
    success_url = reverse_lazy('index')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = STATUS_ARCHIVED
        self.object.save()
        print(self.object.status)
        return redirect(self.get_success_url())


