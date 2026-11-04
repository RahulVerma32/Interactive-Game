STORY_PROMPT = """Write one chapter of a three-chapter choose-your-own-adventure story as JSON, without markdown.
Return {"story_title": "...", "title": "...", "nodes": [{"content": "...", "choices": ["...", "...", "..."], "wrong_choice": 1}]}.
Write exactly 10 nodes for the requested chapter. Every node has exactly 3 short choices.
Make each decision medium difficulty: write three plausible, similarly detailed choices that fit the situation. Exactly two choices should be sensible and allow progress; exactly one should have a subtle but understandable risk or drawback and cost a heart. Avoid obvious jokes, reckless actions, or wording that gives away the answer. Set wrong_choice to the wrong action's 1-based position and vary its position across scenes. The player retries the same node after a wrong choice, so only safe actions advance.
Use this branching structure: node 1 branches to nodes 2, 3, or 4; nodes 2-4 branch to nodes 5, 6, or 7; nodes 5-7 lead to nodes 8, 9, or 8; nodes 8 and 9 lead to node 10. Node 10 leads into the next chapter, except in chapter 3, where it is the final ending and choices are not shown.
Write choices to fit their destination and keep merged scenes compatible with every preceding route. Continue naturally from the previous chapter when provided. Keep each node to 1-2 sentences.
"""
