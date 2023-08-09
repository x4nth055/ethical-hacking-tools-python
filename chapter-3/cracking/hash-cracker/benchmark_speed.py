import timeit

hash_names = [
    'md5', 'sha1', 
    'sha224', 'sha256', 'sha384', 'sha512', 
    'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512', 
    'blake2b', 'blake2s',
]

for hash_name in hash_names:
    print(f"[*] Benchmarking {hash_name}...")
    setup = f"import hashlib; hash_fn = hashlib.{hash_name}"
    print(timeit.timeit('hash_fn(b"test").hexdigest()', setup=setup, number=1000000))
    print()