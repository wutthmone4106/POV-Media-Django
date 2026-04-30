from django.shortcuts import get_object_or_404, redirect, render
from blog import settings # For Email
from pov.models import About, Blog, Category, Comment, Notification, Profile, Reaction, Subscriber #Model
from django.db.models import Q #Search
from django.contrib import messages #Messages
from django.contrib.auth.models import User, User #User Authentication
from django.contrib.auth import authenticate,login as auth_login, logout as auth_logout #Login and Logout
from django.core.paginator import Paginator #Pagination
from django.contrib.auth.decorators import login_required #Login Required
from django.db.models import Count #Dashboard Category Count
from django.utils.text import slugify #Slugify for Slug Field
from django.contrib.auth import update_session_auth_hash #To keep user logged in after password change
from django.http import HttpResponseRedirect #Redirect back to the page before
from .forms import AddUserForm, EditUserForm #Forms for Admin to manage staff (From DJANGO Forms)
from itertools import chain #Recent Activity
from django.core.mail import send_mail # For Email

# === Home ===
def index(request):
    posts = Blog.objects.filter(is_featured = True, status = "Published").order_by('updated_at')
    blogs = Blog.objects.filter(is_featured = False, status = "Published")
    paginator = Paginator(posts, 4) 
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number)

    # Fetch About Us into Index page
    try:
        about = About.objects.get()
    except:
        about = None

    context = {
        'posts' : page_obj,
        'blogs' : blogs,
        'about' : about,
    }
    return render(request, "index.html", context) 

# === Category ===
def posts_by_category(request, category_id):
    # category = get_object_or_404(Category, pk=category_id) [Use this to show 404 error page if the category doesn't exist]
    posts = Blog.objects.filter(status="Published", category= category_id)
    try:
        # Call category by id
        category = Category.objects.get( pk=category_id)
    except:
        # If the category doesn't exist, redirect user to the homepage
        return redirect('index')

    context = {
        'posts' : posts,
        'category' : category,
    }
    return render(request, 'posts_by_category.html', context)
# Use try/expect to do some custom action

# === Single blog page ===
def blogs(request, slug):
    single_blog = get_object_or_404(Blog, slug=slug, status='Published')
    related_posts = Blog.objects.filter(category=single_blog.category, status="Published").exclude(id=single_blog.id)[:3]
    recent_blogs = Blog.objects.filter(status="Published").order_by('-created_at')[:4]

    # Reaction
    reactions_data = [
        ('like', 'Like', '👍', 'primary'),
        ('love', 'Love', '❤️', 'danger'),
        ('haha', 'Haha', '😂', 'warning'),
        ('wow', 'Wow', '😮', 'info'),
        ('sad', 'Sad', '😢', 'secondary'),
        ('angry', 'Angry', '😡', 'dark'),
    ]

    reaction_counts = {}
    for r_type, label, emoji, color in reactions_data:
        reaction_counts[r_type] = single_blog.reactions.filter(type=r_type).count()

    # Comment & Reply Create
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to comment.")
            return redirect('login')

        comment_text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')  # This identifies if it's a reply

        if comment_text:
            new_comment = Comment(
                user=request.user,
                blog=single_blog,
                comment=comment_text
            )
            
            # If parent_id exists, link this comment as a reply
            if parent_id:
                parent_obj = get_object_or_404(Comment, id=parent_id)
                new_comment.parent = parent_obj
                
            Notification.objects.create(
            user=single_blog.author, # The person who owns the blog gets the alert
            message=f"{request.user.username} commented on your post!"
        )
            new_comment.save()
            messages.success(request, "Your message has been posted!")
        
        return HttpResponseRedirect(request.path_info)
    
    comments = Comment.objects.filter(blog=single_blog, parent=None).order_by('-created_at')
    comment_count = Comment.objects.filter(blog=single_blog).count()

    context = {
        'single_blog': single_blog,
        'related_posts': related_posts,
        'recent_blogs': recent_blogs,
        'comments': comments,
        'comment_count': comment_count,
        'reactions_data': reactions_data,
        'reaction_counts': reaction_counts,
    }
    return render(request, 'blogs.html', context)

# === Search ===
def search(request):
    keyword = request.GET.get('search') 
    
    if keyword:
       blogs = Blog.objects.filter(
            Q(title__icontains=keyword) | 
            Q(category__category_name__icontains=keyword) | 
            Q(description__icontains=keyword) | 
            Q(blog_body__icontains=keyword), 
            status="Published"
        )
    else:
        blogs = Blog.objects.none() 
        
    context = {
        'blogs': blogs,
        'keyword': keyword, 
    }
    return render(request, 'search.html', context)

