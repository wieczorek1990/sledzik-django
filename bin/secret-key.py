#!/usr/bin/env python3
# Generator of secret keys.

from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()

print(secret_key)
