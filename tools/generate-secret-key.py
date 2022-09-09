#!/usr/bin/env python

import random
import string

print("".join(random.choices(string.ascii_letters + string.digits, k=64)))
