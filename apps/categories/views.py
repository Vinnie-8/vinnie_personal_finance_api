from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils.dateparse import parse_date

from .models import Category
from .serializers import CategorySerializer, CategoryCreateSerializer
from .services import seed_default_categories, get_category_tree


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/categories/ — list all user categories as a tree
    POST /api/categories/ — create a custom category
    """

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryCreateSerializer
        return CategorySerializer

    def get_queryset(self):
        # Top-level categories only; children come via nested serializer
        return get_category_tree(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_system=False)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/categories/<id>/ — retrieve with children
    PUT    /api/categories/<id>/ — update name/icon/color
    DELETE /api/categories/<id>/ — delete (user-created only)
    """
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.is_system:
            return Response(
                {'detail': 'System categories cannot be deleted.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Re-assign transactions to parent or null
        category.transactions.update(category=category.parent)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryStatsView(APIView):
    """GET /api/categories/<id>/stats/?start=&end= — spending totals"""

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk, user=request.user)
        qs = category.transactions.all()

        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(date__gte=parse_date(start))
        if end:
            qs = qs.filter(date__lte=parse_date(end))

        aggregates = qs.aggregate(
            total=Sum('amount'),
            count=Count('id'),
        )
        # Monthly breakdown
        monthly = (
            qs
            .extra(select={'month': "DATE_TRUNC('month', date)"})
            .values('month')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )
        return Response({
            'category': CategorySerializer(category).data,
            'total': aggregates['total'] or 0,
            'count': aggregates['count'],
            'monthly_breakdown': list(monthly),
        })


class SeedCategoriesView(APIView):
    """POST /api/categories/seed/ — re-apply default categories"""

    def post(self, request):
        # Only add missing defaults, don't duplicate
        existing_names = set(
            Category.objects.filter(user=request.user, is_system=True)
            .values_list('name', flat=True)
        )
        seed_default_categories(request.user)
        return Response({'message': 'Default categories applied.'})
