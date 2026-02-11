# Ouhud QR – Capability Report

Automatisch erzeugt (Routen, Templates, DB, QR, E-Mail, Auth).

| Route | Method | Handler | Status | Redirect | Auth? | Templates | DB Read | DB Write | QR Files | Emails |
|---|---|---:|---:|---|---:|---|---|---|---|---|
| / | GET | - | 200 | - | no | index.html | plans | - | - | - |
| /auth/forgot-password | GET | - | 200 | - | no | forgot-password.html | - | - | - | - |
| /auth/login | GET | - | 200 | - | no | login.html | - | - | - | - |
| /auth/logout | GET | - | 303 | / | no | - | - | - | - | - |
| /auth/register | GET | - | 200 | - | no | register.html | - | - | - | - |
| /base-preview | GET | - | 200 | - | no | base.html | plans | - | - | - |
| /billing/ | GET | - | 303 | / | no | - | - | - | - | - |
| /billing/cancel | GET | - | 303 | / | no | - | - | - | - | - |
| /billing/cancel | GET | - | 303 | / | no | - | - | - | - | - |
| /billing/success | GET | - | 200 | - | no | - | - | - | - | - |
| /billing/test | GET | - | 200 | - | no | - | - | - | - | - |
| /dashboard/ | GET | - | 303 | / | no | - | - | - | - | - |
| /datenschutz | GET | - | 200 | - | no | privacy.html | - | - | - | - |
| /example-qr | GET | - | 200 | - | no | - | - | - | - | - |
| /impressum | GET | - | 200 | - | no | impressum.html | - | - | - | - |
| /kontakt | GET | - | 200 | - | no | kontakt.html | - | - | - | - |
| /kontakt | GET | - | 200 | - | no | kontakt.html | - | - | - | - |
| /password/forgot | GET | - | 200 | - | no | forgot-password.html | - | - | - | - |
| /password/reset | GET | - | 422 | - | no | - | - | - | - | - |
| /profile | GET | - | 303 | /auth/login | yes | - | - | - | - | - |
| /qr/email/ | GET | - | 200 | - | no | qr_email_form.html | - | - | - | - |
| /qr/event/ | GET | - | 200 | - | no | qr_event.html | - | - | - | - |
| /qr/geo/qr/geo/ | GET | - | 200 | - | no | qr_geo.html | - | - | - | - |
| /qr/image/ | GET | - | 200 | - | no | qr_image_form.html | - | - | - | - |
| /qr/multilink/qr/multi/ | GET | - | 200 | - | no | qr_multilink_form.html | - | - | - | - |
| /qr/payment/qr/payment/ | GET | - | 200 | - | no | qr_payment.html | - | - | - | - |
| /qr/pdf/ | GET | - | 200 | - | no | qr_pdf_form.html | - | - | - | - |
| /qr/product/qr/product/ | GET | - | 200 | - | no | qr_product.html | - | - | - | - |
| /qr/sms/ | GET | - | 200 | - | no | qr_sms_form.html | - | - | - | - |
| /qr/social/ | GET | - | 200 | - | no | qr_social_form.html | - | - | - | - |
| /qr/tel/ | GET | - | 200 | - | no | qr_tel.html | - | - | - | - |
| /qr/url/qr/url/ | GET | - | 200 | - | no | qr_url.html | - | - | - | - |
| /qr/vcard/ | GET | - | 200 | - | no | vcard.html | - | - | - | - |
| /qr/vcard/new | GET | - | 200 | - | no | vcard.html | - | - | - | - |
| /qr/wifi/ | GET | - | 200 | - | no | qr_wifi_form.html | - | - | - | - |
| /settings/ | GET | - | 303 | / | no | - | - | - | - | - |
| /settings/billing | GET | - | 303 | / | no | - | - | - | - | - |
| /settings/contact-api | GET | - | 303 | /contact?topic=api-access | no | - | - | - | - | - |
| /settings/security | GET | - | 303 | / | no | - | - | - | - | - |
| /testmail/ | GET | - | 200 | - | no | - | - | - | - | - |