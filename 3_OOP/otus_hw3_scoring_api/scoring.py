import hashlib
import json
import datetime as dt


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    try:
        key_parts = [first_name or "",
                     last_name or "",
                     dt.datetime.strptime('01.02.1990', '%d.%m.%Y').strftime("%Y%m%d")]
        key = "uid:" + hashlib.md5("".join(key_parts).encode()).hexdigest()
    except:
        key = None

    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    cached_val = None

    if key:
        cached_val = store.cache_get(key, collection='score_collection', target_value_name='score')

    score = cached_val or 0

    if cached_val:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    # cache for 60 minutes
    store.cache_set(key=key,
                    value=score,
                    expire_after_seconds=60 * 60,
                    collection='score_collection',
                    target_value_name='score')
    return score


def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
