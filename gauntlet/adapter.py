"""Sends one attacker message to a target and returns its reply. Owner: C. Issue: "[C] External agent adapter".

- kind "zoo": call gauntlet.victims.reply(...) in-process.
- kind "http": POST target.request_template to target.url, where the exact string
  "{{message}}" becomes the message and "{{history}}" the conversation as
  [{"role": "user"|"assistant", "content": ...}]; read the reply text at the
  dotted target.reply_path (e.g. "choices.0.message.content"). HTTP >= 400 or a
  bad path raises TargetError. 60 s timeout.
"""

from gauntlet.schemas import TargetConfig, Turn
from gauntlet.stubs import stub


class TargetError(RuntimeError):
    pass


@stub("[C] External agent adapter")
async def send(target: TargetConfig, history: list[Turn], message: str) -> Turn:
    ...
