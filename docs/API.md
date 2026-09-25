# API quick reference

Development OpenAPI: http://127.0.0.1:8000/docs. Nginx exposes all routes below under `/api`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | /auth/login | Email/password/TOTP login, sets HttpOnly cookies |
| POST | /auth/refresh | Rotate refresh token and issue a new access token |
| POST | /auth/logout | Revoke session and clear cookies |
| POST | /auth/forgot-password | Queue reset email when SMTP is configured |
| POST | /auth/reset-password | Consume reset token and revoke old sessions |
| GET | /users/me | Current identity |
| GET | /users | Scoped workspace directory |
| GET / POST | /requests | List authorized requests / submit request |
| GET | /requests/{id} | Authorized request detail |
| POST | /requests/{id}/approve | Approve current assigned step |
| POST | /requests/{id}/reject | Reject with reason |
| POST | /requests/{id}/request-info | Pause and ask requester for information |
| POST | /requests/{id}/resubmit | Requester supplies information |
| POST | /requests/{id}/cancel | Requester cancels active request |
| POST | /requests/{id}/comments/add | Add an authorized comment |
| POST | /requests/{id}/attachments/upload | Upload private multipart file |
| GET | /attachments/{id} | Authorized attachment download |
| GET | /workflows | Read routing rules |
| POST / PUT | /admin/workflows / /admin/workflows/{id} | Configure workflow |
| POST / PUT | /admin/users / /admin/users/{id} | Create or change account |
| GET | /activity | Scoped activity; admins see workspace audit events |
| GET / POST | /notifications / /notifications/read | Read notifications / mark read |
| GET | /analytics/dashboard | Scoped request counts and pending amount |
| WebSocket | /ws/notifications | Authenticated notification updates |

Decision payload: `{"version":1,"comment":"Business need verified."}`. Reject, request-info, and resubmit require a comment. A stale version returns 409; unauthorized access returns 403. Cookies require the configured same-origin frontend; cross-origin credentialed requests are deliberately constrained.

The application does not hard-delete submitted requests or silently edit approved amounts. Use cancellation and a new request to preserve the audit trail.
