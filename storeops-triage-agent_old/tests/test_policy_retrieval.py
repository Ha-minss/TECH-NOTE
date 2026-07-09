import json
import unittest
from pathlib import Path

import numpy as np

from storeops.core.retrieval import (
    DeterministicEmbeddingProvider,
    HybridPolicyRetriever,
    PolicyDocumentLoader,
)


class PolicyRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.policy_dir = self.project_root / "data" / "policies" / "offline_payment_ops"

    def test_loader_indexes_each_small_policy_document_as_one_full_chunk(self):
        documents = PolicyDocumentLoader(self.policy_dir).load()

        self.assertEqual(len(documents), 5)
        self.assertEqual(
            {document.chunk_id for document in documents},
            {
                "SOP-PAY-OP-001#full",
                "SOP-PAY-OP-002#full",
                "SOP-PAY-OP-003#full",
                "SOP-PAY-OP-004#full",
                "SOP-PAY-OP-005#full",
            },
        )
        self.assertTrue(
            all(document.metadata["document_type"] == "synthetic_operating_guide" for document in documents)
        )

    def test_hybrid_retriever_returns_terminal_policy_for_new_terminal_failure(self):
        retriever = HybridPolicyRetriever.from_policy_dir(
            self.policy_dir,
            embedding_provider=DeterministicEmbeddingProvider(),
            dense_weight=0.6,
            bm25_weight=0.4,
        )

        results = retriever.search("신규 단말기 설치 식별 정보 검증 지침", top_k=2)

        self.assertIn("SOP-PAY-OP-002", {result.document_id for result in results})
        self.assertAlmostEqual(results[0].dense_weight, 0.6)
        self.assertAlmostEqual(results[0].bm25_weight, 0.4)

    def test_hybrid_retriever_returns_pos_policy_for_pos_timeout(self):
        retriever = HybridPolicyRetriever.from_policy_dir(
            self.policy_dir,
            embedding_provider=DeterministicEmbeddingProvider(),
            dense_weight=0.6,
            bm25_weight=0.4,
        )

        results = retriever.search("POS payment timeout Front connection", top_k=1)

        self.assertEqual(results[0].document_id, "SOP-PAY-OP-004")

    def test_embedding_provider_returns_normalized_vectors(self):
        provider = DeterministicEmbeddingProvider()

        vectors = provider.embed(["POS timeout", "merchant registration missing"])

        self.assertEqual(vectors.shape[0], 2)
        norms = np.linalg.norm(vectors, axis=1)
        self.assertTrue(np.allclose(norms, np.ones_like(norms)))

    def test_retrieval_golden_cases_include_required_policies_in_top_k(self):
        evaluation_path = self.project_root / "data" / "evaluation" / "retrieval_cases.json"
        cases = json.loads(evaluation_path.read_text(encoding="utf-8"))
        retriever = HybridPolicyRetriever.from_policy_dir(
            self.policy_dir,
            embedding_provider=DeterministicEmbeddingProvider(),
            dense_weight=0.6,
            bm25_weight=0.4,
        )

        failures = []
        for case in cases:
            results = retriever.search(case["query"], top_k=case["top_k"])
            retrieved_ids = [result.document_id for result in results]
            missing = sorted(set(case["required_policy_ids"]) - set(retrieved_ids))
            if missing:
                failures.append(
                    {
                        "case_id": case["case_id"],
                        "missing": missing,
                        "retrieved": retrieved_ids,
                    }
                )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()