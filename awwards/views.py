from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from .forms import ProjectForm,ProfileForm,VoteForm
from .models import Project,Profile
from django.core.exceptions import ObjectDoesNotExist
from django.http  import HttpResponse
from django.contrib.auth.decorators import login_required
from .email import send_welcome_email
from datetime import date
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import ProfileSerializer,ProjectSerializer

# Create your views here.

def home(request):
    all_projects = Project.fetch_all_images()
    projects = Project.objects.all()
    dayProj = 0
    today = date.today()
    maxVote = 0
    for project in projects:
        design = int(project.design)
        usability = int(project.usability)
        content = int(project.usability)
        avrg = (design + usability + content)/3
        if avrg > maxVote:
            maxVote= avrg
            dayProj = project    
    design = int(dayProj.design)*10
    usability = int(dayProj.usability)*10
    content = int(dayProj.content)*10
    return render(request,"index.html",{"all_images":all_projects, "mainproj":dayProj, "day":today, "design":design,"usability":usability, "content":content })

@login_required(login_url='/accounts/login/')
def new_project(request):
    current_user = request.user
    if request.method == 'POST':
        form = ProjectForm(request.POST,request.FILES)
        if form.is_valid():
            user_image = form.save(commit=False)
            user_image.user = current_user
            user_image.save()
        return redirect('home')
    else:
        form = ProjectForm()
    return render(request,"project.html",{"form":form})

@login_required(login_url='/accounts/login/')
def new_profile(request):
    current_user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.prof_user = current_user
            profile.profile_Id = request.user.id
            profile.save()
        return redirect('profile')
    else:
        form = ProfileForm()
    return render(request, 'profile/new_profile.html', {"form": form})

@login_required(login_url='/accounts/login/')
def profile_edit(request):
    current_user = request.user
    if request.method == 'POST':
        logged_user = Profile.objects.get(prof_user=request.user)
        form = ProfileForm(request.POST, request.FILES, instance=logged_user)
        if form.is_valid():
            form.save()
        return redirect('profile')
    else:
        form = ProfileForm()
    return render(request,'profile/edit_profile.html',{'form':form})



@login_required(login_url='/accounts/login/')
def profile(request):
    current_user = request.user
    projects = Project.objects.filter(user = current_user)

    try:   
        prof = Profile.objects.get(prof_user=current_user)
    except ObjectDoesNotExist:
        return redirect('new_profile')

    return render(request,'profile/profile.html',{'profile':prof,'projects':projects})



def search_project(request):
    if 'project' in request.GET and request.GET ["project"]:
        search_term = request.GET.get("project")
        searched_projects = Project.search_project_by_title(search_term)
        message = f'{search_term}'

        return render(request, 'search.html', {"message":message, "projects":searched_projects})

    else:
        message = "No search results yet!"
        return render (request, 'search.html', {"message": message})

        
@login_required(login_url='/accounts/login/')
def project_review(request,project_id):
    try:
        single_project = Project.get_single_project(project_id)
        average_score = round(((single_project.design + single_project.usability + single_project.content)/3),2)
        if request.method == 'POST':
            vote_form = VoteForm(request.POST)
            if vote_form.is_valid():
                single_project.vote_submissions+=1
                if single_project.design == 0:
                    single_project.design = int(request.POST['design'])
                else:
                    single_project.design = (single_project.design + int(request.POST['design']))/2
                if single_project.usability == 0:
                    single_project.usability = int(request.POST['usability'])
                else:
                    single_project.usability = (single_project.usability + int(request.POST['usability']))/2
                if single_project.content == 0:
                    single_project.content = int(request.POST['content'])
                else:
                    single_project.content = (single_project.content + int(request.POST['usability']))/2

                single_project.save()
                return redirect('project_review',project_id)
        else:
            vote_form = VoteForm()

    except Exception as  e:
        raise Http404()
    return render(request,'review.html',{"vote_form":vote_form,"single_project":single_project,"average_score":average_score})

class ProfileList(APIView):
    def get(self,request,format=None):
        complete_profile = Profile.objects.all()
        serializers = ProfileSerializer(complete_profile, many=True)
        return Response(serializers.data)

class ProjectList(APIView):
    def get(self,request,format=None):
        projects = Project.objects.all()
        serializers = ProjectSerializer(projects, many=True)
        return Response(serializers.data)