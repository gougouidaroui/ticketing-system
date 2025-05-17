from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from .forms import SignUpForm, LoginForm, TicketForm, AssignTicketForm, TicketCommentForm, TicketFilterForm
from .models import Ticket
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import Group
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta, datetime
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
import os
from django.conf import settings
from django.core.mail import send_mail


def is_agent(user):
    return user.groups.filter(name__in=['Technical Agents', 'HR Agents', 'Consultants']).exists()

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:
        return redirect('admin_home')
    if is_agent(request.user):
        return redirect('agent_home')
    return redirect('my_tickets')
@login_required
def admin_home(request):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can access this page.")
        return redirect('my_tickets')
    return render(request, 'admin_home.html')

@login_required
def agent_home(request):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can access this page.")
        return redirect('my_tickets')
    return render(request, 'agent_home.html')

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return redirect('agent_dashboard')

@login_required
def create_ticket(request):
    if not request.user.groups.filter(name='Normal Users').exists() and not request.user.is_superuser:
        messages.error(request, "Only normal users or admins can create tickets.")
        return redirect('my_tickets')
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            return redirect('my_tickets')
    else:
        form = TicketForm()
    return render(request, 'create_ticket.html', {'form': form})

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user, assigned_agent__isnull=True)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ticket '{ticket.name}' updated successfully.")
            return redirect('my_tickets')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'edit_ticket.html', {'form': form, 'ticket': ticket})

@login_required
def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user, assigned_agent__isnull=True)
    if request.method == 'POST':
        ticket_name = ticket.name
        ticket.delete()
        messages.success(request, f"Ticket '{ticket_name}' deleted successfully.")
        return redirect('my_tickets')
    return render(request, 'delete_ticket.html', {'ticket': ticket})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'my_tickets.html', {'tickets': tickets})

@login_required
def assign_tickets(request):
    if not request.user.is_staff:
        messages.error(request, "Only agents can access this page.")
        return redirect('ticket_list')
    tickets = Ticket.objects.filter(assigned_agent__isnull=True)
    return render(request, 'assign_tickets.html', {'tickets': tickets})

@login_required
def assign_ticket(request, ticket_id):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can assign tickets.")
        return redirect('ticket_list')
    ticket = get_object_or_404(Ticket, id=ticket_id, assigned_agent__isnull=True)
    if request.method == 'POST':
        form = AssignTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.assigned_agent = request.user
            ticket.state = 'in_progress'
            ticket.save()
            messages.success(request, f"You have assigned ticket '{ticket.name}'.")
            messages.info(request, f"Your ticket '{ticket.name}' is now being handled by {request.user.username}.", extra_tags=f'for_user_{ticket.user.id}')
            return redirect('assign_tickets')
    else:
        form = AssignTicketForm(instance=ticket)
    return render(request, 'assign_ticket.html', {'form': form, 'ticket': ticket})

@login_required
def agent_tickets(request):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can view assigned tickets.")
        return redirect('ticket_list')

    form = TicketFilterForm(request.GET or None)
    tickets = Ticket.objects.filter(assigned_agent=request.user).select_related('category', 'user', 'assigned_agent')

    if form.is_valid():
        if form.cleaned_data['priority']:
            tickets = tickets.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data['state']:
            tickets = tickets.filter(state=form.cleaned_data['state'])

    sort_by = request.GET.get('sort_by', '-creation_date')
    allowed_sort_fields = ['state', '-state', 'priority', '-priority']
    if sort_by in allowed_sort_fields:
        tickets = tickets.order_by(sort_by)
    else:
        tickets = tickets.order_by('-creation_date')  # Default sort

    return render(request, 'agent_tickets.html', {'tickets': tickets, 'form': form})

@login_required
def resolve_ticket(request, ticket_id):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can resolve tickets.")
        return redirect('ticket_list')
    ticket = get_object_or_404(Ticket, id=ticket_id, state__in=['open', 'in_progress'])
    if request.method == 'POST':
        ticket.state = 'closed'
        ticket.resolution_date = timezone.now()
        ticket.save()
        try:
            send_mail(
                subject=f"Votre ticket '{ticket.subject}' a été résolu",
                message=f"Bonjour {ticket.user.username},\n\nVotre ticket '{ticket.subject}' a été résolu par l'agent {request.user.username}.\nDescription: {ticket.description}\n\nMerci,\nL'équipe de support",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[ticket.user.email],
                fail_silently=False,
            )
            messages.success(request, "Ticket résolu et notification envoyée.")
        except Exception as e:
            messages.error(request, f"Ticket résolu, mais échec de l'envoi de l'email: {str(e)}")

        messages.success(request, f"Ticket '{ticket.name}' has been resolved.")
        messages.info(request, f"Your ticket '{ticket.name}' has been resolved by {request.user.username}.", extra_tags=f'for_user_{ticket.user.id}')
        return redirect('agent_tickets')
    return render(request, 'resolve_ticket.html', {'ticket': ticket})

