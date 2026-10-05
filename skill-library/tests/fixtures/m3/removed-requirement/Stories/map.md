# User Stories

User stories with observable acceptance criteria, traceable to requirements.

<!-- sdlc:generated:start -->
## Documents

| ID | Document | Purpose | Status | Delivery |
|---|---|---|---|---|
| US-001 | [Import Appointments via CSV](US-001-import-appointments-via-csv.md) | Let front-desk staff bulk-load appointments so reminders can be scheduled without manual re-entry. | Draft | Not Started |
| US-002 | [Manually Enter an Appointment](US-002-manually-enter-an-appointment.md) | Let front-desk staff add a single appointment directly so it can receive a reminder without needing a CSV. | Draft | Not Started |
| US-003 | [Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md) | Let patients receive a timely reminder via SMS or email so they are less likely to miss their appointment. | Draft | Not Started |
| US-004 | [Configure Clinic Reminder Lead Time](US-004-configure-clinic-reminder-lead-time.md) | Let a clinic admin control how far ahead of an appointment reminders go out, so timing fits their patients. | Draft | Not Started |
| US-005 | [View Reminder Delivery Status](US-005-view-reminder-delivery-status.md) | Let front-desk staff confirm whether a patient's reminder actually went out, so they can follow up if it didn't. | Draft | Not Started |
| US-006 | [Set Reminder Channel Default and Per-Patient Override](US-006-set-reminder-channel-default-and-per-patient-override.md) | Let a clinic pick its default reminder channel and let staff override it for individual patients who need a different channel. | Draft | Not Started |

## Relationships

| Source | Relationship | Target |
|---|---|---|
| [US-001](US-001-import-appointments-via-csv.md) | Derived From | [PR-001](../PR/PR-001-appointment-reminders-for-clinics.md) |
| [US-001](US-001-import-appointments-via-csv.md) | Related To | [US-002](US-002-manually-enter-an-appointment.md) |
| [US-001](US-001-import-appointments-via-csv.md) | Related To | [US-003](US-003-send-automatic-appointment-reminder.md) |
| [US-002](US-002-manually-enter-an-appointment.md) | Related To | [US-001](US-001-import-appointments-via-csv.md) |
| [US-002](US-002-manually-enter-an-appointment.md) | Related To | [US-003](US-003-send-automatic-appointment-reminder.md) |
| [US-003](US-003-send-automatic-appointment-reminder.md) | Derived From | [PR-001](../PR/PR-001-appointment-reminders-for-clinics.md) |
| [US-003](US-003-send-automatic-appointment-reminder.md) | Related To | [US-001](US-001-import-appointments-via-csv.md) |
| [US-003](US-003-send-automatic-appointment-reminder.md) | Related To | [US-002](US-002-manually-enter-an-appointment.md) |
| [US-003](US-003-send-automatic-appointment-reminder.md) | Related To | [US-004](US-004-configure-clinic-reminder-lead-time.md) |
| [US-003](US-003-send-automatic-appointment-reminder.md) | Related To | [US-006](US-006-set-reminder-channel-default-and-per-patient-override.md) |
| [US-004](US-004-configure-clinic-reminder-lead-time.md) | Derived From | [PR-001](../PR/PR-001-appointment-reminders-for-clinics.md) |
| [US-004](US-004-configure-clinic-reminder-lead-time.md) | Related To | [US-003](US-003-send-automatic-appointment-reminder.md) |
| [US-004](US-004-configure-clinic-reminder-lead-time.md) | Related To | [US-006](US-006-set-reminder-channel-default-and-per-patient-override.md) |
| [US-005](US-005-view-reminder-delivery-status.md) | Derived From | [PR-001](../PR/PR-001-appointment-reminders-for-clinics.md) |
| [US-005](US-005-view-reminder-delivery-status.md) | Related To | [US-003](US-003-send-automatic-appointment-reminder.md) |
| [US-006](US-006-set-reminder-channel-default-and-per-patient-override.md) | Related To | [PR-001](../PR/PR-001-appointment-reminders-for-clinics.md) |
| [US-006](US-006-set-reminder-channel-default-and-per-patient-override.md) | Related To | [US-003](US-003-send-automatic-appointment-reminder.md) |
| [US-006](US-006-set-reminder-channel-default-and-per-patient-override.md) | Related To | [US-004](US-004-configure-clinic-reminder-lead-time.md) |
<!-- sdlc:generated:end -->

## Open Questions

- None yet.
