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

class DevForm(forms.Form):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    username = forms.CharField(label="准考证号",max_length=128,widget=forms.TextInput(attrs={'class':'form-control'}))
    name = forms.CharField(label='姓名',max_length=128,widget=forms.TextInput(attrs={'class':'form-control'}))
    contact = forms.CharField(label='联系方式',max_length=128,widget=forms.TextInput(attrs={'class':'form-control'}))
    usefor = forms.CharField(label="使用场景",max_length=128,widget=forms.Textarea)
    captcha = CaptchaField(label='验证码')