"""
What my test runs, one scenario per criterion in criteria.md. (Unit 8, Milestone 3)

`run_eval.py` runs the "texts" scenarios below, three trials each.
Criteria 4 and 5 need things run_eval.py cannot express (an appeal after a
submission; a request body that is a bare list), so `run_checks.py` runs those.

Criterion 1 ("my own writing, at most 1 of 10 flagged") is NOT here yet: it
needs ten pieces the author actually wrote, and none were available when this
was set up. Add them as a scenario with "criterion": 1 and re-run.
"""

SCENARIOS = [
    {
        # Criterion 2: at most 1 of 5 plain human pieces labeled AI, and at
        # least 3 of 5 labeled "unsure" or "human".
        "name": "plain human writing",
        "criterion": 2,
        "texts": [
            "I like my town. It is small and quiet. I go to school every day and I walk with my friends. We play football after class. My mother cooks dinner at six. I think my town is a good place to live because the people are kind.",
            "My name is Ana. I am from Brazil. I live in a small flat with my sister. In the morning I drink coffee and take the bus to work. I work in a shop. I like my job because I meet many people.",
            "Last weekend I went to the park with my dog. The weather was good. We played with a ball for a long time. Then we sat on a bench and I ate a sandwich. My dog was very tired when we got home.",
            "I want to be a nurse. I want to help sick people. My aunt is a nurse and she is my hero. I study biology and chemistry at school. It is hard but I try my best every day.",
            "Our school has a library. It has many books and some computers. I go there after lunch to read. The teacher is nice and she helps me find good books. I read one book each week.",
        ],
    },
    {
        # Criterion 3: AI group averages at least 0.30 above the human group,
        # and at least 4 of the 5 AI pieces score above 0.50. Scenario names
        # starting "spread-" are compared as a pair.
        "name": "spread-ai",
        "criterion": 3,
        "texts": [
            "Artificial intelligence is transforming the way businesses operate in today's rapidly evolving digital landscape. It is important to note that organizations must carefully consider several key factors when implementing new technologies. Furthermore, effective communication and collaboration are essential to ensuring successful outcomes. By leveraging innovative solutions, companies can improve efficiency, enhance productivity, and drive sustainable growth.",
            "Climate change is one of the most pressing challenges facing our planet today. It is essential to understand that its effects are wide-ranging and impact every aspect of society. Moreover, addressing this issue requires a collaborative approach involving governments, businesses, and individuals. By taking proactive steps, we can create a more sustainable and resilient future for generations to come.",
            "Effective time management is a crucial skill for achieving success in both personal and professional life. It is important to prioritize tasks and set clear goals in order to maximize productivity. Additionally, minimizing distractions and maintaining a healthy work-life balance can significantly enhance overall well-being. Ultimately, developing strong time management habits leads to greater fulfillment.",
            "Social media has fundamentally changed the way people communicate and share information across the globe. It offers numerous benefits, including increased connectivity and access to diverse perspectives. However, it is also important to consider the potential drawbacks, such as misinformation and privacy concerns. Overall, a balanced approach to social media use is essential for a healthy digital life.",
            "Regular physical exercise plays a vital role in maintaining good health and overall well-being. It is well established that engaging in consistent activity can reduce the risk of chronic diseases and improve mental health. Furthermore, incorporating a variety of exercises into a routine can enhance strength, flexibility, and endurance. In conclusion, prioritizing fitness is a valuable investment in long-term health.",
        ],
    },
    {
        "name": "spread-human",
        "criterion": 3,
        "texts": [
            "Honestly? I burned the toast again. Third time this week. My brother laughed so hard he nearly choked on his coffee, and then the smoke alarm went off, which set the dog howling — what a morning. Mum rang at nine to ask if we were all still alive. Barely.",
            "Nobody warned me the ferry smelled of diesel and wet dog. Two hours in, a man with a accordion started on something mournful; a kid threw up over the rail; I ate a cold pie and, God help me, enjoyed it. Docked at six. Rain, of course.",
            "My grandfather's workshop: sawdust in the floorboards, a radio stuck on one station, jars of mismatched screws. He never threw anything out. When he died we found forty-one tape measures. Forty-one! I took one. It still reads two millimetres short.",
            "Look, the soup was fine. Salty, sure, but fine. What I can't forgive is Dave pouring it into the sink in front of everyone and saying 'never again' like he'd survived a shipwreck. Dave. It was soup.",
            "Rehearsal ran till midnight, then the van wouldn't start, then Priya found a kebab shop still open and we sat on the kerb eating chips out of paper, hoarse and happy, arguing about the bridge in track three until the first bus came.",
        ],
    },
]


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")
        texts = scenario.get("texts")
        bodies = scenario.get("bodies")
        if texts and bodies:
            problems.append(f"scenario {i} has both texts and bodies — pick one")
            continue
        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(f"scenario {i}, body {j} is not a dict")
            continue
        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue
        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(f"scenario {i}, text {j} is empty — use 'bodies' for that")
            elif str(text).startswith("REPLACE ME"):
                problems.append(f"scenario {i}, text {j} is still the placeholder")
    return problems