@login_required
def ticket_list(request):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can view all tickets.")
        return redirect('home')

    form = TicketFilterForm(request.GET or None)
    tickets = Ticket.objects.all().select_related('category', 'user', 'assigned_agent')

    if form.is_valid():
        if form.cleaned_data['priority']:
            tickets = tickets.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data['state']:
            tickets = tickets.filter(state=form.cleaned_data['state'])

    sort_by = request.GET.get('sort_by', '-creation_date')
    allowed_sort_fields = ['state', '-state', 'priority', '-priority']
    if sort_by in allowed_sort_fields:
        tickets = tickets.order_by(sort_by)
    else:
        tickets = tickets.order_by('-creation_date')  # Default sort

    return render(request, 'tickets.html', {'tickets': tickets, 'form': form})

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can access the dashboard.")
        return redirect('my_tickets')

    # Line Chart: Tickets created per day
    tickets_per_day = Ticket.objects.annotate(
        date=TruncDate('creation_date')
    ).values('date').annotate(count=Count('id')).order_by('date')
    dates = [entry['date'].strftime('%Y-%m-%d') for entry in tickets_per_day]
    counts = [entry['count'] for entry in tickets_per_day]
    plt.figure(figsize=(10, 5))
    plt.plot(dates, counts, marker='o')
    plt.title('Tickets Created Per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of Tickets')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    line_chart_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', 'tickets_per_day.png')
    os.makedirs(os.path.dirname(line_chart_path), exist_ok=True)
    plt.savefig(line_chart_path)
    plt.close()

    tickets_by_category = Ticket.objects.values('category__name').annotate(count=Count('id'))
    categories = [entry['category__name'] for entry in tickets_by_category]
    category_counts = [entry['count'] for entry in tickets_by_category]
    plt.figure(figsize=(8, 8))
    plt.pie(category_counts, labels=categories, autopct='%1.1f%%')
    plt.title('Tickets by Category')
    pie_chart_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', 'tickets_by_category.png')
    plt.savefig(pie_chart_path)
    plt.close()

    resolved_by_agent = Ticket.objects.filter(state='closed').values('assigned_agent__username').annotate(count=Count('id'))
    agents = [entry['assigned_agent__username'] for entry in resolved_by_agent]
    agent_counts = [entry['count'] for entry in resolved_by_agent]
    plt.figure(figsize=(10, 5))
    plt.bar(agents, agent_counts)
    plt.title('Tickets Resolved by Agent')
    plt.xlabel('Agent')
    plt.ylabel('Number of Tickets')
    plt.xticks(rotation=45)
    plt.tight_layout()
    bar_chart_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', 'tickets_by_agent.png')
    plt.savefig(bar_chart_path)
    plt.close()

    resolved_tickets = Ticket.objects.filter(state='closed', resolution_date__isnull=False)
    avg_hours = 0
    if resolved_tickets.exists():
        total_seconds = 0
        count = 0
        for ticket in resolved_tickets:
            delta = ticket.resolution_date - ticket.creation_date
            total_seconds += delta.total_seconds()
            count += 1
        avg_hours = round(total_seconds / 3600 / count, 2) if count > 0 else 0

    statuses = ['open', 'in_progress', 'closed']
    priorities = ['low', 'medium', 'high']
    data = {status: [] for status in statuses}
    for status in statuses:
        for priority in priorities:
            count = Ticket.objects.filter(state=status, priority=priority).count()
            data[status].append(count)
    x = np.arange(len(priorities))
    width = 0.25
    plt.figure(figsize=(10, 5))
    bottom = np.zeros(len(priorities))
    for status in statuses:
        plt.bar(x, data[status], width, label=status, bottom=bottom)
        bottom += np.array(data[status])
        x = x + width
    plt.title('Tickets by Status and Priority')
    plt.xlabel('Priority')
    plt.ylabel('Number of Tickets')
    plt.xticks(x - width, priorities)
    plt.legend()
    plt.tight_layout()
    stacked_bar_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', 'tickets_by_status_priority.png')
    plt.savefig(stacked_bar_path)
    plt.close()

    context = {
        'line_chart': 'charts/tickets_per_day.png',
        'pie_chart': 'charts/tickets_by_category.png',
        'bar_chart': 'charts/tickets_by_agent.png',
        'avg_resolution_time': avg_hours,
        'stacked_bar_chart': 'charts/tickets_by_status_priority.png',
    }
    return render(request, 'admin_dashboard.html', context)

