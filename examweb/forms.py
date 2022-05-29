'''
forms.py - 表单程序
作者/anthor:liuyi585851
类型/type:后端文件-django文件-表单文件
描述/description:设置表单
使用方法/usage:
UserForm --> 用户登录表单
    username --> 准考证号 文本输入
    password --> 密码 文本输入
    captcha --> 验证码
MarkForm --> 成绩查询表单
    name --> 查询姓名 文本输入
    choice --> 查询考试 选择框
    captcha --> 验证码
'''
from django import forms
from captcha.fields import CaptchaField

class UserForm(forms.Form):
    username = forms.CharField(label="准考证号", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(label='验证码')

class MarkForm(forms.Form):
    def __init__(self, choices=(('a', 'a'), ('b', 'b')), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['choice'].choices = choices
    name = forms.CharField(label="姓名", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    choice = forms.ChoiceField(label="考试",choices=[])
    captcha = CaptchaField(label='验证码')
