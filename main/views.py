import logging
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Property, PropertyImage, Review, ReviewReply
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import check_password

# Create your views here.

def index(request):
    context = {
        'property_type_choices': Property.PROPERTY_TYPE_CHOICES,
        # Add other context variables if needed
    }
    return render(request, 'index.html', context)

def signup(request):
    if request.method == 'POST':
        fname = request.POST['first_name']
        lname = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['confirm_password']
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        try:
            User.objects.create(first_name=fname, username=username, last_name=lname, email=email, password=make_password(password))
            return redirect('signin')
        except Exception as e:
            print(e)

    return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = User.objects.get(username=username)
            user = authenticate(request, username=username, password=password)
        except:
            messages.error(request, 'User Does Not Exist!')
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username Or Password Does Not Exist!')

    return render(request, 'signin.html')

def signout(request):
    logout(request)  # This will log out the user and clear the session
    return redirect('signin')  # Redirect to the sign-in page or another page after logging out

def home(request):
    return render(request, 'index.html')

def house_list(request):
    houses = Property.objects.all()

    # Filter by location with partial matching
    location = request.GET.get('location')
    if location:
        houses = houses.filter(location__icontains=location)

    # Filter by min price
    min_price = request.GET.get('min_price')
    if min_price:
        houses = houses.filter(price__gte=min_price)

    # Filter by max price
    max_price = request.GET.get('max_price')
    if max_price:
        houses = houses.filter(price__lte=max_price)

    # Filter by property type
    property_type = request.GET.get('property_type')
    if property_type:
        houses = houses.filter(property_type=property_type)

    context = {
        'houses': houses,
        'property_type_choices': Property.PROPERTY_TYPE_CHOICES,
    }
    return render(request, 'houselist.html', context)

@login_required
def add_new_listing(request):
    if request.method == 'POST':
        title = request.POST['title']
        price = request.POST['price']
        description = request.POST['description']
        location = request.POST['location']
        amenities = request.POST['amenities']
        property_type = request.POST['property_type']
        images = request.FILES.getlist('images')

        # Create the Property object
        property_obj = Property.objects.create(
            user=request.user,
            title=title,
            description=description,
            price=price,
            location=location,
            amenities=amenities,
            property_type=property_type
        )

        # Save the uploaded images
        for image in images:
            PropertyImage.objects.create(
                property=property_obj,
                image_path=image
            )

        return redirect('house_list')

    context = {
        'property_type_choices': Property.PROPERTY_TYPE_CHOICES
    }
    return render(request, 'add-new-listing.html', context)

logger = logging.getLogger(__name__)