# === Register ===
def register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.warning(request, "User already exists")
            return redirect('register')
        
        # 1. Create the User
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name, 
            last_name=last_name
            )
        
        # 2. Create the associated Profile
        Profile.objects.get_or_create(user=user)
        
        # Email Integration
        subject = "New user register"
        message = f"Username is {user.username}. Email is {user.email}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        send_mail(subject, message, email_from, recipient_list)
        
        messages.success(request, "Registration Successful")
        return redirect('login')
    
    return render(request, 'register.html')

# === Login ===
def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            messages.warning(request, "You are currently login")
            return redirect(index)
        return render(request, 'login.html')
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username = username, password=password)

        # Check Existing User
        if user :
            auth_login(request, user)
            messages.success(request, "Welcome to Point of View Media!")
            return redirect(index)
        else:
            messages.error(request, "Invalid Login")
            return redirect(login)
        
# === Logout ===
def logout(request):
    auth_logout(request)
    return redirect(index)

@login_required
# === Dashboard ===
def dashboard(request):
    # Dashboard count
    blog_count = Blog.objects.all().count()
    category_count = Category.objects.all().count()
    user_count = User.objects.all().count()
    reaction_count = Reaction.objects.all().count()
    blog_category = Category.objects.annotate(blogs_count=Count('blog'))

    # Recent Activity
    recent_blogs = Blog.objects.all().order_by('-created_at')[:5]
    recent_comments = Comment.objects.all().order_by('-created_at')[:5]
    recent_members = User.objects.all().order_by('-date_joined')[:5]
    recent_reactions = Reaction.objects.all().order_by('-created_at')[:5]
    
    all_activity = sorted(
        chain(recent_blogs, recent_comments, recent_members, recent_reactions),
        key=lambda obj: obj.created_at if hasattr(obj, 'created_at') else obj.date_joined,
        reverse=True
    )[:10]

    # Notification
    notifications = Notification.objects.filter(user=request.user)[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    # Data from Model
    categories = Category.objects.all()
    blogs = Blog.objects.all()
    users = User.objects.filter(is_staff=True)

    # Crispy form
    users_with_forms = []
    for u in users:
        users_with_forms.append({
            'user': u,
            'form': EditUserForm(instance=u)
        })

    # login user
    if not request.user.is_staff:
        return redirect('user_profile')
    
    form = AddUserForm()

    # Subscriber (Registered User)
    subscribers = User.objects.filter(is_staff=False, is_superuser=False).order_by('-date_joined')
    # Filter Staff
    staff_members = User.objects.filter(is_staff=True).order_by('-date_joined')

    context = {
        'blog_count' : blog_count,
        'category_count' : category_count,
        'blog_category' : blog_category,
        'user_count' : user_count,
        'reaction_count' : reaction_count,
        'categories': categories,
        'blogs': blogs,
        'users': users,
        'form' : form,
        'users_with_forms': users_with_forms,
        'recent_activities': all_activity,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
        'subscribers': subscribers,
        'staff_members': staff_members,
    }
    return render(request, "dashboard/dashboard.html", context)

# === Blog Create ===
def create_blog(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        blog_body = request.POST.get("blog_body")
        category_id = request.POST.get("category")
        status = request.POST.get("status")
        is_featured = 'is_featured' in request.POST
        image = request.FILES.get("image")

        # Slugify the title to create a slug for the blog post
        slug = slugify(title)
        if Blog.objects.filter(slug=slug).exists():
            slug = slug + "-1"

        # Fetch the category 
        category = get_object_or_404(Category, id=category_id)
        Blog.objects.create(
            title=title,
            slug=slug, 
            description=description,
            blog_body=blog_body,
            category=category,
            status=status,
            is_featured=is_featured,
            image=image,
            author=request.user # Sets current logged-in user as author
        )

        #  Send email to subscribers
        subscribers = Subscriber.objects.values_list('email', flat=True)

        if subscribers:
            send_mail(
                subject=f"New Blog: {title}",
                message=f"A new blog has been posted!\n\n{title}\n\n{description}\n\nCheck it out!",
                from_email='wutthmone@gmail.com',
                recipient_list=list(subscribers),
                fail_silently=True,
            )

        # A notification for admin when new blog is created
        admin = User.objects.filter(is_superuser=True).first()
        Notification.objects.create(
            user=admin,
            message=f"New Blog Created: {title}"
        )
        
        return redirect('dashboard')

# === Blog Update ===
def edit_blog(request, id):
    blog = Blog.objects.get(id=id)
    context = {
        'blog' : blog
    }

    if request.method == "GET":
        return render(request, 'dashboard/dashboard.html', context)
    
    if request.method == "POST":
        blog.title = request.POST.get("title")
        blog.description = request.POST.get("description")
        blog.blog_body = request.POST.get("blog_body")
        blog.status = request.POST.get("status")
        blog.is_featured = 'is_featured' in request.POST
         # Image
        if request.FILES.get("image"):
            if blog.image:
                blog.image.delete(save=False)
            blog.image = request.FILES.get("image")
        # link category
        category_id = request.POST.get("category")
        if category_id:
            blog.category = get_object_or_404(Category, id=category_id)
       
        blog.save()
        return redirect('dashboard')

# === Blog Delete ===
def delete_blog(request,id):
    blog = Blog.objects.get(id=id)
    if request.method == "POST":
        if blog.image:
            blog.image.delete(save=False)
        blog.delete()
        return redirect('dashboard')

# === Category Create ===
def create_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = Category.objects.create(
            category_name = name
            )
        category.save()
        return redirect('dashboard')

# === Category Edit ===
def edit_category(request, id):
    category = Category.objects.get(id=id)
    context = {
        'category' : category
    }

    if request.method == "GET":
        return render(request, 'dashboard/dashboard.html', context)
    
    if request.method == "POST":
        name = request.POST.get("name")
        category.category_name = name
        category.save()
        return redirect('dashboard')

# === Category Delete ===
def delete_category(request, id):
    category = Category.objects.get(id=id)
    context = {
        "category": category
        }
    
    if request.method == "GET":
        return render(request, "dashboard/dashboard.html", context)

    if request.method == "POST":
        category.delete()
        return redirect('dashboard')

# === Member Create ===
@login_required
def create_staff(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
        else:
            print(form.errors)

# === Member Update ===
@login_required
def edit_staff(request, id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=id)
    
    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff member updated successfully.")
            return redirect('dashboard')
    else:
        form = EditUserForm(instance=user)
    
    context = {
        'form': form,
    }
    return render(request, 'dashboard/dashboard.html', context)

# === Member Delete ===
@login_required
def delete_staff(request, id):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    staff = get_object_or_404(User, id=id)
    if request.method == "POST":
        staff.delete()
        messages.success(request, "Staff member removed from directory.")
        return redirect('dashboard')
    return redirect('dashboard')

# === Login Logic ===
@login_required
def account_redirect(request):
    if request.user.is_staff:
        # If they are staff or admin, send to the dashboard
        return redirect('dashboard')
    else:
        # If they are just a reader, send to their profile page
        return redirect('user_profile')

# === User Profile ===
@login_required
def user_profile(request):
    # Get or create profile for the current user
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user = request.user
        
        # Update User Info
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        
        # Update Profile Specific Info
        profile.bio = request.POST.get('bio')
        profile.location = request.POST.get('location')
        
        # Image
        if request.FILES.get('image'):
            profile.image = request.FILES.get('image')

        user.save()
        profile.save()
        
        messages.success(request, "Your profile has been updated!")
        return redirect('user_profile')

    return render(request, 'user_profile.html')

# === User Profile Password Update ===
@login_required
def update_profile_password(request):
    if request.method == "POST":
        user = User.objects.get(id=request.user.id)
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Check current password
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect")
            return redirect('user_profile') 

        # Check new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match")
            return redirect('user_profile') 

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        
        messages.success(request, "Password changed successfully!")
        return redirect('user_profile')
    
    return redirect('user_profile')

# === Comment Update ===
@login_required
def edit_comment(request, id):
    comment = get_object_or_404(Comment, id=id, user=request.user)
    if request.method == "POST":
        comment.comment = request.POST.get('comment')
        comment.save()
        messages.success(request, "Comment updated!")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) # Redirect back to the page before

# === Comment Delete ===
@login_required
def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id, user=request.user)
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) # Redirect back to the page before

