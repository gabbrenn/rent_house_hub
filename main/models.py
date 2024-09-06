from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('AP', 'Apartment'),
        ('VI', 'Villa'),
        ('HO', 'House'),
        ('ST', 'Studio'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    amenities = models.TextField()
    property_type = models.CharField(max_length=2, choices=PROPERTY_TYPE_CHOICES, default='HO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    image_path = models.ImageField(upload_to='property_images/')

    def __str__(self):
        return f"Image for {self.property.title}"

class Review(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # e.g., 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('property', 'user')  # Prevent multiple reviews from the same user on the same property

class ReviewReply(models.Model):
    review = models.ForeignKey(Review, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)