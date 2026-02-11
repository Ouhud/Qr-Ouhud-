# Security Test Matrix: Account Isolation and Access Control

## Scope
This matrix validates that one account cannot manage QR resources of another account without explicit sharing.

## Test Roles
- `guest`: not logged in
- `owner_a`: account that created the QR
- `user_b`: different account, no share
- `viewer_b`: user_b shared with role `viewer`
- `editor_b`: user_b shared with role `editor`
- `admin_b`: user_b shared with role `admin`

## Test Data Setup
1. Login as `owner_a`.
2. Create 1 QR per major type:
`url`, `vcard`, `pdf`, `wifi`, `sms`, `email`, `tel`, `social`, `event`, `geo`, `payment`, `multilink`, `product`, `wallet`, `gs1`, `app_deeplink`, `review`, `booking`, `lead`, `feedback`, `coupon`.
3. Save one reference item:
- `slug_a`: slug of one QR from owner_a
- `id_a`: id of the same QR (if route uses id)
4. Create second account `user_b`.
5. In team sharing, share `slug_a` to `user_b` first as `viewer`, then `editor`, then `admin` for role-based checks.

## Expected Behavior Rules
- Management routes require login.
- Owner can edit/update own QR.
- Unshared foreign user cannot edit/update foreign QR.
- `viewer` can view shared resources, but cannot edit.
- `editor` and `admin` can edit shared QR.
- Public scan route `/d/{slug}` remains public by design.

## Matrix
| ID | Route | Action | guest | owner_a | user_b (unshared) | viewer_b | editor_b | admin_b |
|---|---|---|---|---|---|---|---|---|
| M01 | `/qr/edit/{slug_a}` | open edit page | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M02 | `/qr/update/{slug_a}` | submit update | `401` | `303/200` | `403/404` | `403` | `303/200` | `303/200` |
| M03 | `/qr/image/{slug_a}/edit-image` | open image editor | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M04 | `/qr/image/{slug_a}/update-image` | submit image update | `401` | `303/200` | `403/404` | `403` | `303/200` | `303/200` |
| M05 | `/qr/url/edit/{id_a}` | open URL edit | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M06 | `/qr/url/update/{id_a}` | submit URL update | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M07 | `/qr/vcard/edit/{slug_a}` | open vCard edit | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M08 | `/qr/vcard/update/{id_a}` | submit vCard update | `401` | `303` | `403/404` | `403` | `303` | `303` |
| M09 | `/qr/pdf/edit/{slug_a}` | open PDF edit | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M10 | `/qr/pdf/update/{id_a}` | submit PDF update | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M11 | `/qr/update/{id_a}` via `qr_base` | generic update | `401` | `200` | `403/404` | `403` | `200` | `200` |
| M12 | `/team/workspaces` | open team page | `401` | `200` | `200` | `200` | `200` | `200` |
| M13 | `/team/share` | share QR | `401` | `303/200` | `303/403` | `303/403` | `303/403` | `303/403` |
| M14 | `/team/workspaces/{id}/qrs/assign` | assign QR | `401` | `303/200` | `403` | `403` | `403` | `403` |
| M15 | `/profile` | list own/shared qrs | `303->login` | `200` | `200` | `200` | `200` | `200` |
| M16 | `/settings/security` | security page | `401` | `200` | `200` | `200` | `200` | `200` |
| P01 | `/d/{slug_a}` | public resolve | `200/302` | `200/302` | `200/302` | `200/302` | `200/302` | `200/302` |

## Data Isolation Assertions
1. `user_b` must never see owner_a QR in management pages unless shared.
2. Any update from `user_b` to owner_a QR without share must fail.
3. Creating QR while not logged in must fail with `401`.
4. Dashboard scan list should not show local test traffic by default.

## Quick Verification Commands
Use browser session for role-based tests. Use CLI only for public routes.

```bash
# Syntax + policy sanity checks
./scripts/security_check.sh

# Public resolver should stay reachable (replace slug)
curl -i "http://127.0.0.1:8000/d/REPLACE_SLUG"
```

## Result Template
Copy this block to track release sign-off.

```text
Release:
Date:
Tester:

M01:
M02:
M03:
M04:
M05:
M06:
M07:
M08:
M09:
M10:
M11:
M12:
M13:
M14:
M15:
M16:
P01:

Final verdict: PASS / FAIL
Blocking issues:
```