def house_detail(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    amenities_list = property.amenities.split(',')  # Splitting the string into a list

    reviews = Review.objects.filter(property=property)
    email_sent = False
    email_failed = False
    error_message = ""

    if request.method == 'POST':
        # Handling contact form submission
        if 'contact_form' in request.POST:
            name = request.POST.get('name')
            sender_email = request.POST.get('email')
            message = request.POST.get('message')
            owner_email = property.user.email

            # Basic validation
            if not name or not sender_email or not message:
                error_message = "All fields are required."
            elif not validate_email(sender_email):
                error_message = "Invalid email address."
            else:
                try:
                    email_message = f"""
                    Dear {property.user.first_name},

                    You have received a new inquiry regarding your property listing: {property.title}.

                    Sender: {name}
                    Email: {sender_email}

                    Message:
                    {message}

                    Best regards,
                    Rent House Hub
                    """

                    email = EmailMessage(
                        subject=f"Property Inquiry: {property.title}",
                        body=email_message,
                        from_email=sender_email,
                        to=[owner_email],
                    )
                    email.send()
                    email_sent = True
                except Exception as e:
                    email_failed = True
                    logger.error(f"Failed to send email: {e}")

        # Handling review reply submission
        elif 'reply_content' in request.POST and 'review_id' in request.POST:
            review_id = request.POST.get('review_id')
            reply_content = request.POST.get('reply_content')
            review = get_object_or_404(Review, id=review_id)

            if request.user == property.user:
                if reply_content:
                    ReviewReply.objects.create(
                        review=review,
                        user=request.user,
                        reply_content=reply_content
                    )
                    return redirect('house_detail', property_id=property.id)
                else:
                    error_message = "Reply content cannot be empty."

    context = {
        'property': property,
        'amenities_list': amenities_list,
        'reviews': reviews,
        'error_message': error_message,
        'email_sent': email_sent,
        'email_failed': email_failed,
    }

    return render(request, 'house-detail.html', context)


def validate_email(email):
    from django.core.validators import validate_email as django_validate_email
    from django.core.exceptions import ValidationError
    
    try:
        django_validate_email(email)
        return True
    except ValidationError:
        return False
    
def submit_review(request, property_id):
    # Retrieve the property object or return 404 if not found
    property = get_object_or_404(Property, id=property_id)
    
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return redirect('signin')  # Redirect to sign-in page if the user is not authenticated
    
    # Check if the request method is POST
    if request.method == 'POST':
        # Retrieve the form data
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Validate form data
        if rating and comment:
            # Check if a review already exists for this user and property
            existing_review = Review.objects.filter(property=property, user=request.user).exists()
            if existing_review:
                # Display an error message if the user has already reviewed this property
                messages.error(request, 'You have already submitted a review for this property.')
            else:
                # Create and save the new review
                review = Review(property=property, user=request.user, rating=rating, comment=comment)
                review.save()
                
                # Display a success message
                messages.success(request, 'Your review has been submitted successfully!')
            
            # Redirect to the property detail page
            return redirect('house_detail', property_id=property_id)
        else:
            # Display an error message if the form data is invalid
            messages.error(request, 'Please provide both rating and comment.')
    
    # Redirect to the property detail page if not a POST request
    return redirect('house_detail', property_id=property_id)


@login_required
def my_listings(request):
    properties = Property.objects.filter(user=request.user)
    return render(request, 'my-listings.html', {'properties': properties})

@login_required
def edit_listing(request, property_id):
    property = get_object_or_404(Property, id=property_id, user=request.user)

    if request.method == 'POST':
        title = request.POST['title']
        price = request.POST['price']
        description = request.POST['description']
        location = request.POST['location']
        amenities = request.POST['amenities']
        property_type = request.POST['property_type']
        images = request.FILES.getlist('images')

        # Update the Property object
        property.title = title
        property.price = price
        property.description = description
        property.location = location
        property.amenities = amenities
        property.property_type = property_type
        property.save()

        # Update the PropertyImage objects
        if images:
            PropertyImage.objects.filter(property=property).delete()  # Remove old images
            for image in images:
                PropertyImage.objects.create(
                    property=property,
                    image_path=image
                )

        messages.success(request, 'Property updated successfully!')
        return redirect('house_detail', property_id=property.id)

    else:
        images = PropertyImage.objects.filter(property=property)
        context = {
            'property': property,
            'images': images,
            'property_type_choices': Property.PROPERTY_TYPE_CHOICES
        }
        return render(request, 'edit-listing.html', context)

@login_required
def delete_listing(request, property_id):
    property = get_object_or_404(Property, id=property_id, user=request.user)
    if request.method == 'POST':
        property.delete()
        return redirect('my_listings')
    return render(request, 'confirm-delete.html', {'property': property})

@login_required
def profile_settings(request):
    user = request.user

    if request.method == 'POST':
        # Handle profile updates
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if not first_name or not last_name or not email:
            messages.error(request, 'All fields are required.')
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            messages.success(request, 'Your profile was successfully updated!')

        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_new_password = request.POST.get('confirm_new_password')

        if current_password and new_password and confirm_new_password:
            if not check_password(current_password, user.password):
                messages.error(request, 'Your current password is incorrect.')
            elif new_password != confirm_new_password:
                messages.error(request, 'The new passwords do not match.')
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
        
        return redirect('profile_settings')

    return render(request, 'profile-settings.html', {'user': user})

def about_us(request):
    return render(request, 'about_us.html')
def terms_conditions(request):
    return render(request, 'terms_conditions.html')
def privacy_policy(request):
    return render(request, 'privacy_policy.html')