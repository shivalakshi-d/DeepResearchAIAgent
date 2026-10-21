from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("AI news", max_results=5))

    print("Results count:", len(results))
    print(results[:2])