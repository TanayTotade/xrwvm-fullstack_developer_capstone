# Uncomment the required imports before adding the code

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate

from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def get_cars(request):
    count = CarMake.objects.filter().count()
    print(count)
    if(count == 0):
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels":cars})
    
# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    data = {"userName":""}
    return JsonResponse(data)

# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    context = {}

    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    email_exist = False
    try:
        User.objects.get(username=username)
        username_exist = True
    except:
        logger.debug("{} is new user".format(username))

    if not username_exist:
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,password=password, email=email)
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    else :
        data = {"userName":username,"error":"Already Registered"}
        return JsonResponse(data)

def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = f"/fetchDealers/{state}"

    response = get_request(endpoint)

    if isinstance(response, dict) and "data" in response:
        dealerships = response["data"]
    else:
        dealerships = []

    print("FINAL DEALERS COUNT:", len(dealerships))

    return JsonResponse({
        "status": 200,
        "dealers": dealerships
    })

def get_dealer_reviews(request, dealer_id):
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})

    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    response = get_request(endpoint)

    reviews = []

    # ✅ response IS A LIST
    if isinstance(response, list):
        for review in response:
            review_detail = {
                "name": review.get("name", ""),
                "review": review.get("review", ""),
                "purchase": review.get("purchase", False),
                "purchase_date": review.get("purchase_date", ""),
                "car_make": review.get("car_make", ""),
                "car_model": review.get("car_model", ""),
                "car_year": review.get("car_year", ""),
            }

            sentiment_response = analyze_review_sentiments(
                review_detail["review"]
            )

            review_detail["sentiment"] = (
                sentiment_response.get("sentiment", "neutral")
                if sentiment_response else "neutral"
            )

            reviews.append(review_detail)

    return JsonResponse({"status": 200, "reviews": reviews})




def get_dealer_details(request, dealer_id):
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})
    
    endpoint = f"/fetchDealer/{dealer_id}"
    response = get_request(endpoint)

    dealer = response[0] if isinstance(response, list) and len(response) > 0 else {}

    return JsonResponse({
        "status": 200,
        "dealer": dealer
    })


def add_review(request):
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})
