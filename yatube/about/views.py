from django.views.generic import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = 'Автор проекта - Лара Павлова.'
        context['github'] = (
            '<a href="https://github.com/lerapraga">'
            'Ссылка на github</a>'
        )
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pycharm'] = 'Сайт написан VS Code - Insiders.'
        context['tech'] = 'Задействовала паджинатор, формы, декораторы и т.д.'
        return context
