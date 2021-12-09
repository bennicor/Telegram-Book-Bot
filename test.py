from pymemcache.client import base

client = base.Client(("localhost", 11211))

client.set('some_key', 'some value')

# Retrieve previously set data again:
value = client.get('some_key')

print(value.decode("utf-8"))