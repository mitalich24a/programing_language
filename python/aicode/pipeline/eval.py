
async def evaluate_agent(harness):

    test_cases = [

        {
            "query": "What is the international transfer limit?",
            "expected_terms": ["10,000"]
        },

        {
            "query": "How long does an international transfer take?",
            "expected_terms": ["business days"]
        },

        {
            "query": "What is the exchange rate from USD to INR?",
            "expected_terms": ["88"]
        }
    ]

    passed = 0

    for index, test in enumerate(test_cases):

        answer = await harness.run(
            tenant_id="retail",
            user_id="EVALUATION_USER",
            conversation_id=f"TEST_{index}",
            query=test["query"]
        )

        answer_lower = str(answer).lower()

        expected = test["expected_terms"]

        success = any(
            term.lower() in answer_lower
            for term in expected
        )

        if success:
            passed += 1

        print("\nQuery:", test["query"])
        print("Answer:", answer)
        print("Passed:", success)

    print("\nEvaluation summary")
    print("Total:", len(test_cases))
    print("Passed:", passed)
    print("Failed:", len(test_cases) - passed)

    accuracy = passed / len(test_cases)

    print("Pass rate:", accuracy * 100, "%")
