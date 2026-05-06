"""
OMA Agent — Migration Chainer (Module 26)
Executes incremental, step-by-step migrations for large version jumps.
e.g. 15.0 -> 19.0 becomes 15->16, 16->17, 17->18, 18->19.
"""

from __future__ import annotations

import logging
import copy
from typing import Any

from backend.migration_engine import migrate_code
from backend.schemas import MigrationRequest, MigrationResponse, OdooVersion

logger = logging.getLogger(__name__)

# The ordered list of supported versions
_VERSION_ORDER = [OdooVersion.V15, OdooVersion.V16, OdooVersion.V17, OdooVersion.V18, OdooVersion.V19]


async def run_incremental_migration(
    request: MigrationRequest, 
    context: dict[str, Any] | None = None
) -> MigrationResponse:
    """
    Run migration step-by-step through intermediate versions.
    The output of step N becomes the input of step N+1.
    """
    src_idx = _VERSION_ORDER.index(request.source_version)
    tgt_idx = _VERSION_ORDER.index(request.target_version)

    if src_idx >= tgt_idx:
        # Fallback to standard migration if no steps needed
        return await migrate_code(request, context)

    current_code = request.file_content
    original_code = request.file_content
    steps_record = []
    
    logger.info("Starting incremental migration %s -> %s for %s", 
                request.source_version.value, request.target_version.value, request.filename)

    # Walk through each adjacent version pair
    for i in range(src_idx, tgt_idx):
        step_src = _VERSION_ORDER[i]
        step_tgt = _VERSION_ORDER[i + 1]

        logger.info("Incremental step: %s -> %s", step_src.value, step_tgt.value)

        # Create a new request for this specific step
        step_request = copy.deepcopy(request)
        step_request.source_version = step_src
        step_request.target_version = step_tgt
        step_request.file_content = current_code

        # Run the step
        step_response = await migrate_code(step_request, context)
        current_code = step_response.migrated_code

        # Record the step
        steps_record.append({
            "step": f"{step_src.value} -> {step_tgt.value}",
            "migrated_code": current_code,
            "issues": [issue.dict() for issue in step_response.issues],
        })

    # The final step_response contains the diff between the penultimate and target.
    # We need to construct a final response that represents the FULL jump.
    from backend.migration_engine import _generate_diff
    from backend.issue_detector import detect_issues

    full_diff = _generate_diff(
        original=original_code,
        new=current_code,
        filename=request.filename,
        src=request.source_version.value,
        tgt=request.target_version.value
    )

    # Detect issues on the original code for the final report
    original_issues = detect_issues(original_code, request.source_version)

    return MigrationResponse(
        module_name=request.module_name,
        source_version=request.source_version.value,
        target_version=request.target_version.value,
        original_code=original_code,
        migrated_code=current_code,
        diff=full_diff,
        issues=original_issues,
        explanation="",  # Will be filled by explainer if needed
        filename=request.filename,
        incremental_steps=steps_record,
    )
