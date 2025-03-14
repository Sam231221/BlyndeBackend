from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import Genre, User, Product, ImageAlbum, DiscountOffers


class UserAdminForm(UserChangeForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class GenreAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = Genre
        fields = "__all__"


class DiscountOfferAdminForm(forms.ModelForm):
    thumbnail = forms.ImageField(required=False, label="Upload New Thumbnail")
    remove_thumbnail = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = DiscountOffers
        fields = "__all__"


class ProductAdminForm(forms.ModelForm):
    thumbnail = forms.ImageField(required=False, label="Upload New Thumbnail")
    remove_thumbnail = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = Product
        fields = "__all__"


class ImageAlbumAdminForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Upload New Image")
    remove_image = forms.BooleanField(required=False, label="Remove Current Image")

    class Meta:
        model = ImageAlbum
        fields = "__all__"
