"""Four hand-written trajectories for airline task id=3.

Gold/silent replay the two gold GET tools so ActionEvaluator can match them.
Cheat says nothing useful except a flight number that happens to contain
the substring communicate_info requires ("4"). Refuse is the empty agent.
"""

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    ToolCall,
    ToolMessage,
    UserMessage,
)

USER_TURN = UserMessage.text(
    "Hi, I'm Anya Garcia, user id anya_garcia_5901, confirmation JMO1MG. "
    "How many suitcases can I bring on my upcoming flight? I'm pretty sure "
    "I'm a Gold member. Please give me the total as a number."
)


def _get(name: str, arguments: dict, call_id: str) -> list[Message]:
    """One assistant tool call + a dummy ToolMessage (ids must pair)."""
    return [
        AssistantMessage(
            role="assistant",
            tool_calls=[
                ToolCall(id=call_id, name=name, arguments=arguments),
            ],
        ),
        ToolMessage(id=call_id, role="tool", content="{}"),
    ]


# Gold GET tools from evaluation_criteria.actions. Dummy tool outputs are
# enough: EnvironmentEvaluator skips non-mutating tools on replay.
_LOOKUPS: list[Message] = [
    *_get("get_reservation_details", {"reservation_id": "JMO1MG"}, "call_res"),
    *_get("get_user_details", {"user_id": "anya_garcia_5901"}, "call_user"),
]


gold: list[Message] = [
    USER_TURN,
    *_LOOKUPS,
    AssistantMessage.text(
        "You are actually a Silver member, not Gold. "
        "You can bring 4 suitcases."
    ),
]

silent: list[Message] = [
    USER_TURN,
    *_LOOKUPS,
    AssistantMessage.text(
        "I have reviewed your reservation and membership. "
        "Let me know if you have other questions."
    ),
]

# Solves nothing. The "4" inside AA-1234 is the whole point.
cheat: list[Message] = [
    USER_TURN,
    AssistantMessage.text("your flight is AA-1234"),
]

refuse: list[Message] = []


TRAJECTORIES: dict[str, list[Message]] = {
    "gold": gold,
    "silent": silent,
    "cheat": cheat,
    "refuse": refuse,
}
