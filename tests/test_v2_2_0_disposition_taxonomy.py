from jammate_engine.core.voicing import (
    ClosedProjectionMethod,
    Disposition,
    DispositionFamily,
    OpenProjectionMethod,
    SpreadProjectionMethod,
    projection_spec_from_legacy_disposition,
)
from jammate_engine.core.voicing.disposition.models import Disposition as CanonicalDisposition
from jammate_engine.core.voicing.policy import Disposition as PolicyDisposition


def test_legacy_disposition_enum_has_single_canonical_definition() -> None:
    assert PolicyDisposition is CanonicalDisposition
    assert Disposition is CanonicalDisposition


def test_drop2_is_open_projection_method_not_top_level_family() -> None:
    assert DispositionFamily.OPEN.value == "open"
    assert OpenProjectionMethod.DROP2.value == "drop2"
    assert "drop2" not in {family.value for family in DispositionFamily}


def test_legacy_dispositions_normalize_to_projection_taxonomy() -> None:
    assert projection_spec_from_legacy_disposition(Disposition.CLOSED).family == DispositionFamily.CLOSED
    assert projection_spec_from_legacy_disposition(Disposition.CLOSED).closed_method == ClosedProjectionMethod.COMPACT

    assert projection_spec_from_legacy_disposition(Disposition.OPEN).family == DispositionFamily.OPEN
    assert projection_spec_from_legacy_disposition(Disposition.OPEN).open_method == OpenProjectionMethod.GENERIC_OPEN

    assert projection_spec_from_legacy_disposition(Disposition.TWO_HAND_SPREAD).family == DispositionFamily.SPREAD
    assert projection_spec_from_legacy_disposition(Disposition.TWO_HAND_SPREAD).spread_method == SpreadProjectionMethod.LOWER_UPPER_GROUPED

    assert projection_spec_from_legacy_disposition(Disposition.LEFT_ROOT_RIGHT_CHORD).family == DispositionFamily.SPREAD
    assert projection_spec_from_legacy_disposition(Disposition.LEFT_ROOT_RIGHT_CHORD).spread_method == SpreadProjectionMethod.FOUNDATION_PROJECTION

    assert projection_spec_from_legacy_disposition(Disposition.OPEN_ROOT_10TH).spread_method == SpreadProjectionMethod.ROOT_10TH_PROJECTION
