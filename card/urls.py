from django.urls import path
from .views import (
    cards,
    create_card,
    freeze_and_unfreeze_card,
    fund_card,
    withdraw_from_card,
    cancel_card,
    card_transactions,
    card_statement,
    test
)

urlpatterns = [
    path('', cards, name='cards'),
    path('create_card/', create_card, name='create_card'),
    path('freeze_and_unfreeze_card/<card_id>/', freeze_and_unfreeze_card, name='freeze_and_unfreeze_card'),
    path('fund_card/<card_id>/', fund_card, name='fund_card'),
    path('withdraw_from_card/<card_id>/', withdraw_from_card, name='withdraw_from_card'),
    path('cancel_card/<card_id>/', cancel_card, name='cancel_card'),
    path('card_transactions/<card_id>/', card_transactions, name='card_transactions'),
    path('card_statement/<card_id>/', card_statement, name='card_statement'),
    path('test/', test, name='test')
]
