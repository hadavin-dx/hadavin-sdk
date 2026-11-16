import os, random
def pytest_collection_modifyitems(session, config, items):
    seed = int(os.environ["SHUF_SEED"])
    print(f"SHUFFLE seed={seed} items={len(items)}")
    random.Random(seed).shuffle(items)
