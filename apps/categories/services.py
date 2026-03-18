from .models import Category

DEFAULT_CATEGORIES = [
    # Income
    {'name': 'Salary', 'icon': 'briefcase', 'color': '#28a745', 'category_type': 'income'},
    {'name': 'Freelance', 'icon': 'laptop', 'color': '#20c997', 'category_type': 'income'},
    {'name': 'Investment Returns', 'icon': 'chart-line', 'color': '#17a2b8', 'category_type': 'income'},
    {'name': 'Rental Income', 'icon': 'home', 'color': '#6f42c1', 'category_type': 'income'},
    {'name': 'Other Income', 'icon': 'plus-circle', 'color': '#6c757d', 'category_type': 'income'},

    # Expense — with children
    {'name': 'Housing', 'icon': 'house', 'color': '#dc3545', 'category_type': 'expense', 'children': [
        {'name': 'Rent / Mortgage', 'icon': 'key', 'color': '#dc3545'},
        {'name': 'Utilities', 'icon': 'bolt', 'color': '#fd7e14'},
        {'name': 'Internet', 'icon': 'wifi', 'color': '#0dcaf0'},
    ]},
    {'name': 'Food & Dining', 'icon': 'utensils', 'color': '#fd7e14', 'category_type': 'expense', 'children': [
        {'name': 'Groceries', 'icon': 'shopping-basket', 'color': '#fd7e14'},
        {'name': 'Restaurants', 'icon': 'concierge-bell', 'color': '#e83e8c'},
        {'name': 'Coffee', 'icon': 'coffee', 'color': '#795548'},
    ]},
    {'name': 'Transport', 'icon': 'car', 'color': '#0d6efd', 'category_type': 'expense', 'children': [
        {'name': 'Fuel', 'icon': 'gas-pump', 'color': '#0d6efd'},
        {'name': 'Public Transport', 'icon': 'bus', 'color': '#6610f2'},
        {'name': 'Ride Share', 'icon': 'taxi', 'color': '#ffc107'},
    ]},
    {'name': 'Healthcare', 'icon': 'heartbeat', 'color': '#e83e8c', 'category_type': 'expense', 'children': [
        {'name': 'Medical', 'icon': 'stethoscope', 'color': '#dc3545'},
        {'name': 'Pharmacy', 'icon': 'pills', 'color': '#e83e8c'},
        {'name': 'Gym / Fitness', 'icon': 'dumbbell', 'color': '#20c997'},
    ]},
    {'name': 'Entertainment', 'icon': 'film', 'color': '#6f42c1', 'category_type': 'expense', 'children': [
        {'name': 'Streaming', 'icon': 'play-circle', 'color': '#e50914'},
        {'name': 'Gaming', 'icon': 'gamepad', 'color': '#6f42c1'},
        {'name': 'Hobbies', 'icon': 'paint-brush', 'color': '#fd7e14'},
    ]},
    {'name': 'Shopping', 'icon': 'shopping-cart', 'color': '#ffc107', 'category_type': 'expense', 'children': [
        {'name': 'Clothing', 'icon': 'tshirt', 'color': '#ffc107'},
        {'name': 'Electronics', 'icon': 'mobile-alt', 'color': '#17a2b8'},
    ]},
    {'name': 'Education', 'icon': 'graduation-cap', 'color': '#0dcaf0', 'category_type': 'expense'},
    {'name': 'Travel', 'icon': 'plane', 'color': '#20c997', 'category_type': 'expense'},
    {'name': 'Savings & Investments', 'icon': 'piggy-bank', 'color': '#198754', 'category_type': 'both'},
    {'name': 'Other Expenses', 'icon': 'ellipsis-h', 'color': '#6c757d', 'category_type': 'expense'},
]


def seed_default_categories(user):
    """Create default categories for a new user."""
    for cat_data in DEFAULT_CATEGORIES:
        children = cat_data.pop('children', [])
        parent = Category.objects.create(
            user=user,
            is_system=True,
            **cat_data,
        )
        for child_data in children:
            Category.objects.create(
                user=user,
                parent=parent,
                is_system=True,
                category_type=cat_data.get('category_type', 'expense'),
                **child_data,
            )
        # Restore children key for next call safety
        cat_data['children'] = children


def get_category_tree(user):
    """Return categories as a nested tree (parents only, children nested)."""
    parents = Category.objects.filter(
        user=user, parent__isnull=True
    ).prefetch_related('children')
    return parents
