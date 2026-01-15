from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from .models import User, Seller, Product


@receiver(pre_delete, sender=User)
def delete_user_files(sender, instance, **kwargs):
    """Delete user profile picture when user is deleted"""
    if instance.profile_picture:
        try:
            instance.profile_picture.delete(save=False)
        except Exception as e:
            print(f"Error deleting user profile picture: {e}")


@receiver(pre_delete, sender=Seller)
def delete_seller_id_card(sender, instance, **kwargs):
    """Delete seller ID card when seller is deleted"""
    if instance.id_card:
        try:
            instance.id_card.delete(save=False)
        except Exception as e:
            print(f"Error deleting seller ID card: {e}")


@receiver(pre_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    """Delete product image when product is deleted"""
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            print(f"Error deleting product image: {e}")


@receiver(pre_save, sender=User)
def delete_old_user_profile_picture(sender, instance, **kwargs):
    """Delete old profile picture when user updates their profile picture"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.profile_picture and old_instance.profile_picture != instance.profile_picture:
                old_instance.profile_picture.delete(save=False)
        except User.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error deleting old user profile picture: {e}")


@receiver(pre_save, sender=Seller)
def delete_old_seller_id_card(sender, instance, **kwargs):
    """Delete old ID card when seller updates their ID card"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = Seller.objects.get(pk=instance.pk)
            if old_instance.id_card and old_instance.id_card != instance.id_card:
                old_instance.id_card.delete(save=False)
        except Seller.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error deleting old seller ID card: {e}")


@receiver(pre_save, sender=Product)
def delete_old_product_image(sender, instance, **kwargs):
    """Delete old product image when product image is updated"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            if old_instance.image and old_instance.image != instance.image:
                old_instance.image.delete(save=False)
        except Product.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error deleting old product image: {e}")


@receiver(pre_save, sender=User)
def set_admin_role_for_superuser(sender, instance, **kwargs):
    """Set role to 'admin' when user is a superuser"""
    if instance.is_superuser:
        instance.role = 'admin'

