from datetime import datetime

from domain.entities.compass_draft import CompassDraft
from domain.entities.context_compass import ContextCompass
from domain.exceptions import ContextTooLarge, IncompleteDraft
from domain.value_objects.token_count import TokenCount


class CompassPromotionPolicy:
    @staticmethod
    def promote(
        draft: CompassDraft, token_ceiling: int = 1000
    ) -> ContextCompass:
        if not draft.quick_commands:
            raise IncompleteDraft("Draft must have quick commands.")

        if not draft.key_files:
            raise IncompleteDraft("Draft must have key files.")

        total_chars = (
            len(draft.quick_commands)
            + sum(len(f) for f in draft.key_files)
            + len(draft.non_obvious_patterns)
            + len(draft.gotchas)
            + sum(len(s) for s in draft.see_also)
        )
        estimated_tokens = total_chars // 4

        if estimated_tokens > token_ceiling:
            raise ContextTooLarge(
                f"Assembled token count {estimated_tokens} exceeds "
                f"ceiling {token_ceiling}"
            )

        token_count = TokenCount(value=estimated_tokens, ceiling=token_ceiling)

        return ContextCompass(
            quick_commands=draft.quick_commands,
            key_files=draft.key_files,
            non_obvious_patterns=draft.non_obvious_patterns,
            gotchas=draft.gotchas,
            see_also=draft.see_also,
            token_count=token_count,
            last_updated=datetime.now(),
        )
