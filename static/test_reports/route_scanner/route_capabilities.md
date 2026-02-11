# Route Capability Report (2025-11-08T19:32:48)

## QR-Typen Übersicht
- **URL**: 5 Routen
- **VCARD**: 9 Routen
- **IMAGE**: 6 Routen
- **SMS**: 4 Routen
- **WIFI**: 3 Routen
- **EMAIL**: 4 Routen
- **SOCIAL**: 4 Routen
- **PDF**: 5 Routen
- **EDIT**: 1 Routen
- **UPDATE**: 1 Routen
- **TEL**: 4 Routen
- **EVENT**: 5 Routen
- **GEO**: 4 Routen
- **PAYMENT**: 2 Routen
- **MULTILINK**: 5 Routen
- **PRODUCT**: 4 Routen
- **MY**: 1 Routen

## Routen (GET)

| Path | Methoden | Status | Template | Redirect | JSON | Auth | QR-Files |
|---|---|---|---|---|---|---|---|
| /qr/url/ | GET | None | None | False | False | False | 0 |
| /qr/url/create | POST |  |  |  |  |  | 0 |
| /qr/url/edit/{qr_id} | GET | None | None | False | False | False | 0 |
| /qr/url/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /qr/url/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/vcard/ | GET | None | None | False | False | False | 0 |
| /qr/vcard/new | GET | None | None | False | False | False | 0 |
| /qr/vcard/create | POST |  |  |  |  |  | 0 |
| /qr/vcard/edit/{slug} | GET | None | None | False | False | False | 0 |
| /qr/vcard/edit/id/{qr_id} | GET | None | None | False | False | False | 0 |
| /qr/vcard/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /qr/vcard/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/vcard/{slug}.vcf | GET | None | None | False | False | False | 0 |
| /qr/vcard/d/{slug} | GET | None | None | False | False | False | 0 |
| /profile | GET | None | None | False | False | False | 0 |
| /profile/update | POST |  |  |  |  |  | 0 |
| /profile/delete-image | POST |  |  |  |  |  | 0 |
| /auth/register | GET | None | None | False | False | False | 0 |
| /auth/register | POST |  |  |  |  |  | 0 |
| /auth/login | GET | None | None | False | False | False | 0 |
| /auth/login | POST |  |  |  |  |  | 0 |
| /auth/logout | GET | None | None | False | False | False | 0 |
| /auth/change-password | POST |  |  |  |  |  | 0 |
| /auth/forgot-password | GET | None | None | False | False | False | 0 |
| /auth/forgot-password | POST |  |  |  |  |  | 0 |
| /qr/image/ | GET | None | None | False | False | False | 0 |
| /qr/image/create | POST |  |  |  |  |  | 0 |
| /qr/image/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/image/update/{slug} | POST |  |  |  |  |  | 0 |
| /qr/sms/ | GET | None | None | False | False | False | 0 |
| /qr/sms/create | POST |  |  |  |  |  | 0 |
| /qr/sms/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/sms/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /qr/wifi/ | GET | None | None | False | False | False | 0 |
| /qr/wifi/create | POST |  |  |  |  |  | 0 |
| /qr/wifi/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/email/ | GET | None | None | False | False | False | 0 |
| /qr/email/create | POST |  |  |  |  |  | 0 |
| /qr/email/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/email/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /settings/ | GET | None | None | False | False | False | 0 |
| /settings/update-profile | POST |  |  |  |  |  | 0 |
| /settings/billing | GET | None | None | False | False | False | 0 |
| /settings/security | GET | None | None | False | False | False | 0 |
| /settings/security/change-password | POST |  |  |  |  |  | 0 |
| /settings/contact-api | GET | None | None | False | False | False | 0 |
| /qr/social/ | GET | None | None | False | False | False | 0 |
| /qr/social/create | POST |  |  |  |  |  | 0 |
| /qr/social/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/social/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /dashboard/ | GET | None | None | False | False | False | 0 |
| /impressum | GET | None | None | False | False | False | 0 |
| /datenschutz | GET | None | None | False | False | False | 0 |
| /kontakt | GET | None | None | False | False | False | 0 |
| /contact | POST |  |  |  |  |  | 0 |
| /qr/pdf/ | GET | None | None | False | False | False | 0 |
| /qr/pdf/create | POST |  |  |  |  |  | 0 |
| /qr/pdf/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/pdf/{slug}.pdf | GET | None | None | False | False | False | 0 |
| /qr/pdf/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/edit/{slug} | GET | None | None | False | False | False | 0 |
| /qr/update/{slug} | POST |  |  |  |  |  | 0 |
| /qr/image/{slug}/edit-image | GET | None | None | False | False | False | 0 |
| /qr/image/{slug}/update-image | POST |  |  |  |  |  | 0 |
| /billing/ | GET | None | None | False | False | False | 0 |
| /billing/upgrade/{plan_name} | GET | None | None | False | False | False | 0 |
| /billing/cancel | GET | None | None | False | False | False | 0 |
| /billing/webhook | POST |  |  |  |  |  | 0 |
| /billing/test | GET | None | None | False | False | False | 0 |
| /kontakt | GET | None | None | False | False | False | 0 |
| /contact | POST |  |  |  |  |  | 0 |
| /password/forgot | GET | None | None | False | False | False | 0 |
| /password/forgot | POST |  |  |  |  |  | 0 |
| /password/reset | GET | None | None | False | False | False | 0 |
| /password/reset | POST |  |  |  |  |  | 0 |
| /qr/tel/ | GET | None | None | False | False | False | 0 |
| /qr/tel/create | POST |  |  |  |  |  | 0 |
| /qr/tel/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/tel/update/{qr_id} | POST |  |  |  |  |  | 0 |
| /qr/event/ | GET | None | None | False | False | False | 0 |
| /qr/event/create | POST |  |  |  |  |  | 0 |
| /qr/event/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/event/{slug}.ics | GET | None | None | False | False | False | 0 |
| /qr/event/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/geo/ | GET | None | None | False | False | False | 0 |
| /qr/geo/create | POST |  |  |  |  |  | 0 |
| /qr/geo/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/geo/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/payment/ | GET | None | None | False | False | False | 0 |
| /qr/payment/generate | POST |  |  |  |  |  | 0 |
| /qr/multilink/ | GET | None | None | False | False | False | 0 |
| /qr/multilink/create | POST |  |  |  |  |  | 0 |
| /qr/multilink/d/{slug} | GET | None | None | False | False | False | 0 |
| /qr/multilink/edit/{slug} | GET | None | None | False | False | False | 0 |
| /qr/multilink/update/{slug} | POST |  |  |  |  |  | 0 |
| /qr/product/ | GET | None | None | False | False | False | 0 |
| /qr/product/create | POST |  |  |  |  |  | 0 |
| /qr/product/v/{slug} | GET | None | None | False | False | False | 0 |
| /qr/product/img/{slug} | GET | None | None | False | False | False | 0 |
| /dyn/{public_id} | GET | None | None | False | False | False | 0 |
| /billing/checkout/{plan_name} | GET | None | None | False | False | False | 0 |
| /billing/success | GET | None | None | False | False | False | 0 |
| /billing/cancel | GET | None | None | False | False | False | 0 |
| /billing/webhook | POST |  |  |  |  |  | 0 |
| /testmail/ | GET | None | None | False | False | False | 0 |
| /qr/my | GET | None | None | False | False | False | 0 |
| / | GET | None | None | False | False | False | 0 |
| /base-preview | GET | None | None | False | False | False | 0 |
| /example-qr | GET | None | None | False | False | False | 0 |