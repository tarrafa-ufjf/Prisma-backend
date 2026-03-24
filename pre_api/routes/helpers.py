from flask import request, jsonify

RANKING_TYPES = ("best-performance", "at-risk")


def parse_ranking_query_params():
    kind = request.args.get("type", "best-performance")
    if kind not in RANKING_TYPES:
        return None, None, jsonify({"error": "invalid 'type'. Use 'best-performance' or 'at-risk'"}), 400
    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        limit = 5

    limit = max(1, min(limit, 100))
    return kind, limit, None, None
