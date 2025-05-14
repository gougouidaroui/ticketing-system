from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CustomUser, Ticket, Category, TicketComment
from django.conf import settings

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=17,
        required=True,
        help_text="Enter phone number in the format: '+999999999'.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = ''
        self.fields['email'].label = ''
        self.fields['phone_number'].label = ''
        self.fields['password1'].label = ''
        self.fields['password2'].label = ''
        self.fields['username'].widget.attrs.update({'placeholder': 'Username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email'})
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'Phone Number'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})

        self.fields['password2'].help_text = None

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("This phone number is already in use.")
        return phone_number

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='',
                               widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(label='',
                               widget=forms.TextInput(attrs={'placeholder': 'Password'}))

    class Meta:
        model = User
        fields = ('username', 'password')


class TicketForm(forms.ModelForm):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    STATE_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    )

    category = forms.ChoiceField(choices=(), required=True)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, initial='low')
    state = forms.ChoiceField(choices=STATE_CHOICES, initial="open", widget=forms.HiddenInput())

    class Meta:
        model = Ticket
        fields = ('name', 'description', 'category', 'priority', 'state')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ticket Name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Describe the issue', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [(category.id, category.name) for category in Category.objects.all()]
        self.fields['name'].label = 'Ticket title'
        self.fields['description'].label = 'description'
        self.fields['category'].label = 'category'
        self.fields['priority'].label = 'priority'

    def clean_category(self):
        category_id = self.cleaned_data['category']
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise forms.ValidationError("Invalid category selected.")
        return category

class AssignTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('assigned_agent',)
        widgets = {
            'assigned_agent': forms.HiddenInput(),
        }

class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
        }

class TicketFilterForm(forms.Form):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('','All Priorities')
    )
    STATE_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('','All Statuses'),
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False
    )
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=False
    )