def generate_chart_if_needed(path, generate_func, max_age_hours=1):
    if os.path.exists(path):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(path))
        if (datetime.now() - file_mtime).total_seconds() < max_age_hours * 3600:
            return
    generate_func()

@login_required
def agent_dashboard(request):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can access the agent dashboard.")
        return redirect('my_tickets')

    tickets_by_category = Ticket.objects.filter(assigned_agent=request.user).values('category__name').annotate(count=Count('id'))
    categories = [entry['category__name'] for entry in tickets_by_category]
    category_counts = [entry['count'] for entry in tickets_by_category]
    pie_chart_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', f'agent_{request.user.username}_categories.png')
    def generate_pie_chart():
        if not categories or sum(category_counts) == 0:
            plt.figure(figsize=(8, 8))
            plt.text(0.5, 0.5, 'No Tickets Assigned', horizontalalignment='center', verticalalignment='center')
            plt.title('My Assigned Tickets by Category')
            os.makedirs(os.path.dirname(pie_chart_path), exist_ok=True)
            plt.savefig(pie_chart_path)
            plt.close()
        else:
            plt.figure(figsize=(8, 8))
            plt.pie(category_counts, labels=categories, autopct='%1.1f%%')
            plt.title('My Assigned Tickets by Category')
            plt.savefig(pie_chart_path)
            plt.close()
    generate_chart_if_needed(pie_chart_path, generate_pie_chart)

    statuses = ['open', 'in_progress', 'closed']
    status_counts = [Ticket.objects.filter(assigned_agent=request.user, state=status).count() for status in statuses]
    bar_chart_path = os.path.join(settings.STATICFILES_DIRS[0], 'charts', f'agent_{request.user.username}_status.png')
    def generate_bar_chart():
        plt.figure(figsize=(10, 5))
        plt.bar(statuses, status_counts)
        plt.title('My Assigned Tickets by Status')
        plt.xlabel('Status')
        plt.ylabel('Number of Tickets')
        plt.tight_layout()
        os.makedirs(os.path.dirname(bar_chart_path), exist_ok=True)
        plt.savefig(bar_chart_path)
        plt.close()
    generate_chart_if_needed(bar_chart_path, generate_bar_chart)

    resolved_tickets = Ticket.objects.filter(assigned_agent=request.user, state='closed', resolution_date__isnull=False)
    avg_hours = 0
    if resolved_tickets.exists():
        total_seconds = 0
        count = 0
        for ticket in resolved_tickets:
            delta = ticket.resolution_date - ticket.creation_date
            total_seconds += delta.total_seconds()
            count += 1
        avg_hours = round(total_seconds / 3600 / count, 2) if count > 0 else 0

    context = {
        'pie_chart': f'charts/agent_{request.user.username}_categories.png',
        'bar_chart': f'charts/agent_{request.user.username}_status.png',
        'avg_resolution_time': avg_hours,
    }
    return render(request, 'agent_dashboard.html', context)

@login_required
def add_comment(request, ticket_id):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can add comments.")
        return redirect('ticket_list')
    if request.user.is_superuser:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    else:
        ticket = get_object_or_404(Ticket, id=ticket_id, assigned_agent=request.user)
    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.agent = request.user
            comment.save()
            messages.success(request, "Comment added successfully.")
            return redirect('tickets_list' if request.user.is_superuser else 'agent_tickets')
    else:
        form = TicketCommentForm()
    return render(request, 'add_comment.html', {'form': form, 'ticket': ticket})

@login_required
def unassign_ticket(request, ticket_id):
    if not is_agent(request.user) and not request.user.is_superuser:
        messages.error(request, "Only agents or admins can unassign tickets.")
        return redirect('ticket_list')
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        ticket.assigned_agent = None
        ticket.state = 'open'
        ticket.save()
        messages.success(request, f"You have unassigned ticket '{ticket.name}'.")
        return redirect('agent_tickets')
    return render(request, 'unassign_ticket.html', {'ticket': ticket})
