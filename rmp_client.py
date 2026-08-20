"""rmp_client.py — minimal RateMyProfessors lookups via the unofficial GraphQL endpoint.

No official API exists. This uses the same public GraphQL endpoint + fixed Basic-auth
token (base64 "test:test") that every open-source RMP wrapper uses (RateMyProfessorAPI,
rmp_client, etc.) — it's the token RMP's own web client ships with, not a private
credential. Bounded, cached, personal/demo use per project scope.
"""
import json, os, time, requests

GQL_URL = "https://www.ratemyprofessors.com/graphql"
AUTH = "Basic dGVzdDp0ZXN0"
HEADERS = {"Authorization": AUTH, "Content-Type": "application/json",
           "User-Agent": "cmu-course-helper/0.1 (student project, bounded demo use)"}
CACHE_FILE = "rmp_cache.json"

SCHOOL_QUERY = """
query NewSearchSchoolsQuery($query: SchoolSearchQuery!) {
  newSearch { schools(query: $query) { edges { node { id name city state } } } }
}"""

TEACHER_QUERY = """
query NewSearchTeachersQuery($query: TeacherSearchQuery!) {
  newSearch {
    teachers(query: $query) {
      edges {
        node {
          id firstName lastName department
          avgRating avgDifficulty numRatings wouldTakeAgainPercent
          school { name }
        }
      }
    }
  }
}"""

def _gql(query, variables):
    r = requests.post(GQL_URL, headers=HEADERS, json={"query": query, "variables": variables}, timeout=20)
    r.raise_for_status()
    return r.json()

def _load_cache():
    return json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}

def _save_cache(c):
    json.dump(c, open(CACHE_FILE, "w"), indent=2)

def find_school_id(name="Carnegie Mellon University"):
    data = _gql(SCHOOL_QUERY, {"query": {"text": name}})
    edges = data["data"]["newSearch"]["schools"]["edges"]
    for e in edges:
        if e["node"]["name"] == name:
            return e["node"]["id"]
    return edges[0]["node"]["id"] if edges else None

def _name_matches(query, node):
    """Surname must match exactly. First name (if given) needs at least a shared
    stem, so 'Dave'/'David' pass but 'Bryan Parno' != 'Bryan Routledge' (first-name-
    only overlap) and 'Keenan Crane' != 'Earl Crane' (surname-only overlap)."""
    qtoks = query.split()
    last_q, last_n = qtoks[-1].lower(), node["lastName"].lower()
    if last_q != last_n:
        return False
    if len(qtoks) == 1:
        return True
    first_q, first_n = qtoks[0].lower(), node["firstName"].lower()
    return (first_n.startswith(first_q) or first_q.startswith(first_n)
            or first_n[:3] == first_q[:3])

def lookup_professor(name, school_id, cache=None):
    cache = cache if cache is not None else _load_cache()
    if name in cache:
        return cache[name]
    data = _gql(TEACHER_QUERY, {"query": {"text": name, "schoolID": school_id}})
    edges = [e["node"] for e in data["data"]["newSearch"]["teachers"]["edges"]]
    matches = [n for n in edges if _name_matches(name, n)]
    result = matches[0] if matches else None
    cache[name] = result
    _save_cache(cache)
    return result

def lookup_many(names, school_name="Carnegie Mellon University", delay=1.5):
    school_id = find_school_id(school_name)
    cache = _load_cache()
    out = {}
    for n in names:
        out[n] = lookup_professor(n, school_id, cache)
        time.sleep(delay)
    return out
