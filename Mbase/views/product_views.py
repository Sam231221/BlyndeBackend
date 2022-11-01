
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from Mbase.models import Product, Review
from Mbase.serializers import ProductSerializer

from rest_framework import status

from Mbase.models import Category,  ImageAlbum
from Mbase.serializers import CategorySerializer,ImageAlbumSerializer



'''
Generating API from python file.
------------------------------------------------------------
#With Response() method of DRF. You'll get Nice view
from django.http import JsonResponse

from .products import products
@api_view(['GET'])
def getRoutes(request):
    routes=['example.com', 'example.com/4',]
    return Response(routes)

@api_view(['GET'])
def getProducts(request):
    print(products)
    return Response(products)

@api_view(['GET'])
def getProduct(request, pk):
    product=None
    for i in products:
        if i['_id'] == pk:
            product = i
            break
    return Response(product)    
'''


@api_view(['GET'])
def getCategories(request):
    categories_obj = Category.objects.all().exclude(name__icontains='deals')
    categories = CategorySerializer(categories_obj, many=True).data
    print(categories)
    for category in categories:
        category_obj = Category.objects.filter(id=category['id']).first()
        category['genres'] = list(category_obj.genre_set.values())

    return Response(categories)


@api_view(['GET'])
def getAllProducts(request):
    products = Product.objects.all()
    serialized_data = ProductSerializer(products, many=True).data
    return Response(serialized_data)


@api_view(['GET'])
def getProducts(request):
    query = request.query_params.get('keyword')
    if query == None:
        query = ''

    products = Product.objects.filter(
        name__icontains=query).order_by('-createdAt')
    print('p:', products)
    page = request.query_params.get('page')
    paginator = Paginator(products, 4)

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    if page == None:
        page = 1

    page = int(page)
    print('Page:', page)
    serialized_products = ProductSerializer(products, many=True).data
    for product in serialized_products:
       product_obj = Product.objects.filter(_id=product['_id']).first()
       product['images'] = list(product_obj.imagealbum_set.values())

    return Response({'products': serialized_products, 'page': page, 'pages': paginator.num_pages})


@api_view(['GET'])
def getTopProducts(request):
    products = Product.objects.filter(rating__gte=4).order_by('-rating')[0:5]
    serialized_products = ProductSerializer(products, many=True).data
    for product in serialized_products:
       product_obj = Product.objects.filter(_id=product['_id']).first()
       product['images'] = list(product_obj.imagealbum_set.values())
    return Response(serialized_products)


@api_view(['GET'])
def getDealProducts(request):
    category_obj =Category.objects.filter(name__icontains="deals").first()
    products = Product.objects.filter(category=category_obj)[0:6]
    serialized_products = ProductSerializer(products, many=True).data
    for product in serialized_products:
       product_obj = Product.objects.filter(_id=product['_id']).first()
       imagealbum_objs= ImageAlbum.objects.filter(product=product_obj) 
       product['images'] = ImageAlbumSerializer(imagealbum_objs, many=True).data

    return Response(serialized_products)


@api_view(['GET'])
def getRecentProducts(request):
    category_obj = Category.objects.filter(name__icontains="deals").first()
    products = Product.objects.order_by('-createdAt').exclude(category=category_obj)[0:8]
    serialized_products = ProductSerializer(products, many=True).data
    for product in serialized_products:
       product_obj = Product.objects.filter(_id=product['_id']).first()
       imagealbum_objs= ImageAlbum.objects.filter(product=product_obj) 
       product['images'] = ImageAlbumSerializer(imagealbum_objs, many=True).data

    return Response(serialized_products)


@api_view(['GET'])
def getFeaturedProducts(request):
    products = Product.objects.filter(is_featured=True)[0:8]
    serialized_products = ProductSerializer(products, many=True).data
    for product in serialized_products:
       product_obj = Product.objects.filter(_id=product['_id']).first()
       product['images'] = list(product_obj.imagealbum_set.values())

    return Response(serialized_products)

@api_view(['GET'])
def getProduct(request, pk):
    product = Product.objects.get(_id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def createProduct(request):
    user = request.user
    product = Product.objects.create(
        user=user,
        name='Sample Name',
        price=0,
        brand='Sample Brand',
        countInStock=0,
        description=''
    )

    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateProduct(request, pk):
    data = request.data
    product = Product.objects.get(_id=pk)
    print(data['category'])
    product.name = data['name']
    product.price = data['price']
    product.brand = data['brand']
    product.countInStock = data['countInStock']
    product.category = Category.objects.filter(name=data['category']).first()
    product.description = data['description']

    product.save()

    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteProduct(request, pk):
    product = Product.objects.get(_id=pk)
    product.delete()
    return Response('Producted Deleted')


@api_view(['POST'])
def uploadImage(request):
    data = request.data

    product_id = data['product_id']
    product = Product.objects.get(_id=product_id)

    product.image = request.FILES.get('image')
    product.save()

    return Response('Image was uploaded')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request, pk):
    user = request.user
    product = Product.objects.get(_id=pk)
    data = request.data

    # 1 - Review already exists
    alreadyExists = product.review_set.filter(user=user).exists()
    if alreadyExists:
        content = {'detail': 'Product already reviewed'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # 2 - No Rating or 0
    elif data['rating'] == 0:
        content = {'detail': 'Please select a rating'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # 3 - Create review
    else:
        review = Review.objects.create(
            user=user,
            product=product,
            name=user.first_name,
            rating=data['rating'],
            comment=data['comment'],
        )

        reviews = product.review_set.all()
        product.numReviews = len(reviews)

        total = 0
        for i in reviews:
            total += i.rating

        product.rating = total / len(reviews)
        product.save()

        return Response('Review Added')
