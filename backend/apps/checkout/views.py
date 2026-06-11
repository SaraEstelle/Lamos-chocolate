from django.http import HttpResponse

def stripe_webhook_view(request):
    return HttpResponse("Webhook received", status=200)