# === Like Comment ===
@login_required
def like_comment(request, id):
    comment = get_object_or_404(Comment, id=id)
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # Redirect back to the page before

# === Reaction ===
@login_required
def react_to_blog(request, blog_id, reaction_type):
    blog = get_object_or_404(Blog, id=blog_id)
    reaction, created = Reaction.objects.get_or_create(
        user=request.user, 
        blog=blog,
        defaults={'type': reaction_type}
    )
    
    if not created:
        if reaction.type == reaction_type:
            reaction.delete() # Toggle off
        else:
            reaction.type = reaction_type # Change reaction
            reaction.save()
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) # Redirect back to the page before

# === Mark as Read ===
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# === Notification Redirect ===
def notification_redirect(request, pk):
    notification = get_object_or_404(Notification, id=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Assuming a notification has a link/url field to the blog
    return redirect(notification.link)

# === Subscribe (Newsletter) ===
def subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if Subscriber.objects.filter(email=email).exists():
            messages.warning(request, "You're already subscribed!")
        else:
            Subscriber.objects.create(email=email)
            messages.success(request, "Subscribed successfully!")

        return redirect(request.META.get('HTTP_REFERER', '/')) 
    
# === Subscriber Delete (Admin Only) ===
@login_required
def delete_subscriber(request, id):
    # Ensure only admins can delete
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
        
    subscriber = get_object_or_404(User, id=id)
    subscriber.delete()
    messages.success(request, "Subscriber deleted successfully.")
    return redirect('dashboard')