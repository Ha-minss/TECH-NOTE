import unittest

from storeops.core.contracts import WorkflowState
from storeops.operator.transitions import InvalidStateTransition, transition


class StateTransitionTests(unittest.TestCase):
    def test_review_states_can_enter_human_review(self) -> None:
        for source in (
            WorkflowState.READY_FOR_REVIEW,
            WorkflowState.DEGRADED_REVIEW,
            WorkflowState.CONFLICT_REVIEW,
        ):
            with self.subTest(source=source):
                self.assertEqual(
                    WorkflowState.HUMAN_REVIEW,
                    transition(source, WorkflowState.HUMAN_REVIEW),
                )

    def test_handoff_requires_route_approval(self) -> None:
        with self.assertRaises(InvalidStateTransition):
            transition(
                WorkflowState.HUMAN_REVIEW,
                WorkflowState.HANDED_OFF,
            )

    def test_approved_route_can_be_handed_off(self) -> None:
        self.assertEqual(
            WorkflowState.HANDED_OFF,
            transition(
                WorkflowState.ROUTE_APPROVED,
                WorkflowState.HANDED_OFF,
            ),
        )

    def test_terminal_state_cannot_transition(self) -> None:
        with self.assertRaises(InvalidStateTransition):
            transition(
                WorkflowState.HANDED_OFF,
                WorkflowState.READY_FOR_REVIEW,
            )


if __name__ == "__main__":
    unittest.main()
