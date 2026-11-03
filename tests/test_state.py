from cacheflow.state import RunState, RunStatus


def test_run_state_protects_spine_messages_and_tracks_scratch():
    state = RunState(
        run_id="r1",
        workflow="demo",
        status=RunStatus.RUNNING,
        message_history=[],
        protected_indices=[],
    )

    state.add_message({"role": "user", "content": "hello", "metadata": {}})
    state.add_message({"role": "assistant", "content": "ok", "metadata": {"classification": "reasoning"}})
    state.add_message({"role": "assistant", "content": "scratch", "metadata": {}})

    assert state.protected_indices == [0, 1]
    assert state.message_classifications[0] == "spine"
    assert state.message_classifications[1] == "reasoning"
    assert state.scratch_indices() == [2]

    state.classify_all()
    assert state.protected_indices == [0, 1]
    assert state.scratch_indices() == [2]
