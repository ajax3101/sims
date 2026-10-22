"""Imports every module's models so Base.metadata is complete (Alembic, tests)."""

from sims.modules.academic.models import *  # noqa: F403
from sims.modules.finance.models import *  # noqa: F403
from sims.modules.imports.models import *  # noqa: F403
from sims.modules.performance.models import *  # noqa: F403
from sims.modules.staff.models import *  # noqa: F403
from sims.modules.students.models import *  # noqa: F403
