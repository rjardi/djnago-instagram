from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render

from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout

from instagram.forms import LoginForm, RegistrationForm
from django.contrib import messages

from django.views.generic import FormView, DetailView, UpdateView, ListView

from posts.models import Post
from profiles.forms import FollowForm
from profiles.models import Follow, UserProfile

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class HomeView(TemplateView) :
    template_name = "general/home.html"

    def get_context_data(self, **kwargs):

        context=super().get_context_data(**kwargs)

        # Si el usuario esta logueado
        if self.request.user.is_authenticated:
            # Obtenemos los posts de los usuarios que seguimos
            seguidos=Follow.objects.filter(follower=self.request.user.profile).values_list('following__user', flat=True)
            # Traemos los posts de los users que seugimos
            last_posts=Post.objects.filter(user__profile__user__in=seguidos)
        else:
            last_posts=Post.objects.all().order_by("-created_at")[:5]
        context["last_posts"]=last_posts

        return context

class LoginView(FormView):
    template_name = "general/login.html"
    form_class= LoginForm

    def form_valid(self, form):
        usuario = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=usuario, password=password)

        if user is not None:
            login(self.request, user)
            messages.add_message(self.request, messages.SUCCESS, f'Bienvenido de nuevo {user.username}')
            return HttpResponseRedirect(reverse('home'))

        else:
            messages.add_message(
                self.request, messages.ERROR, 'Usuario no válido o contraseña no válida')
            return super(LoginView, self).form_invalid(form)

class RegisterView(CreateView) :
    template_name = "general/register.html"
    model=User
    success_url=reverse_lazy("login")
    form_class=RegistrationForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Usuario creado correctamente.")
        return super(RegisterView, self).form_valid(form)
    
@method_decorator(login_required, name="dispatch")    
class ProfileDetailView(DetailView, FormView) :
    model = UserProfile
    template_name = "general/profile_detail.html"
    context_object_name="profile"
    form_class=FollowForm

    def get_initial(self):
        self.initial["profile_pk"]=self.get_object().pk
        return super().get_initial()
    
    def form_valid(self, form):
        profile_pk=form.cleaned_data.get("profile_pk")
        following=UserProfile.objects.get(pk=profile_pk)
            
        if Follow.objects.filter(
            follower=self.request.user.profile,
            following=following
        ).count():
            Follow.objects.filter(
                follower=self.request.user.profile,
                following=following
            ).delete()
            messages.add_message(self.request, messages.SUCCESS, f"Se ha dejado de seguir a {following.user.username}")
            
        else:
            Follow.objects.get_or_create(
                follower=self.request.user.profile,
                following=following
            )
            messages.add_message(self.request, messages.SUCCESS, f"Siguiendo a {following.user.username}")
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("profile_detail", args=[self.get_object().pk])
    
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        following=Follow.objects.filter(follower=self.request.user.profile, following=self.get_object()).exists()
        context["following"]=following
        return context
    

@method_decorator(login_required, name="dispatch")    
class ProfileListView(ListView) :
    model = UserProfile
    template_name = "general/profile_list.html"
    context_object_name="profiles"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserProfile.objects.all().order_by('user__username').exclude(user=self.request.user)
        return UserProfile.objects.all().order_by('user__username')


@method_decorator(login_required, name="dispatch")
class ProfileUpdateView(UpdateView) :
    model = UserProfile
    template_name = "general/profile_update.html"
    context_object_name="profile"
    fields =["profile_picture","bio","birth_date"]
    # Metodo que se ejecuta antes de realizar el despacho de la url asociada a la vista, es decir se ejecuta antes de renderizar la vista
    # Útil para hacer comprobaciones como en el caso siguiente que queremos evitar que un usuario logeado pueda acceder a la url de edición de un perfil que no sea el suyo
    def dispatch(self, request, *args, **kwargs):
        user_profile=self.get_object()
        if user_profile.user != self.request.user:
            return HttpResponseRedirect(reverse("home"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Perfil actualizado correctamente.")
        return super(ProfileUpdateView, self).form_valid(form)
    
    def get_success_url(self):
        return reverse("profile_detail", args=[self.get_object().pk])

class LegalView(TemplateView) :
    template_name = "general/legal.html"

class ContactView(TemplateView) :
    template_name = "general/contact.html"

# @method_decorator(login_required, name="dispatch")
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Se ha cerrado sesión correctamente.")
    return HttpResponseRedirect(reverse('home'))