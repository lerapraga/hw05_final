from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment, Post

User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {'text': 'Текст поста',
                  'group': 'Группа',
                  'image': 'Картинка'}
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка для поста'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(),
        }
