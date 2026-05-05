# Models have been moved to domain-specific apps.
# This file re-exports them for backwards compatibility.
from accounts.models import User, StudentProfile, CompanyProfile  # noqa: F401
from offers.models import InternshipOffer, InternshipOfferView  # noqa: F401
from applications.models import InternshipApplication  # noqa: F401
from notifications.models import Notification  # noqa: F401
